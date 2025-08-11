import zipfile
import os
import tempfile
from PIL import Image
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone
from .models import AiaFile, ImageAsset, UsabilityEvaluation
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
import hashlib
import json

# Dicionário global para armazenar os ícones do Material Design
MATERIAL_ICONS_DB = {}

# Configurações dos ícones Material Design
MATERIAL_ICON_STYLES = {
    'materialicons': 'filled',
    'materialiconsoutlined': 'outlined', 
    'materialiconsround': 'round',
    'materialiconssharp': 'sharp',
    'materialiconstwotone': 'twotone'
}


def load_material_icons():
    """
    Carrega todos os ícones do Material Design da estrutura source/src/
    
    Estrutura esperada:
    source/src/categoria/nome_do_icone/estilo/arquivo.svg
    
    Exemplo:
    source/src/action/home/materialicons/24px.svg
    source/src/action/home/materialiconsoutlined/24px.svg
    """
    global MATERIAL_ICONS_DB
    
    # Caminho para os ícones (relativo ao diretório do projeto)
    base_path = Path(__file__).parent.parent / 'source' / 'src'
    
    if not base_path.exists():
        print(f"⚠️  Diretório de ícones não encontrado: {base_path}")
        return
    
    icon_count = 0
    category_count = 0
    
    try:
        # Percorre todas as categorias
        for category_path in base_path.iterdir():
            if not category_path.is_dir():
                continue
                
            category_name = category_path.name
            category_count += 1
            
            # Percorre todos os ícones na categoria
            for icon_path in category_path.iterdir():
                if not icon_path.is_dir():
                    continue
                    
                icon_name = icon_path.name
                
                # Inicializa entrada para o ícone se não existir
                if category_name not in MATERIAL_ICONS_DB:
                    MATERIAL_ICONS_DB[category_name] = {}
                    
                if icon_name not in MATERIAL_ICONS_DB[category_name]:
                    MATERIAL_ICONS_DB[category_name][icon_name] = {}
                
                # Percorre todos os estilos do ícone
                for style_path in icon_path.iterdir():
                    if not style_path.is_dir():
                        continue
                        
                    style_dir_name = style_path.name
                    style_name = MATERIAL_ICON_STYLES.get(style_dir_name, style_dir_name)
                    
                    # Procura arquivo SVG no diretório do estilo
                    svg_files = list(style_path.glob('*.svg'))
                    
                    if svg_files:
                        svg_file = svg_files[0]  # Pega o primeiro arquivo SVG encontrado
                        
                        try:
                            # Lê e processa o arquivo SVG
                            svg_content = svg_file.read_text(encoding='utf-8')
                            
                            # Extrai informações básicas do SVG
                            svg_info = parse_svg_info(svg_content)
                            
                            # Armazena as informações do ícone
                            MATERIAL_ICONS_DB[category_name][icon_name][style_name] = {
                                'path': str(svg_file),
                                'content': svg_content,
                                'viewBox': svg_info.get('viewBox', '0 0 24 24'),
                                'width': svg_info.get('width', '24'),
                                'height': svg_info.get('height', '24'),
                                'hash': hashlib.md5(svg_content.encode()).hexdigest()
                            }
                            
                            icon_count += 1
                            
                        except Exception as e:
                            print(f"⚠️  Erro ao processar {svg_file}: {e}")
                            continue
        
        print(f"✅ Material Icons carregados: {icon_count} ícones em {category_count} categorias")
        
        # Salva cache dos ícones carregados
        save_icons_cache()
        
    except Exception as e:
        print(f"❌ Erro ao carregar Material Icons: {e}")


def parse_svg_info(svg_content):
    """
    Extrai informações básicas de um arquivo SVG
    """
    try:
        root = ET.fromstring(svg_content)
        
        # Remove namespace se presente
        if root.tag.startswith('{'):
            root.tag = root.tag.split('}')[1]
        
        info = {}
        
        # Extrai atributos principais
        info['viewBox'] = root.get('viewBox', '0 0 24 24')
        info['width'] = root.get('width', '24')
        info['height'] = root.get('height', '24')
        
        return info
        
    except ET.ParseError as e:
        print(f"⚠️  Erro ao fazer parse do SVG: {e}")
        return {'viewBox': '0 0 24 24', 'width': '24', 'height': '24'}


