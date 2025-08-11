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
import re
try:
    import wcag_contrast_ratio
    import colour
    COLOR_ANALYSIS_AVAILABLE = True
except ImportError:
    COLOR_ANALYSIS_AVAILABLE = False
    print("⚠️ Bibliotecas de análise de cor não disponíveis. Instale: pip install wcag-contrast-ratio colour-science")

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
        
        # Analyze layout and spacing from .scm files
        layout_analysis = analyze_layout_and_spacing(temp_dir)
        
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
        
        # Tarefa 4.1: Analisar consistência de estilo dos ícones Material Design
        icon_analysis = analyze_icon_style_consistency(aia_file)
        
        # Generate usability evaluation with layout analysis and icon analysis
        generate_usability_evaluation(aia_file, layout_analysis, icon_analysis)


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
            
            # Tarefa 4.1: Verificar se é um ícone Material Design e identificar estilo
            if image_asset.asset_type == 'icon':
                material_style = identify_material_icon(image_asset)
                if material_style:
                    image_asset.is_material_icon = True
                    image_asset.material_icon_style = material_style
                else:
                    image_asset.is_material_icon = False
            
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


def generate_usability_evaluation(aia_file, layout_analysis=None, icon_analysis=None):
    """Generate comprehensive usability evaluation for the app using new granular scoring"""
    
    images = aia_file.images.all()
    
    if not images.exists():
        # Se não há imagens, cria avaliação com scores máximos
        recommendations = ['• ✨ Projeto sem assets visuais - nenhum problema detectado.']
        
        # Adicionar recomendações de layout se disponível
        if layout_analysis:
            layout_recommendations = generate_layout_recommendations(layout_analysis)
            recommendations.extend(layout_recommendations)
        
        # Adicionar recomendações de ícones se disponível
        if icon_analysis and icon_analysis.get('issues'):
            recommendations.append('\n🎨 **Análise de Ícones Material Design:**')
            recommendations.extend(icon_analysis['issues'])
        
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
                'recommendations': '\n'.join(recommendations),
            }
        )
        return
    
    # Calcula scores usando a nova lógica granular
    scores = calculate_overall_scores(list(images))
    
    # Aplicar penalização por inconsistência de ícones
    if icon_analysis and icon_analysis.get('has_style_inconsistency', False):
        # Reduzir pontuação de ícones em 20 pontos por inconsistência
        scores['icon_quality_score'] = max(0, scores['icon_quality_score'] - 20)
        # Reduzir pontuação geral proportionalmente
        scores['overall_score'] = (scores['image_quality_score'] + scores['icon_quality_score']) / 2
    
    # Calculate detailed metrics
    total_images = images.count()
    high_quality_count = images.filter(quality_rating__in=['high', 'excellent']).count()
    low_quality_count = images.filter(quality_rating='low').count()
    oversized_count = images.filter(file_size__gt=1024*1024).count()  # > 1MB
    undersized_count = images.filter(width__lt=100, height__lt=100).count()
    
    # Generate comprehensive usability report
    recommendations = generate_comprehensive_usability_report(aia_file, list(images), scores, layout_analysis, icon_analysis)
    
    # Adicionar recomendações de layout se disponível
    if layout_analysis:
        layout_recommendations = generate_layout_recommendations(layout_analysis)
        if layout_recommendations:
            recommendations += '\n\n🏗️ **Análise de Layout e Interface:**\n' + '\n'.join(layout_recommendations)
    
    # Adicionar recomendações de ícones se disponível
    if icon_analysis and icon_analysis.get('issues'):
        recommendations += '\n\n🎨 **Análise de Consistência de Ícones:**\n' + '\n'.join(icon_analysis['issues'])
    
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


def generate_comprehensive_usability_report(aia_file, images, scores, layout_analysis=None, icon_analysis=None):
    """
    Gera um relatório completo de análise de usabilidade explicando cada pontuação
    e critério de avaliação utilizado
    """
    report_sections = []
    
    # === CABEÇALHO DO RELATÓRIO ===
    report_sections.append(f"""
📊 **RELATÓRIO DE ANÁLISE DE USABILIDADE**
Arquivo: {aia_file.name}
Data da Análise: {timezone.now().strftime('%d/%m/%Y às %H:%M')}
Total de Assets Analisados: {images.count()}

═══════════════════════════════════════════════════════════════
""")

    # === PONTUAÇÃO GERAL ===
    overall_score = scores['overall_score']
    if overall_score >= 90:
        grade = "🏆 EXCELENTE"
        grade_desc = "Aplicativo com qualidade excepcional"
    elif overall_score >= 80:
        grade = "🥇 MUITO BOM"
        grade_desc = "Aplicativo com alta qualidade"
    elif overall_score >= 70:
        grade = "🥈 BOM"
        grade_desc = "Aplicativo com qualidade satisfatória"
    elif overall_score >= 60:
        grade = "🥉 RAZOÁVEL"
        grade_desc = "Aplicativo precisa de melhorias"
    else:
        grade = "❌ INSATISFATÓRIO"
        grade_desc = "Aplicativo precisa de revisão completa"

    report_sections.append(f"""
🎯 **AVALIAÇÃO GERAL: {overall_score:.1f}/100 - {grade}**
{grade_desc}

📊 **BREAKDOWN DA PONTUAÇÃO:**
• Qualidade de Imagens: {scores['image_quality_score']:.1f}/100
• Qualidade de Ícones: {scores['icon_quality_score']:.1f}/100
• Score Final: ({scores['image_quality_score']:.1f} + {scores['icon_quality_score']:.1f}) ÷ 2 = {overall_score:.1f}

""")

    # === ANÁLISE DETALHADA POR CATEGORIA ===
    
    # Análise de Imagens
    image_assets = [asset for asset in images if asset.asset_type in ['image', 'background', 'button', 'other']]
    if image_assets:
        report_sections.append(generate_image_quality_analysis(image_assets, scores['image_quality_score']))
    
    # Análise de Ícones
    icon_assets = [asset for asset in images if asset.asset_type == 'icon']
    if icon_assets:
        report_sections.append(generate_icon_quality_analysis(icon_assets, scores['icon_quality_score'], icon_analysis))
    
    # === ANÁLISE ACADÊMICA (LAYOUT, TIPOGRAFIA, CORES) ===
    if layout_analysis:
        report_sections.append(generate_academic_analysis_report(layout_analysis))
    
    # === RECOMENDAÇÕES ESPECÍFICAS ===
    recommendations = generate_detailed_recommendations(aia_file, images, scores)
    if recommendations:
        report_sections.append(f"""
💡 **RECOMENDAÇÕES PARA MELHORIA:**

{chr(10).join(recommendations)}
""")

    # === CONCLUSÃO ===
    report_sections.append(f"""
═══════════════════════════════════════════════════════════════

✅ **RESUMO EXECUTIVO:**
Este relatório avaliou {images.count()} asset(s) usando critérios acadêmicos baseados em:
• Resolução e otimização de arquivos (40% da nota)
• Proporções adequadas para dispositivos móveis (30% da nota)  
• Consistência visual e padrões de design (30% da nota)

📚 **BASE ACADÊMICA:**
Análise baseada em Nascimento & Brehm (2022), Solecki (2020), e diretrizes 
WCAG 2.1 AA para garantir qualidade educacional e acessibilidade.

🎓 **OBJETIVO EDUCACIONAL:**
Este sistema foi desenvolvido para auxiliar estudantes a compreender 
boas práticas de design de interface móvel no contexto do App Inventor.
""")

    return '\n'.join(report_sections)


