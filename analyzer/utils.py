import zipfile
import os
import tempfile
from PIL import Image
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone
from .models import AiaFile, ImageAsset, UsabilityEvaluation
import shutil


def analyze_aia_file(aia_file):
    """
    Extract and analyze images from an .aia file
    .aia files are ZIP archives containing App Inventor project files
    """
    
    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract .aia file (it's a ZIP)
        with zipfile.ZipFile(aia_file.file.path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find and process images
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
        image_count = 0
        icon_count = 0
        
        # Clear existing images for this file
        aia_file.images.all().delete()
        
        # Walk through extracted files
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                if file_ext in image_extensions:
                    try:
                        # Process the image
                        image_asset = process_image_file(
                            file_path, 
                            file, 
                            aia_file, 
                            os.path.relpath(file_path, temp_dir)
                        )
                        
                        if image_asset:
                            image_count += 1
                            if is_icon(file, image_asset):
                                icon_count += 1
                                image_asset.asset_type = 'icon'
                                image_asset.save()
                    
                    except Exception as e:
                        print(f"Error processing image {file}: {str(e)}")
                        continue
        
        # Update file analysis status
        aia_file.total_images = image_count
        aia_file.total_icons = icon_count
        aia_file.is_analyzed = True
        aia_file.analysis_completed_at = timezone.now()
        aia_file.save()
        
        # Generate usability evaluation
        generate_usability_evaluation(aia_file)


def process_image_file(file_path, filename, aia_file, relative_path):
    """Process a single image file and create ImageAsset record"""
    
    try:
        with Image.open(file_path) as img:
            # Get image properties
            width, height = img.size
            format_name = img.format or 'UNKNOWN'
            file_size = os.path.getsize(file_path)
            
            # Create ImageAsset record
            image_asset = ImageAsset(
                aia_file=aia_file,
                name=filename,
                original_path=relative_path,
                width=width,
                height=height,
                file_size=file_size,
                format=format_name
            )
            
            # Copy image to media directory
            with open(file_path, 'rb') as f:
                image_content = ContentFile(f.read())
                image_asset.extracted_file.save(
                    f"{aia_file.id}_{filename}",
                    image_content,
                    save=False
                )
            
            # Analyze image quality
            analyze_image_quality(image_asset, img)
            
            # Determine asset type
            image_asset.asset_type = determine_asset_type(filename, width, height)
            
            image_asset.save()
            return image_asset
            
    except Exception as e:
        print(f"Error processing image {filename}: {str(e)}")
        return None


def analyze_image_quality(image_asset, pil_image):
    """Analyze image quality and set quality metrics"""
    
    width = image_asset.width
    height = image_asset.height
    file_size = image_asset.file_size
    
    # Calculate quality score based on multiple factors
    quality_score = 50  # Base score
    
    # Resolution factor
    total_pixels = width * height
    if total_pixels >= 1920 * 1080:  # Full HD or higher
        quality_score += 30
    elif total_pixels >= 1280 * 720:  # HD
        quality_score += 20
    elif total_pixels >= 640 * 480:  # VGA
        quality_score += 10
    else:
        quality_score -= 20  # Very low resolution
    
    # File size optimization factor
    bytes_per_pixel = file_size / total_pixels if total_pixels > 0 else 0
    if 1 <= bytes_per_pixel <= 4:  # Well optimized
        quality_score += 10
    elif bytes_per_pixel > 8:  # Too large
        quality_score -= 15
    elif bytes_per_pixel < 0.5:  # Overly compressed
        quality_score -= 10
    
    # Aspect ratio check (mobile-friendly ratios)
    aspect_ratio = width / height if height > 0 else 0
    mobile_friendly_ratios = [16/9, 4/3, 3/2, 1/1, 9/16]  # Common mobile ratios
    ratio_match = any(abs(aspect_ratio - ratio) < 0.1 for ratio in mobile_friendly_ratios)
    
    # Ensure score is within bounds
    quality_score = max(0, min(100, quality_score))
    
    # Set quality rating
    if quality_score >= 80:
        quality_rating = 'excellent'
    elif quality_score >= 65:
        quality_rating = 'high'
    elif quality_score >= 40:
        quality_rating = 'medium'
    else:
        quality_rating = 'low'
    
    # Set usability flags
    image_asset.quality_score = quality_score
    image_asset.quality_rating = quality_rating
    image_asset.resolution_adequate = total_pixels >= 640 * 480
    image_asset.aspect_ratio_appropriate = ratio_match
    image_asset.file_size_optimized = 1 <= bytes_per_pixel <= 6


def determine_asset_type(filename, width, height):
    """Determine the type of asset based on filename and dimensions"""
    
    filename_lower = filename.lower()
    
    # Check for common icon patterns
    if any(keyword in filename_lower for keyword in ['icon', 'ico', 'button', 'btn']):
        return 'icon'
    
    # Check for background patterns
    if any(keyword in filename_lower for keyword in ['background', 'bg', 'wallpaper']):
        return 'background'
    
    # Check dimensions for icons (typically small and square-ish)
    if width <= 128 and height <= 128 and abs(width - height) <= 32:
        return 'icon'
    
    # Check for button-like dimensions
    if (width > height and width <= 300 and height <= 100) or \
       (height > width and height <= 300 and width <= 100):
        return 'button'
    
    # Large images are likely backgrounds
    if width >= 800 or height >= 600:
        return 'background'
    
    return 'image'


def is_icon(filename, image_asset):
    """Determine if an image is likely an icon"""
    return image_asset.asset_type == 'icon' or \
           (image_asset.width <= 128 and image_asset.height <= 128)


def generate_usability_evaluation(aia_file):
    """Generate comprehensive usability evaluation for the app"""
    
    images = aia_file.images.all()
    
    if not images.exists():
        return
    
    # Calculate metrics
    total_images = images.count()
    high_quality_count = images.filter(quality_rating__in=['high', 'excellent']).count()
    low_quality_count = images.filter(quality_rating='low').count()
    oversized_count = images.filter(file_size__gt=1024*1024).count()  # > 1MB
    undersized_count = images.filter(width__lt=100, height__lt=100).count()
    
    # Calculate scores
    image_quality_score = (high_quality_count / total_images) * 100 if total_images > 0 else 0
    icon_quality_score = calculate_icon_quality_score(aia_file)
    overall_score = (image_quality_score + icon_quality_score) / 2
    
    # Generate recommendations
    recommendations = generate_recommendations(aia_file, images)
    
    # Create or update evaluation
    evaluation, created = UsabilityEvaluation.objects.get_or_create(
        aia_file=aia_file,
        defaults={
            'image_quality_score': image_quality_score,
            'icon_quality_score': icon_quality_score,
            'overall_usability_score': overall_score,
            'high_quality_images_count': high_quality_count,
            'low_quality_images_count': low_quality_count,
            'oversized_images_count': oversized_count,
            'undersized_images_count': undersized_count,
            'recommendations': recommendations,
        }
    )
    
    if not created:
        # Update existing evaluation
        evaluation.image_quality_score = image_quality_score
        evaluation.icon_quality_score = icon_quality_score
        evaluation.overall_usability_score = overall_score
        evaluation.high_quality_images_count = high_quality_count
        evaluation.low_quality_images_count = low_quality_count
        evaluation.oversized_images_count = oversized_count
        evaluation.undersized_images_count = undersized_count
        evaluation.recommendations = recommendations
        evaluation.save()


def calculate_icon_quality_score(aia_file):
    """Calculate quality score specifically for icons"""
    
    icons = aia_file.images.filter(asset_type='icon')
    
    if not icons.exists():
        return 100  # No icons, no problems
    
    high_quality_icons = icons.filter(quality_rating__in=['high', 'excellent']).count()
    total_icons = icons.count()
    
    return (high_quality_icons / total_icons) * 100


def generate_recommendations(aia_file, images):
    """Generate specific recommendations for improving usability"""
    
    recommendations = []
    
    # Check for low quality images
    low_quality_images = images.filter(quality_rating='low')
    if low_quality_images.exists():
        recommendations.append(
            f"• {low_quality_images.count()} imagem(ns) com baixa qualidade detectada(s). "
            "Considere usar imagens com maior resolução."
        )
    
    # Check for oversized images
    oversized_images = images.filter(file_size__gt=1024*1024)  # > 1MB
    if oversized_images.exists():
        recommendations.append(
            f"• {oversized_images.count()} imagem(ns) muito grande(s) detectada(s). "
            "Otimize o tamanho dos arquivos para melhorar a performance."
        )
    
    # Check for inadequate resolutions
    low_res_images = images.filter(resolution_adequate=False)
    if low_res_images.exists():
        recommendations.append(
            f"• {low_res_images.count()} imagem(ns) com resolução inadequada. "
            "Use imagens com pelo menos 640x480 pixels."
        )
    
    # Check for poor aspect ratios
    bad_ratio_images = images.filter(aspect_ratio_appropriate=False)
    if bad_ratio_images.exists():
        recommendations.append(
            f"• {bad_ratio_images.count()} imagem(ns) com proporções inadequadas para dispositivos móveis. "
            "Considere usar proporções como 16:9, 4:3 ou 1:1."
        )
    
    # Check icon consistency
    icons = images.filter(asset_type='icon')
    if icons.exists():
        icon_sizes = set((icon.width, icon.height) for icon in icons)
        if len(icon_sizes) > 3:
            recommendations.append(
                "• Ícones com tamanhos inconsistentes detectados. "
                "Use tamanhos padronizados (ex: 32x32, 64x64, 128x128)."
            )
    
    if not recommendations:
        recommendations.append("• Parabéns! Nenhum problema significativo detectado nas imagens.")
    
    return '\n'.join(recommendations)