def save_icons_cache():
    """
    Salva cache dos ícones carregados para acelerar próximas execuções
    """
    try:
        cache_path = Path(__file__).parent.parent / 'material_icons_cache.json'
        
        # Prepara dados para serialização (remove conteúdo SVG para reduzir tamanho)
        cache_data = {}
        for category, icons in MATERIAL_ICONS_DB.items():
            cache_data[category] = {}
            for icon_name, styles in icons.items():
                cache_data[category][icon_name] = {}
                for style_name, info in styles.items():
                    cache_data[category][icon_name][style_name] = {
                        'path': info['path'],
                        'viewBox': info['viewBox'],
                        'width': info['width'],
                        'height': info['height'],
                        'hash': info['hash']
                    }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
        print(f"💾 Cache salvo em: {cache_path}")
        
    except Exception as e:
        print(f"⚠️  Erro ao salvar cache: {e}")


def load_icons_cache():
    """
    Carrega cache dos ícones se disponível
    """
    try:
        cache_path = Path(__file__).parent.parent / 'material_icons_cache.json'
        
        if not cache_path.exists():
            return False
            
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        global MATERIAL_ICONS_DB
        MATERIAL_ICONS_DB = cache_data
        
        # Conta ícones carregados
        icon_count = sum(len(styles) for icons in MATERIAL_ICONS_DB.values() for styles in icons.values())
        print(f"💾 Cache carregado: {icon_count} ícones")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Erro ao carregar cache: {e}")
        return False


def find_similar_material_icon(image_asset, similarity_threshold=0.8):
    """
    Encontra ícones do Material Design similares a um ícone do app
    """
    if not MATERIAL_ICONS_DB:
        if not load_icons_cache():
            load_material_icons()
    
    if not MATERIAL_ICONS_DB:
        return None
    
    # Para demonstração, vamos usar características básicas
    # Em uma implementação real, você usaria comparação visual mais sofisticada
    
    results = []
    icon_name_lower = image_asset.name.lower()
    
    # Busca por nome similar
    for category, icons in MATERIAL_ICONS_DB.items():
        for icon_name, styles in icons.items():
            # Verifica se o nome é similar
            if icon_name.lower() in icon_name_lower or icon_name_lower in icon_name.lower():
                for style_name, info in styles.items():
                    results.append({
                        'category': category,
                        'name': icon_name,
                        'style': style_name,
                        'similarity': 0.9,  # Placeholder - implementar algoritmo real
                        'path': info['path'],
                        'hash': info['hash']
                    })
    
    # Filtra por threshold e ordena por similaridade
    results = [r for r in results if r['similarity'] >= similarity_threshold]
    results.sort(key=lambda x: x['similarity'], reverse=True)
    
    return results[:5]  # Retorna top 5 matches


def analyze_icon_against_material_design(image_asset):
    """
    Analisa um ícone do app contra os padrões do Material Design
    """
    if image_asset.asset_type != 'icon':
        return None
    
    # Carrega ícones se necessário
    if not MATERIAL_ICONS_DB:
        if not load_icons_cache():
            load_material_icons()
    
    analysis = {
        'follows_material_guidelines': False,
        'recommended_size': '24dp (72px)',
        'size_score': 0,
        'material_matches': [],
        'recommendations': []
    }
    
    # Verifica tamanho recomendado (múltiplos de 24px para Material Design)
    width, height = image_asset.width, image_asset.height
    
    # Material Design recomenda múltiplos de 24px (24, 48, 72, 96, etc.)
    material_sizes = [24, 48, 72, 96, 144, 192]
    closest_size = min(material_sizes, key=lambda x: abs(x - max(width, height)))
    
    if abs(max(width, height) - closest_size) <= 4:  # Tolerância de 4px
        analysis['size_score'] = 100
        analysis['follows_material_guidelines'] = True
    elif width == height:  # Pelo menos é quadrado
        analysis['size_score'] = 70
    else:
        analysis['size_score'] = 30
        analysis['recommendations'].append(
            f"Ícone deveria ser quadrado e usar tamanhos padrão do Material Design (24, 48, 72px, etc.)"
        )
    
    # Procura por ícones similares
    similar_icons = find_similar_material_icon(image_asset)
    if similar_icons:
        analysis['material_matches'] = similar_icons
        analysis['recommendations'].append(
            f"Encontrados {len(similar_icons)} ícones similares no Material Design. "
            "Considere usar um ícone padrão para melhor consistência."
        )
    else:
        analysis['recommendations'].append(
            "Nenhum ícone similar encontrado no Material Design. "
            "Certifique-se de que o ícone segue as diretrizes visuais do Material Design."
        )
    
    return analysis


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