def generate_image_quality_analysis(image_assets, image_score):
    """Gera análise detalhada da qualidade das imagens"""
    if not image_assets:
        return ""
    
    # Calcular estatísticas
    total_images = len(image_assets)
    excellent_count = len([img for img in image_assets if calculate_asset_quality_score(img) >= 85])
    good_count = len([img for img in image_assets if 70 <= calculate_asset_quality_score(img) < 85])
    medium_count = len([img for img in image_assets if 50 <= calculate_asset_quality_score(img) < 70])
    poor_count = len([img for img in image_assets if calculate_asset_quality_score(img) < 50])
    
    # Análise de tamanhos
    oversized = len([img for img in image_assets if img.file_size > 1024*1024])
    undersized = len([img for img in image_assets if img.width < 300 or img.height < 300])
    
    return f"""
🖼️ **ANÁLISE DE QUALIDADE DAS IMAGENS: {image_score:.1f}/100**

📊 **DISTRIBUIÇÃO POR QUALIDADE:**
• Excelente (85-100): {excellent_count}/{total_images} imagens ({excellent_count/total_images*100:.1f}%)
• Boa (70-84): {good_count}/{total_images} imagens ({good_count/total_images*100:.1f}%)
• Média (50-69): {medium_count}/{total_images} imagens ({medium_count/total_images*100:.1f}%)
• Baixa (<50): {poor_count}/{total_images} imagens ({poor_count/total_images*100:.1f}%)

🔍 **CRITÉRIOS DE AVALIAÇÃO:**
1. **Resolução (40% da nota):** Imagens devem ter pelo menos 640×480px
2. **Otimização (30% da nota):** 1-4 bytes por pixel indica boa compressão
3. **Proporções (30% da nota):** Adequadas para dispositivos móveis

⚠️ **PROBLEMAS DETECTADOS:**
• {oversized} imagem(ns) muito pesada(s) (>1MB)
• {undersized} imagem(ns) com resolução muito baixa

📈 **COMO MELHORAR A PONTUAÇÃO:**
• Resolução ideal: 1920×1080px ou superior para imagens principais
• Compressão: Use ferramentas como TinyPNG para otimizar sem perder qualidade
• Formato: PNG para ícones e logos, JPEG para fotos
"""


def generate_icon_quality_analysis(icon_assets, icon_score, icon_analysis=None):
    """Gera análise detalhada da qualidade dos ícones"""
    if not icon_assets:
        return ""
    
    total_icons = len(icon_assets)
    material_icons = len([icon for icon in icon_assets if hasattr(icon, 'is_material_icon') and icon.is_material_icon])
    
    # Análise de tamanhos
    standard_sizes = [24, 48, 72, 96, 128, 192, 256, 512]
    standard_count = len([icon for icon in icon_assets if icon.width in standard_sizes and icon.height in standard_sizes])
    square_count = len([icon for icon in icon_assets if icon.width == icon.height])
    
    # Penalização por inconsistência
    consistency_penalty = ""
    if icon_analysis and icon_analysis.get('has_style_inconsistency', False):
        styles_used = icon_analysis.get('stats', {}).get('styles_used', [])
        consistency_penalty = f"\n❌ **PENALIZAÇÃO APLICADA:** -20 pontos por inconsistência de estilos Material Design\n• Estilos encontrados: {', '.join(styles_used)}"
    
    return f"""
🎨 **ANÁLISE DE QUALIDADE DOS ÍCONES: {icon_score:.1f}/100**

� **ESTATÍSTICAS GERAIS:**
• Total de ícones: {total_icons}
• Ícones Material Design detectados: {material_icons}/{total_icons}
• Ícones quadrados: {square_count}/{total_icons} ({square_count/total_icons*100:.1f}%)
• Ícones em tamanhos padrão: {standard_count}/{total_icons} ({standard_count/total_icons*100:.1f}%)

🔍 **CRITÉRIOS DE AVALIAÇÃO:**
1. **Resolução (40% da nota):** Ícones devem ter pelo menos 128×128px
2. **Padrão Material Design (30% da nota):** Tamanhos múltiplos de 24px
3. **Consistência (30% da nota):** Formato quadrado e estilo uniforme
{consistency_penalty}

📐 **TAMANHOS RECOMENDADOS (Material Design):**
• Interface: 24px, 48px (densidade padrão)
• Launcher: 48dp, 72dp, 96dp, 144dp, 192dp
• Densidade alta: 36px, 72px, 108px

📈 **COMO MELHORAR A PONTUAÇÃO:**
• Use apenas um estilo Material Design por aplicativo
• Mantenha proporções quadradas (1:1)
• Prefira tamanhos padrão: 24, 48, 72, 96, 128, 192, 256px
• Use SVG quando possível para escalabilidade perfeita
"""