def calculate_asset_quality_score(asset):
    """
    Calcula uma pontuação de qualidade de 0 a 100 para um único asset (imagem ou ícone).
    Sistema de pontuação granular baseado em múltiplos critérios ponderados.
    """
    score = 0
    max_score = 100
    
    # Critério 1: Resolução (Peso 40)
    min_resolution = 128  # Mínimo para ícones
    ideal_resolution = 512  # Ideal para imagens
    total_pixels = asset.width * asset.height
    
    if asset.width >= ideal_resolution and asset.height >= ideal_resolution:
        score += 40  # Resolução excelente
    elif asset.width >= min_resolution and asset.height >= min_resolution:
        # Pontuação proporcional entre mínimo e ideal
        pixel_ratio = min(total_pixels / (ideal_resolution * ideal_resolution), 1.0)
        score += 20 + (20 * pixel_ratio)  # 20-40 pontos baseado na proporção
    else:
        # Penalização proporcional para resoluções muito baixas
        pixel_ratio = total_pixels / (min_resolution * min_resolution)
        score += max(0, 20 * pixel_ratio)  # 0-20 pontos baseado na proporção
        
    # Critério 2: Otimização do Arquivo (Bytes por Pixel) (Peso 30)
    bpp = asset.bytes_per_pixel if asset.bytes_per_pixel is not None else 0
    if 1 <= bpp <= 4:  # Bem otimizado
        score += 30
    elif 0.5 <= bpp < 1:  # Levemente comprimido mas aceitável
        score += 25
    elif 4 < bpp <= 8:  # Um pouco grande mas ainda aceitável
        score += 20
    elif bpp > 8:  # Muito grande
        score += 10
    elif bpp > 0.1:  # Comprimido mas ainda utilizável
        score += 15
    else:  # Muito comprimido ou corrupto
        score += 5

    # Critério 3: Proporção (Peso 20)
    if asset.width > 0 and asset.height > 0:
        ratio = max(asset.width, asset.height) / min(asset.width, asset.height)
        
        if 1 <= ratio <= 2:  # Proporções ideais (1:1, 4:3, 16:9)
            score += 20
        elif ratio <= 3:  # Proporções aceitáveis
            score += 15
        elif ratio <= 5:  # Proporções pobres mas utilizáveis
            score += 10
        else:  # Proporções muito ruins
            score += 5
    else:
        score += 5  # Erro nos dados de dimensão

    # Critério 4: Conformidade com Material Design (apenas para ícones) (Peso 10)
    if asset.asset_type == 'icon':
        # Verifica se segue diretrizes do Material Design
        material_analysis = analyze_icon_against_material_design(asset)
        if material_analysis:
            # Converte o size_score (0-100) para escala de 10 pontos
            material_score = (material_analysis['size_score'] / 100) * 10
            score += material_score
        else:
            # Se não conseguiu analisar, dá pontuação parcial
            score += 5
    else:
        # Se não for um ícone, este critério não se aplica, então damos os pontos
        score += 10

    return min(round(score), max_score)  # Garante que a nota não passe de 100


def calculate_overall_scores(assets):
    """
    Calcula os scores de qualidade para imagens, ícones e o geral, usando a nova lógica granular.
    """
    if not assets:
        # Se não há assets, retorna 100 (projeto limpo)
        return {
            "overall_score": 100,
            "image_quality_score": 100,
            "icon_quality_score": 100,
        }
    
    # Separa assets por tipo
    image_assets = [asset for asset in assets if asset.asset_type in ['image', 'background', 'button', 'other']]
    icon_assets = [asset for asset in assets if asset.asset_type == 'icon']

    # Calcula scores individuais para cada asset
    all_scores = [calculate_asset_quality_score(asset) for asset in assets]
    image_scores = [calculate_asset_quality_score(asset) for asset in image_assets] if image_assets else []
    icon_scores = [calculate_asset_quality_score(asset) for asset in icon_assets] if icon_assets else []

    # Score geral: média de todos os assets
    overall_score = sum(all_scores) / len(all_scores)

    # Scores por categoria: média de cada categoria, ou 100 se não houver assets na categoria
    image_quality_score = sum(image_scores) / len(image_scores) if image_scores else 100
    icon_quality_score = sum(icon_scores) / len(icon_scores) if icon_scores else 100

    return {
        "overall_score": round(overall_score, 1),
        "image_quality_score": round(image_quality_score, 1),
        "icon_quality_score": round(icon_quality_score, 1),
    }


def analyze_image_quality(image_asset, pil_image):
    """Analyze image quality and set quality metrics using the new granular scoring system"""
    
    # Calcula o score granular usando a nova função
    quality_score = calculate_asset_quality_score(image_asset)
    
    # Determina a classificação qualitativa baseada no score numérico
    if quality_score >= 85:
        quality_rating = 'excellent'
    elif quality_score >= 70:
        quality_rating = 'high'
    elif quality_score >= 50:
        quality_rating = 'medium'
    else:
        quality_rating = 'low'
    
    # Calcula métricas auxiliares
    width = image_asset.width
    height = image_asset.height
    file_size = image_asset.file_size
    total_pixels = width * height
    bytes_per_pixel = file_size / total_pixels if total_pixels > 0 else 0
    
    # Aspect ratio check (mobile-friendly ratios)
    aspect_ratio = width / height if height > 0 else 0
    mobile_friendly_ratios = [16/9, 4/3, 3/2, 1/1, 9/16]  # Common mobile ratios
    ratio_match = any(abs(aspect_ratio - ratio) < 0.1 for ratio in mobile_friendly_ratios)
    
    # Set all calculated values
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
    """Generate comprehensive usability evaluation for the app using new granular scoring"""
    
    images = aia_file.images.all()
    
    if not images.exists():
        # Se não há imagens, cria avaliação com scores máximos
        evaluation, created = UsabilityEvaluation.objects.get_or_create(
            aia_file=aia_file,
            defaults={
                'image_quality_score': 100,
                'icon_quality_score': 100,
                'overall_usability_score': 100,
                'high_quality_images_count': 0,
                'low_quality_images_count': 0,
                'oversized_images_count': 0,
                'undersized_images_count': 0,
                'recommendations': '• ✨ Projeto sem assets visuais - nenhum problema detectado.',
            }
        )
        return
    
    # Calcula scores usando a nova lógica granular
    scores = calculate_overall_scores(list(images))
    
    # Calculate detailed metrics
    total_images = images.count()
    high_quality_count = images.filter(quality_rating__in=['high', 'excellent']).count()
    low_quality_count = images.filter(quality_rating='low').count()
    oversized_count = images.filter(file_size__gt=1024*1024).count()  # > 1MB
    undersized_count = images.filter(width__lt=100, height__lt=100).count()
    
    # Generate recommendations
    recommendations = generate_recommendations(aia_file, images)
    
    # Create or update evaluation
    evaluation, created = UsabilityEvaluation.objects.get_or_create(
        aia_file=aia_file,
        defaults={
            'image_quality_score': scores['image_quality_score'],
            'icon_quality_score': scores['icon_quality_score'],
            'overall_usability_score': scores['overall_score'],
            'high_quality_images_count': high_quality_count,
            'low_quality_images_count': low_quality_count,
            'oversized_images_count': oversized_count,
            'undersized_images_count': undersized_count,
            'recommendations': recommendations,
        }
    )
    
    if not created:
        # Update existing evaluation
        evaluation.image_quality_score = scores['image_quality_score']
        evaluation.icon_quality_score = scores['icon_quality_score']
        evaluation.overall_usability_score = scores['overall_score']
        evaluation.high_quality_images_count = high_quality_count
        evaluation.low_quality_images_count = low_quality_count
        evaluation.oversized_images_count = oversized_count
        evaluation.undersized_images_count = undersized_count
        evaluation.recommendations = recommendations
        evaluation.save()