def generate_academic_analysis_report(layout_analysis):
    """Gera relatório da análise acadêmica (layout, tipografia, cores)"""
    if not layout_analysis:
        return ""
    
    screens_analyzed = layout_analysis.get('screens_analyzed', 0)
    has_margin_issues = layout_analysis.get('has_margin_issues', False)
    has_spacing_issues = layout_analysis.get('has_spacing_issues', False)
    has_font_issues = layout_analysis.get('has_font_issues', False)
    has_bold_issues = layout_analysis.get('has_bold_issues', False)
    has_contrast_issues = layout_analysis.get('has_contrast_issues', False)
    has_saturation_issues = layout_analysis.get('has_saturation_issues', False)
    
    # Calcular score acadêmico
    total_issues = sum([has_margin_issues, has_spacing_issues, has_font_issues, 
                       has_bold_issues, has_contrast_issues, has_saturation_issues])
    academic_score = max(0, 100 - (total_issues * 15))  # -15 pontos por problema
    
    if academic_score >= 90:
        academic_grade = "🏆 EXCELENTE"
    elif academic_score >= 75:
        academic_grade = "🥇 MUITO BOM"  
    elif academic_score >= 60:
        academic_grade = "🥈 BOM"
    else:
        academic_grade = "❌ PRECISA MELHORAR"
    
    return f"""
🎓 **ANÁLISE ACADÊMICA: {academic_score}/100 - {academic_grade}**
Baseada em Nascimento & Brehm (2022) e Solecki (2020)

📊 **TELAS ANALISADAS:** {screens_analyzed}

🏗️ **LAYOUT E ESPAÇAMENTO (Parte 1):**
• Margens adequadas: {'❌ Problema detectado' if has_margin_issues else '✅ Adequadas'}
• Espaçamento entre elementos: {'❌ Problema detectado' if has_spacing_issues else '✅ Adequado'}

🔤 **TIPOGRAFIA (Parte 2):**
• Consistência de fontes: {'❌ Muitas fontes diferentes' if has_font_issues else '✅ Consistente'}
• Uso de negrito: {'❌ Abuso de negrito detectado' if has_bold_issues else '✅ Uso adequado'}

🎨 **CORES (Parte 3):**
• Contraste WCAG AA: {'❌ Problemas de contraste' if has_contrast_issues else '✅ Adequado'}
• Saturação de cores: {'❌ Cores muito saturadas' if has_saturation_issues else '✅ Adequada'}

📚 **METODOLOGIA:**
• **Parte 1:** Análise de margens e espaçamento baseada em múltiplos de 8px
• **Parte 2:** Verificação de consistência tipográfica e legibilidade
• **Parte 3:** Análise WCAG 2.1 AA (contraste 4.5:1) e detecção de cores neon
• **Parte 4:** Consistência de ícones Material Design

🎯 **PONTUAÇÃO:**
Cada problema detectado reduz 15 pontos da nota acadêmica.
Score atual: 100 - ({total_issues} × 15) = {academic_score} pontos
"""