def generate_recommendations(aia_file, images):
    """Generate specific recommendations for improving usability with granular scoring context"""
    
    recommendations = []
    
    # Calcula scores gerais para contexto
    scores = calculate_overall_scores(list(images))
    
    # Estatísticas detalhadas por score
    excellent_images = images.filter(quality_score__gte=85)
    good_images = images.filter(quality_score__gte=70, quality_score__lt=85)
    medium_images = images.filter(quality_score__gte=50, quality_score__lt=70)
    poor_images = images.filter(quality_score__lt=50)
    
    # Recomendações baseadas na distribuição de qualidade
    if poor_images.exists():
        recommendations.append(
            f"🔴 **{poor_images.count()} asset(s) com qualidade muito baixa** (score < 50). "
            f"Estes assets precisam de atenção imediata para melhorar resolução, otimização ou proporções."
        )
    
    if medium_images.exists():
        recommendations.append(
            f"🟡 **{medium_images.count()} asset(s) com qualidade média** (score 50-69). "
            f"Pequenos ajustes podem elevar significativamente a qualidade destes assets."
        )
    
    if good_images.exists() and excellent_images.count() == 0:
        recommendations.append(
            f"🟢 **{good_images.count()} asset(s) com boa qualidade** (score 70-84). "
            f"Considere otimizações finais para alcançar excelência (score ≥ 85)."
        )
    
    # Check for oversized images
    oversized_images = images.filter(file_size__gt=1024*1024)  # > 1MB
    if oversized_images.exists():
        avg_size = sum(img.file_size for img in oversized_images) / len(oversized_images) / (1024*1024)
        recommendations.append(
            f"📦 **{oversized_images.count()} imagem(ns) muito pesada(s)** (>{avg_size:.1f}MB em média). "
            f"Comprima estas imagens para melhorar performance do app."
        )
    
    # Check for inadequate resolutions
    low_res_images = images.filter(resolution_adequate=False)
    if low_res_images.exists():
        recommendations.append(
            f"📐 **{low_res_images.count()} imagem(ns) com resolução inadequada**. "
            f"Use pelo menos 640×480px para garantir qualidade visual em diferentes dispositivos."
        )
    
    # Check for poor aspect ratios
    bad_ratio_images = images.filter(aspect_ratio_appropriate=False)
    if bad_ratio_images.exists():
        recommendations.append(
            f"📱 **{bad_ratio_images.count()} imagem(ns) com proporções inadequadas** para dispositivos móveis. "
            f"Prefira proporções como 16:9, 4:3, 3:2 ou 1:1."
        )
    
    # Icon-specific recommendations with Material Design focus
    icons = images.filter(asset_type='icon')
    if icons.exists():
        icon_scores = [calculate_asset_quality_score(icon) for icon in icons]
        avg_icon_score = sum(icon_scores) / len(icon_scores)
        
        # Check icon size consistency
        icon_sizes = set((icon.width, icon.height) for icon in icons)
        if len(icon_sizes) > 3:
            recommendations.append(
                f"🎨 **Ícones com tamanhos inconsistentes** detectados ({len(icon_sizes)} tamanhos diferentes). "
                f"Padronize usando múltiplos de 24px: 24, 48, 72, 96px (Material Design)."
            )
        
        # Check Material Design compliance
        non_square_icons = [icon for icon in icons if icon.width != icon.height]
        if non_square_icons:
            recommendations.append(
                f"⬜ **{len(non_square_icons)} ícone(s) não quadrado(s)**. "
                f"Ícones devem ser quadrados conforme diretrizes do Material Design."
            )
        
        # Material Design standard sizes
        material_sizes = [24, 48, 72, 96, 144, 192]
        non_standard_icons = [
            icon for icon in icons 
            if not any(abs(max(icon.width, icon.height) - size) <= 4 for size in material_sizes)
        ]
        if non_standard_icons:
            recommendations.append(
                f"📏 **{len(non_standard_icons)} ícone(s) com tamanhos não padronizados**. "
                f"Use múltiplos de 24px (24, 48, 72, 96, 144, 192px) para melhor consistência."
            )
        
        # Overall icon quality assessment
        if avg_icon_score < 70:
            recommendations.append(
                f"🎯 **Score médio dos ícones: {avg_icon_score:.1f}/100**. "
                f"Considere usar ícones da biblioteca oficial do Material Design para garantir qualidade e consistência."
            )
        elif avg_icon_score >= 85:
            recommendations.append(
                f"✨ **Excelente qualidade dos ícones** (score médio: {avg_icon_score:.1f}/100). "
                f"Seus ícones seguem bem as diretrizes de design!"
            )
    
    # Overall project assessment
    overall_score = scores['overall_score']
    if overall_score >= 90:
        recommendations.append(
            f"🎉 **Projeto exemplar!** Score geral: {overall_score:.1f}/100. "
            f"Seus assets visuais seguem excelentes padrões de qualidade."
        )
    elif overall_score >= 75:
        recommendations.append(
            f"👍 **Boa qualidade geral** (score: {overall_score:.1f}/100). "
            f"Pequenos ajustes podem elevar seu projeto ao nível de excelência."
        )
    elif overall_score >= 50:
        recommendations.append(
            f"⚠️ **Qualidade moderada** (score: {overall_score:.1f}/100). "
            f"Foque nos assets com menor pontuação para melhorar significativamente o projeto."
        )
    else:
        recommendations.append(
            f"🔧 **Projeto precisa de atenção** (score: {overall_score:.1f}/100). "
            f"Revise a qualidade dos assets seguindo as recomendações específicas acima."
        )
    
    # Material Design promotion
    if icons.exists():
        recommendations.append(
            f"💡 **Dica Pro:** Explore a biblioteca oficial do Material Design "
            f"(https://fonts.google.com/icons) para ícones de alta qualidade que seguem "
            f"automaticamente todas as diretrizes de design."
        )
    
    if not recommendations:
        recommendations.append("✨ **Perfeito!** Nenhum problema detectado nos assets visuais.")
    
    return '\n'.join(recommendations)