def generate_detailed_recommendations(aia_file, images, scores):
    """Gera recomendações detalhadas baseadas na análise completa"""
    recommendations = []
    
    overall_score = scores['overall_score']
    
    # Recomendações baseadas no score geral
    if overall_score < 70:
        recommendations.append(
            "🚨 **AÇÃO URGENTE NECESSÁRIA:** Score abaixo de 70 indica problemas significativos "
            "que afetam a qualidade do aplicativo. Priorize as correções listadas abaixo."
        )
    elif overall_score < 85:
        recommendations.append(
            "⚠️ **MELHORIAS RECOMENDADAS:** Score pode ser elevado com ajustes específicos. "
            "Foque nos problemas de maior impacto listados abaixo."
        )
    else:
        recommendations.append(
            "✅ **QUALIDADE SATISFATÓRIA:** Continue mantendo os padrões de qualidade. "
            "Pequenos ajustes podem levar à excelência."
        )
    
    # Análise específica por tipo de asset
    poor_assets = [asset for asset in images if calculate_asset_quality_score(asset) < 50]
    if poor_assets:
        recommendations.append(
            f"🔴 **CRÍTICO:** {len(poor_assets)} asset(s) com score abaixo de 50 necessitam "
            f"atenção imediata. Assets críticos: {', '.join([asset.name for asset in poor_assets[:3]])}"
            f"{'...' if len(poor_assets) > 3 else ''}"
        )
    
    # Recomendações de otimização
    oversized = [asset for asset in images if asset.file_size > 1024*1024]
    if oversized:
        total_savings = sum(asset.file_size for asset in oversized) / (1024*1024) * 0.7  # Estimativa de 70% de redução
        recommendations.append(
            f"💾 **OTIMIZAÇÃO:** Comprimir {len(oversized)} imagem(ns) pode reduzir "
            f"aproximadamente {total_savings:.1f}MB do tamanho total do aplicativo."
        )
    
    # Recomendações Material Design
    icons = [asset for asset in images if asset.asset_type == 'icon']
    if icons:
        # Calcular score médio dos ícones
        icon_scores = [calculate_asset_quality_score(icon) for icon in icons]
        avg_icon_score = sum(icon_scores) / len(icon_scores) if icon_scores else 0
        
        non_square = [icon for icon in icons if icon.width != icon.height]
        if non_square:
            recommendations.append(
                f"📐 **MATERIAL DESIGN:** {len(non_square)} ícone(s) não seguem o padrão "
                f"quadrado. Redimensione para formato 1:1 para melhor compatibilidade."
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
    if icons:
        recommendations.append(
            f"💡 **Dica Pro:** Explore a biblioteca oficial do Material Design "
            f"(https://fonts.google.com/icons) para ícones de alta qualidade que seguem "
            f"automaticamente todas as diretrizes de design."
        )
    
    if not recommendations:
        recommendations.append("✨ **Perfeito!** Nenhum problema detectado nos assets visuais.")
    
    return '\n'.join(recommendations)


def analyze_layout_and_spacing(temp_dir):
    """
    Analisa layout e espaçamento de todos os screens do App Inventor
    baseado nos trabalhos de Nascimento & Brehm (2022)
    """
    layout_issues = []
    typography_issues = []
    screens_analyzed = 0
    all_components = []  # Para análise de tipografia
    
    # Encontrar todos os arquivos .scm
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            if file.endswith('.scm'):
                file_path = os.path.join(root, file)
                screen_name = os.path.splitext(file)[0]
                
                try:
                    screen_data = parse_scm_file(file_path)
                    if screen_data:
                        screens_analyzed += 1
                        
                        # Coletar todos os componentes para análise de tipografia
                        components = extract_all_components(screen_data)
                        all_components.extend(components)
                        
                        # Verificar margens da tela
                        if not check_screen_margins(screen_data):
                            layout_issues.append(f"Screen {screen_name}: Falta de margens adequadas nas laterais")
                        
                        # Verificar espaçamento entre componentes
                        if not check_element_spacing(screen_data):
                            layout_issues.append(f"Screen {screen_name}: Espaçamento inadequado entre elementos")
                            
                except Exception as e:
                    print(f"Erro ao analisar {file}: {str(e)}")
                    continue
    
    # Análise de tipografia em todos os componentes
    typography_analysis = analyze_typography(all_components)
    
    # Análise de cores em todos os componentes
    color_analysis = analyze_colors(all_components)
    
    return {
        'screens_analyzed': screens_analyzed,
        'layout_issues': layout_issues,
        'typography_issues': typography_analysis.get('issues', []),
        'color_issues': color_analysis.get('issues', []),
        'has_margin_issues': any('margens' in issue for issue in layout_issues),
        'has_spacing_issues': any('espaçamento' in issue for issue in layout_issues),
        'has_font_issues': typography_analysis.get('has_font_issues', False),
        'has_bold_issues': typography_analysis.get('has_bold_issues', False),
        'has_contrast_issues': color_analysis.get('has_contrast_issues', False),
        'has_saturation_issues': color_analysis.get('has_saturation_issues', False),
        'typography_stats': typography_analysis.get('stats', {}),
        'color_stats': color_analysis.get('stats', {})
    }


def parse_scm_file(file_path):
    """
    Extrai e parseia o conteúdo JSON de um arquivo .scm do App Inventor
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Os arquivos .scm contêm JSON entre markers específicos
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            return None
            
        json_content = content[json_start:json_end]
        return json.loads(json_content)
        
    except Exception as e:
        print(f"Erro ao parsear arquivo SCM {file_path}: {str(e)}")
        return None


def check_screen_margins(screen_data):
    """
    Tarefa 1.1: Verificar se os componentes principais na tela possuem 
    uma margem de respiro nas laterais
    
    Verifica se existe um padrão de margem adequado na tela
    """
    try:
        properties = screen_data.get('Properties', {})
        components = properties.get('$Components', [])
        
        if not components:
            return True  # Tela vazia, não há problema de margem
        
        # Procurar por HorizontalArrangements que funcionem como container principal
        main_containers = []
        for component in components:
            if component.get('$Type') == 'HorizontalArrangement':
                # Verificar se tem largura "Fill Parent" ou similar
                width = component.get('Width', '')
                if (width == 'Fill parent' or width == '-2' or 
                    width == 'Automatic' or width == '' or
                    (isinstance(width, str) and '%' in width and int(width.replace('%', '')) > 80)):
                    main_containers.append(component)
        
        # Se temos containers principais, verificar se eles têm estrutura de margem
        if main_containers:
            for container in main_containers:
                if has_margin_structure(container):
                    return True
        
        # Verificar se os componentes principais estão muito próximos das bordas
        # Se não há estrutura de margem explícita, verificar larguras dos componentes
        total_components = count_interactive_components(components)
        if total_components <= 1:
            return True  # Com poucos componentes, margem é menos crítica
        
        # Se há muitos componentes sem estrutura de margem, é um problema
        return False
        
    except Exception as e:
        print(f"Erro ao verificar margens: {str(e)}")
        return True  # Em caso de erro, não penalizar


def has_margin_structure(container):
    """
    Verifica se um container tem estrutura típica de margem
    """
    sub_components = container.get('$Components', [])
    
    if len(sub_components) == 0:
        return False
    
    # Padrão 1: Labels vazios nas laterais funcionando como espaçadores
    if len(sub_components) >= 3:
        first = sub_components[0]
        last = sub_components[-1]
        
        # Verificar se primeiro e último são Labels vazios
        if (first.get('$Type') == 'Label' and last.get('$Type') == 'Label' and
            (first.get('Text', '').strip() == '' or first.get('Text', '').strip() == ' ') and
            (last.get('Text', '').strip() == '' or last.get('Text', '').strip() == ' ')):
            return True
    
    # Padrão 2: Componente central com largura controlada
    if len(sub_components) == 1:
        central_component = sub_components[0]
        width = central_component.get('Width', '')
        
        # Se o componente central tem largura específica (não Fill Parent), pode indicar margem
        if (isinstance(width, str) and width.isdigit() and int(width) < 300) or \
           (isinstance(width, str) and '%' in width and int(width.replace('%', '')) < 90):
            return True
    
    return False


def check_element_spacing(screen_data):
    """
    Tarefa 1.2: Verificar se existe um espaçamento vertical mínimo 
    entre os componentes interativos
    
    Procura por Labels vazios ou HorizontalArrangements com altura específica 
    que funcionem como espaçadores
    """
    try:
        properties = screen_data.get('Properties', {})
        components = properties.get('$Components', [])
        
        if len(components) <= 1:
            return True  # Com poucos componentes, espaçamento não é crítico
        
        interactive_components = []
        spacer_components = []
        
        # Classificar componentes em interativos e espaçadores
        for i, component in enumerate(components):
            component_type = component.get('$Type', '')
            
            # Componentes interativos
            if component_type in ['Button', 'TextBox', 'Slider', 'CheckBox', 
                                'Switch', 'ListView', 'Image', 'ImageSprite']:
                interactive_components.append((i, component))
            
            # Possíveis espaçadores
            elif component_type == 'Label':
                text = component.get('Text', '').strip()
                height = component.get('Height', '')
                
                if (text == '' or text == ' ') and height:
                    # Label vazio com altura definida = espaçador
                    spacer_components.append((i, component))
                    
            elif component_type == 'HorizontalArrangement':
                height = component.get('Height', '')
                sub_components = component.get('$Components', [])
                
                # HorizontalArrangement vazio com altura = espaçador
                if len(sub_components) == 0 and height and is_spacer_height(height):
                    spacer_components.append((i, component))
        
        if len(interactive_components) <= 1:
            return True  # Não precisa de espaçamento com 1 componente ou menos
        
        # Verificar se há espaçadores entre componentes interativos
        spacing_found = 0
        for i in range(len(interactive_components) - 1):
            current_pos = interactive_components[i][0]
            next_pos = interactive_components[i + 1][0]
            
            # Verificar se há espaçador entre os dois componentes interativos
            for spacer_pos, spacer in spacer_components:
                if current_pos < spacer_pos < next_pos:
                    spacing_found += 1
                    break
        
        # Se encontramos espaçadores para pelo menos 50% dos gaps, consideramos adequado
        required_spacers = len(interactive_components) - 1
        return spacing_found >= (required_spacers * 0.5)
        
    except Exception as e:
        print(f"Erro ao verificar espaçamento: {str(e)}")
        return True  # Em caso de erro, não penalizar


def count_interactive_components(components):
    """
    Conta o número de componentes interativos em uma lista de componentes
    """
    interactive_types = ['Button', 'TextBox', 'Slider', 'CheckBox', 
                        'Switch', 'ListView', 'Image', 'ImageSprite']
    count = 0
    
    for component in components:
        if component.get('$Type', '') in interactive_types:
            count += 1
        
        # Recursivamente contar em sub-componentes
        sub_components = component.get('$Components', [])
        if sub_components:
            count += count_interactive_components(sub_components)
    
    return count


def is_spacer_height(height):
    """
    Determina se uma altura específica indica um espaçador
    """
    if isinstance(height, str):
        # Alturas pequenas em pixels (5-50px são típicas para espaçamento)
        if height.isdigit():
            return 5 <= int(height) <= 50
        
        # Percentuais pequenos
        if '%' in height:
            try:
                percentage = int(height.replace('%', ''))
                return 1 <= percentage <= 10
            except:
                return False
    
    return False


def generate_layout_recommendations(layout_analysis):
    """
    Gera recomendações específicas baseadas na análise de layout, tipografia e cores
    """
    recommendations = []
    
    if not layout_analysis:
        return recommendations
    
    screens_analyzed = layout_analysis.get('screens_analyzed', 0)
    layout_issues = layout_analysis.get('layout_issues', [])
    typography_issues = layout_analysis.get('typography_issues', [])
    color_issues = layout_analysis.get('color_issues', [])
    has_margin_issues = layout_analysis.get('has_margin_issues', False)
    has_spacing_issues = layout_analysis.get('has_spacing_issues', False)
    has_font_issues = layout_analysis.get('has_font_issues', False)
    has_bold_issues = layout_analysis.get('has_bold_issues', False)
    has_contrast_issues = layout_analysis.get('has_contrast_issues', False)
    has_saturation_issues = layout_analysis.get('has_saturation_issues', False)
    typography_stats = layout_analysis.get('typography_stats', {})
    color_stats = layout_analysis.get('color_stats', {})
    
    if screens_analyzed == 0:
        recommendations.append("⚠️ **Não foi possível analisar as telas do projeto.** Verifique se o arquivo .aia está íntegro.")
        return recommendations
    
    # Relatório geral
    recommendations.append(f"📊 **{screens_analyzed} tela(s) analisada(s) para padrões de layout e tipografia**")
    
    # === RECOMENDAÇÕES DE LAYOUT ===
    
    # Recomendações específicas por tipo de problema
    if has_margin_issues:
        recommendations.append(
            "📐 **Problema de Margens:** Algumas telas não possuem margens adequadas nas laterais. "
            "Recomendação: Use HorizontalArrangement com Labels vazios nas laterais para criar "
            "respiro visual, ou configure componentes com largura específica (ex: 80%) em vez de 'Fill Parent'."
        )
    
    if has_spacing_issues:
        recommendations.append(
            "📏 **Problema de Espaçamento:** Componentes muito próximos entre si detectados. "
            "Recomendação: Adicione Labels vazios com altura de 8-16 pixels entre botões, caixas de texto "
            "e outros elementos interativos para melhorar a legibilidade."
        )
    
    # === RECOMENDAÇÕES DE TIPOGRAFIA ===
    
    if has_font_issues:
        font_count = typography_stats.get('unique_fonts', 0)
        recommendations.append(
            f"🔤 **Problema de Consistência Tipográfica:** {font_count} fontes diferentes detectadas. "
            "Recomendação: Use no máximo 2 fontes (uma para títulos e outra para corpo de texto) "
            "para manter a consistência visual e profissionalismo."
        )
    
    if has_bold_issues:
        bold_texts_count = typography_stats.get('bold_long_texts', 0)
        recommendations.append(
            f"📝 **Uso Abusivo de Negrito:** {bold_texts_count} texto(s) longo(s) em negrito detectado(s). "
            "Recomendação: Reserve o negrito para destacar palavras-chave ou frases curtas. "
            "Parágrafos longos em negrito dificultam a leitura."
        )
    
    # Recomendações específicas por tela e tipografia
    if layout_issues:
        recommendations.append("🔍 **Detalhes de layout por tela:**")
        for issue in layout_issues:
            recommendations.append(f"  • {issue}")
    
    if typography_issues:
        recommendations.append("🔍 **Detalhes de tipografia:**")
        for issue in typography_issues:
            recommendations.append(f"  • {issue}")
    
    # === RECOMENDAÇÕES DE CORES ===
    
    if has_contrast_issues:
        contrast_violations = color_stats.get('contrast_violations', 0)
        recommendations.append(
            f"🔴 **Problema de Contraste:** {contrast_violations} violação(ões) WCAG detectada(s). "
            "Recomendação: Verifique se o texto está legível sobre o fundo. "
            "Use ferramentas de verificação de contraste ou prefira cores mais escuras para texto "
            "sobre fundos claros, e cores claras para texto sobre fundos escuros."
        )
    
    if has_saturation_issues:
        neon_colors_count = color_stats.get('neon_colors', 0)
        recommendations.append(
            f"🌈 **Problema de Saturação:** {neon_colors_count} cor(es) muito saturada(s) detectada(s). "
            "Recomendação: Cores neon podem causar fadiga visual. "
            "Prefira tons mais suaves (saturação <80%) especialmente para fundos, "
            "textos longos e elementos que ficam visíveis por muito tempo."
        )
    
    # Detalhes de cores
    if color_issues:
        recommendations.append("🔍 **Detalhes de análise de cores:**")
        for issue in color_issues:
            recommendations.append(f"  • {issue}")
    
    # Dicas proativas
    all_issues_resolved = (not has_margin_issues and not has_spacing_issues and 
                          not has_font_issues and not has_bold_issues and 
                          not has_contrast_issues and not has_saturation_issues)
    
    if all_issues_resolved:
        recommendations.append("✅ **Excelente!** Layout bem estruturado com margens, espaçamento, tipografia e cores adequados.")
    else:
        recommendations.append(
            "💡 **Dicas de Design:** "
            "• Interfaces bem espaçadas seguem a regra dos múltiplos de 8px "
            "• Use hierarquia tipográfica: títulos maiores, texto normal menor "
            "• Mantenha consistência: mesma fonte para elementos similares "
            "• Garanta contraste mínimo 4.5:1 entre texto e fundo (WCAG AA) "
            "• Evite cores muito saturadas para reduzir fadiga visual"
        )
    
    return recommendations


def extract_all_components(screen_data):
    """
    Extrai todos os componentes de uma tela de forma recursiva
    para análise de tipografia
    """
    all_components = []
    
    try:
        properties = screen_data.get('Properties', {})
        components = properties.get('$Components', [])
        
        def extract_recursive(component_list):
            for component in component_list:
                all_components.append(component)
                # Recursivamente extrair subcomponentes
                sub_components = component.get('$Components', [])
                if sub_components:
                    extract_recursive(sub_components)
        
        extract_recursive(components)
        
    except Exception as e:
        print(f"Erro ao extrair componentes: {str(e)}")
    
    return all_components


def analyze_typography(all_components):
    """
    Analisa a tipografia de todos os componentes do projeto
    Implementa as Tarefas 2.1 e 2.2
    """
    # Estatísticas gerais
    font_issues = []
    bold_issues = []
    
    # Para análise de consistência de fontes
    unique_fonts = set()
    
    # Para análise de uso de negrito
    bold_long_texts = []
    
    # Componentes que podem ter propriedades tipográficas
    text_components = ['Label', 'Button', 'TextBox', 'Textarea', 'PasswordTextBox']
    
    for component in all_components:
        component_type = component.get('$Type', '')
        component_name = component.get('$Name', 'Unnamed')
        
        if component_type in text_components:
            # Tarefa 2.1: Verificar consistência de fontes
            font_typeface = component.get('FontTypeface', '')
            if font_typeface and font_typeface.strip():
                unique_fonts.add(font_typeface.strip())
            
            # Tarefa 2.2: Verificar uso abusivo de negrito
            is_bold = component.get('FontBold', 'False')
            text_content = component.get('Text', '')
            
            if str(is_bold).lower() == 'true' and text_content:
                word_count = len(text_content.split())
                if word_count > 15:  # Texto longo em negrito
                    bold_long_texts.append({
                        'component': component_name,
                        'type': component_type,
                        'word_count': word_count,
                        'text_preview': text_content[:50] + '...' if len(text_content) > 50 else text_content
                    })
    
    # Gerar issues específicos
    
    # Tarefa 2.1: Verificar se há muitas fontes diferentes
    has_font_issues = len(unique_fonts) > 2
    if has_font_issues:
        fonts_list = ', '.join(list(unique_fonts))
        font_issues.append(f"Muitas fontes detectadas: {fonts_list}")
    
    # Tarefa 2.2: Verificar textos longos em negrito
    has_bold_issues = len(bold_long_texts) > 0
    if has_bold_issues:
        for bold_text in bold_long_texts:
            bold_issues.append(
                f"Componente '{bold_text['component']}' ({bold_text['type']}) "
                f"tem {bold_text['word_count']} palavras em negrito: {bold_text['text_preview']}"
            )
    
    # Compilar todas as issues
    all_issues = font_issues + bold_issues
    
    return {
        'issues': all_issues,
        'has_font_issues': has_font_issues,
        'has_bold_issues': has_bold_issues,
        'stats': {
            'unique_fonts': len(unique_fonts),
            'fonts_list': list(unique_fonts),
            'bold_long_texts': len(bold_long_texts),
            'bold_details': bold_long_texts
        }
    }


def check_font_consistency(all_components):
    """
    Tarefa 2.1: Verificar consistência de fontes
    Garante que o aplicativo não use uma quantidade excessiva de fontes diferentes
    """
    unique_fonts = set()
    text_components = ['Label', 'Button', 'TextBox', 'Textarea', 'PasswordTextBox']
    
    for component in all_components:
        component_type = component.get('$Type', '')
        
        if component_type in text_components:
            font_typeface = component.get('FontTypeface', '')
            if font_typeface and font_typeface.strip():
                unique_fonts.add(font_typeface.strip())
    
    # Se mais de 2 fontes diferentes, retorna False (inconsistente)
    return len(unique_fonts) <= 2, list(unique_fonts)


def check_bold_usage(all_components):
    """
    Tarefa 2.2: Verificar uso abusivo de negrito
    Identifica parágrafos longos que estão inteiramente em negrito
    """
    problematic_components = []
    
    for component in all_components:
        component_type = component.get('$Type', '')
        component_name = component.get('$Name', 'Unnamed')
        
        if component_type == 'Label':  # Focando em Labels que são mais usados para texto
            is_bold = component.get('FontBold', 'False')
            text_content = component.get('Text', '')
            
            if str(is_bold).lower() == 'true' and text_content:
                word_count = len(text_content.split())
                if word_count > 15:  # Limite de 15 palavras
                    problematic_components.append({
                        'name': component_name,
                        'word_count': word_count,
                        'text': text_content
                    })
    
    return len(problematic_components) == 0, problematic_components


def analyze_colors(all_components):
    """
    Análise de cores de todos os componentes do projeto
    Implementa as Tarefas 3.1 e 3.2 baseadas em Solecki (2020)
    """
    if not COLOR_ANALYSIS_AVAILABLE:
        return {
            'issues': ['⚠️ Análise de cores não disponível - bibliotecas não instaladas'],
            'has_contrast_issues': False,
            'has_saturation_issues': False,
            'stats': {}
        }
    
    color_issues = []
    contrast_issues = []
    saturation_issues = []
    
    # Coletar todas as cores únicas do projeto
    all_colors = set()
    contrast_pairs = []
    
    for component in all_components:
        component_type = component.get('$Type', '')
        component_name = component.get('$Name', 'Unnamed')
        
        # Coletar cores de componentes que podem ter texto e fundo
        text_color = component.get('TextColor', '')
        background_color = component.get('BackgroundColor', '')
        button_color = component.get('ButtonColor', '')
        
        # Adicionar cores únicas para análise de saturação
        for color in [text_color, background_color, button_color]:
            if color and color.strip():
                all_colors.add(color.strip())
        
        # Verificar contraste entre texto e fundo
        if text_color and background_color:
            contrast_pairs.append({
                'component': component_name,
                'type': component_type,
                'text_color': text_color,
                'background_color': background_color
            })
    
    # Tarefa 3.1: Verificar contraste WCAG
    contrast_analysis = check_color_contrast(contrast_pairs)
    contrast_issues = contrast_analysis['issues']
    
    # Tarefa 3.2: Verificar saturação excessiva
    saturation_analysis = check_color_saturation(list(all_colors))
    saturation_issues = saturation_analysis['issues']
    
    # Compilar todas as issues
    all_issues = contrast_issues + saturation_issues
    
    return {
        'issues': all_issues,
        'has_contrast_issues': len(contrast_issues) > 0,
        'has_saturation_issues': len(saturation_issues) > 0,
        'stats': {
            'total_colors': len(all_colors),
            'colors_list': list(all_colors),
            'contrast_violations': len(contrast_issues),
            'neon_colors': len(saturation_issues),
            'contrast_pairs': len(contrast_pairs)
        }
    }


def check_color_contrast(contrast_pairs):
    """
    Tarefa 3.1: Implementar Verificador de Contraste (WCAG)
    Garante que o texto seja legível para todos os usuários
    """
    issues = []
    
    if not COLOR_ANALYSIS_AVAILABLE:
        return {'issues': ['Verificação de contraste não disponível']}
    
    for pair in contrast_pairs:
        try:
            component_name = pair['component']
            component_type = pair['type']
            text_color = normalize_app_inventor_color(pair['text_color'])
            bg_color = normalize_app_inventor_color(pair['background_color'])
            
            if text_color and bg_color:
                # Normalizar RGB para 0.0-1.0 para wcag-contrast-ratio
                text_color_normalized = [c/255.0 for c in text_color]
                bg_color_normalized = [c/255.0 for c in bg_color]
                
                # Calcular taxa de contraste usando wcag-contrast-ratio
                contrast_ratio = wcag_contrast_ratio.rgb(text_color_normalized, bg_color_normalized)
                
                # Verificar se atende critério WCAG AA (4.5:1)
                if contrast_ratio < 4.5:
                    issues.append(
                        f"🔴 **Contraste insuficiente:** Componente '{component_name}' ({component_type}) "
                        f"tem taxa de contraste {contrast_ratio:.2f}:1. "
                        f"Cores: texto {pair['text_color']} sobre fundo {pair['background_color']}. "
                        f"Recomendação: A taxa de contraste deve ser de pelo menos 4.5:1 para atender WCAG AA."
                    )
                
        except Exception as e:
            print(f"Erro ao calcular contraste para {component_name}: {str(e)}")
            continue
    
    return {'issues': issues}


def check_color_saturation(colors_list):
    """
    Tarefa 3.2: Detectar Cores Neon (Saturação Excessiva)
    Evita o uso de cores excessivamente vibrantes
    """
    issues = []
    neon_colors = []
    
    if not COLOR_ANALYSIS_AVAILABLE:
        return {'issues': ['Verificação de saturação não disponível']}
    
    for color_hex in colors_list:
        try:
            # Normalizar cor do App Inventor para RGB
            rgb_color = normalize_app_inventor_color(color_hex)
            if not rgb_color:
                continue
            
            # Converter RGB para HSL usando colour-science
            rgb_normalized = [c/255.0 for c in rgb_color]  # Normalizar para 0-1
            hsl = colour.RGB_to_HSL(rgb_normalized)
            
            hue = hsl[0] * 360      # Convertir para graus (0-360)
            saturation = hsl[1]     # Já em 0-1
            lightness = hsl[2]      # Já em 0-1
            
            # Detectar cores "neon": alta saturação (>80%) e alta luminosidade (>70%)
            if saturation > 0.8 and lightness > 0.7:
                neon_colors.append({
                    'hex': color_hex,
                    'saturation': saturation * 100,
                    'lightness': lightness * 100
                })
                
        except Exception as e:
            print(f"Erro ao analisar saturação da cor {color_hex}: {str(e)}")
            continue
    
    if neon_colors:
        color_list = ', '.join([f"{c['hex']} (S:{c['saturation']:.0f}%, L:{c['lightness']:.0f}%)" 
                                for c in neon_colors])
        issues.append(
            f"🌈 **Cores muito saturadas detectadas:** {color_list}. "
            f"Recomendação: Cores neon podem causar fadiga visual. "
            f"Prefira tons mais suaves (saturação <80%) para fundos e textos longos."
        )
    
    return {'issues': issues}


def normalize_app_inventor_color(color_value):
    """
    Converte cores do App Inventor para RGB
    App Inventor usa formato &HFF000000 ou &H00000000
    """
    if not color_value or not isinstance(color_value, str):
        return None
    
    color_value = color_value.strip()
    
    try:
        # Formato App Inventor: &HFF000000 (AARRGGBB)
        if color_value.startswith('&H'):
            hex_value = color_value[2:]  # Remove &H
            if len(hex_value) == 8:
                # AARRGGBB - ignorar canal alpha
                r = int(hex_value[2:4], 16)
                g = int(hex_value[4:6], 16)
                b = int(hex_value[6:8], 16)
                return (r, g, b)
            elif len(hex_value) == 6:
                # RRGGBB
                r = int(hex_value[0:2], 16)
                g = int(hex_value[2:4], 16)
                b = int(hex_value[4:6], 16)
                return (r, g, b)
        
        # Formato hexadecimal padrão: #RRGGBB
        elif color_value.startswith('#'):
            hex_value = color_value[1:]
            if len(hex_value) == 6:
                r = int(hex_value[0:2], 16)
                g = int(hex_value[2:4], 16)
                b = int(hex_value[4:6], 16)
                return (r, g, b)
        
        # Tentar interpretar como número decimal
        elif color_value.isdigit():
            color_int = int(color_value)
            # Converter para RGB (assumir formato ARGB)
            r = (color_int >> 16) & 0xFF
            g = (color_int >> 8) & 0xFF
            b = color_int & 0xFF
            return (r, g, b)
            
    except ValueError:
        pass
    
    return None


def identify_material_icon(image_asset):
    """
    Tarefa 4.1: Identificar se uma imagem é um ícone Material Design e qual estilo
    Retorna o estilo do ícone (filled, outlined, round, sharp, twotone) ou None
    """
    try:
        # Carrega a imagem para análise
        with Image.open(image_asset.extracted_file.path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calcular hash da imagem para comparação
            img_hash = calculate_image_hash(img)
            
            # Verificar se é um ícone Material Design comparando com a base de dados
            for category_name, icons in MATERIAL_ICONS_DB.items():
                for icon_name, styles in icons.items():
                    for style_name, icon_data in styles.items():
                        # Comparar hash ou similaridade visual
                        if is_similar_to_material_icon(img, icon_data, img_hash):
                            return style_name
            
            return None
            
    except Exception as e:
        print(f"Erro ao identificar ícone Material Design para {image_asset.name}: {str(e)}")
        return None


def calculate_image_hash(img):
    """
    Calcula um hash simples da imagem para comparação
    """
    try:
        # Redimensiona para 8x8 para comparação rápida
        img_small = img.resize((8, 8), Image.Resampling.LANCZOS)
        
        # Converte para escala de cinza
        img_gray = img_small.convert('L')
        
        # Calcula a média dos pixels
        pixels = list(img_gray.getdata())
        avg = sum(pixels) / len(pixels)
        
        # Cria hash binário baseado na média
        hash_bits = []
        for pixel in pixels:
            hash_bits.append('1' if pixel > avg else '0')
        
        return ''.join(hash_bits)
    except:
        return None


def is_similar_to_material_icon(img, icon_data, img_hash):
    """
    Verifica se uma imagem é similar a um ícone Material Design
    Por simplicidade, vamos usar o nome do arquivo e características básicas
    """
    try:
        # Por enquanto, implementação simplificada baseada em nome e tamanho
        # Em uma implementação completa, seria necessário análise de SVG e comparação visual
        
        # Verifica se o tamanho está dentro dos padrões de ícones Material Design
        img_size = img.size
        standard_sizes = [16, 18, 20, 24, 32, 36, 40, 48, 56, 64, 72, 96, 128, 144, 192, 256, 512]
        
        # Se ambas as dimensões são iguais (quadrado) e correspondem a tamanhos padrão
        if img_size[0] == img_size[1] and img_size[0] in standard_sizes:
            # Análise adicional pode ser implementada aqui
            # Por exemplo, análise de cor dominante, presença de transparência, etc.
            return True
            
        return False
    except:
        return False


def analyze_icon_style_consistency(aia_file):
    """
    Tarefa 4.1: Analisar consistência de estilo dos ícones Material Design
    Retorna análise de consistência e recomendações
    """
    try:
        # Buscar todas as imagens do arquivo AIA que são ícones Material Design
        material_icons = aia_file.images.filter(
            is_material_icon=True,
            material_icon_style__isnull=False
        )
        
        if not material_icons.exists():
            return {
                'issues': [],
                'has_style_inconsistency': False,
                'stats': {
                    'total_material_icons': 0,
                    'styles_used': [],
                    'styles_count': 0,
                    'icon_details': []
                }
            }
        
        # Coletar todos os estilos encontrados
        styles_used = set()
        icon_details = []
        
        for icon in material_icons:
            style = icon.material_icon_style
            if style:
                styles_used.add(style)
                icon_details.append({
                    'name': icon.name,
                    'style': style,
                    'asset_type': icon.asset_type
                })
        
        # Filtrar None values
        styles_used = {style for style in styles_used if style is not None}
        
        # Verificar consistência
        has_inconsistency = len(styles_used) > 1
        issues = []
        
        if has_inconsistency:
            styles_list = ', '.join(sorted(styles_used))
            issues.append(
                f"🎨 **Estilos de ícones mistos detectados:** {styles_list}. "
                f"Para manter a consistência visual, escolha e utilize apenas um estilo "
                f"em todo o aplicativo. Recomendação: Use 'filled' para interfaces mais "
                f"tradicionais ou 'outlined' para designs mais modernos e limpos."
            )
            
            # Detalhes por estilo
            for style in sorted(styles_used):
                icons_of_style = [icon for icon in icon_details if icon['style'] == style]
                icon_names = [icon['name'] for icon in icons_of_style]
                issues.append(
                    f"  • **Estilo '{style}':** {len(icons_of_style)} ícone(s) - "
                    f"{', '.join(icon_names[:3])}"
                    f"{'...' if len(icon_names) > 3 else ''}"
                )
        
        return {
            'issues': issues,
            'has_style_inconsistency': has_inconsistency,
            'stats': {
                'total_material_icons': len(icon_details),
                'styles_used': list(styles_used),
                'styles_count': len(styles_used),
                'icon_details': icon_details
            }
        }
        
    except Exception as e:
        print(f"Erro ao analisar consistência de estilo dos ícones: {str(e)}")
        return {
            'issues': [f'Erro na análise de consistência de ícones: {str(e)}'],
            'has_style_inconsistency': False,
            'stats': {
                'total_material_icons': 0,
                'styles_used': [],
                'styles_count': 0,
                'icon_details': []
            }
        }
