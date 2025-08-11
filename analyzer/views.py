from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView
from django.core.files.storage import default_storage
from django.conf import settings
from .models import AiaFile, ImageAsset, UsabilityEvaluation
from .forms import AiaFileUploadForm
from .utils import analyze_aia_file, find_similar_material_icon, analyze_icon_against_material_design
import os


class AiaFileListView(ListView):
    """List all uploaded .aia files"""
    model = AiaFile
    template_name = 'analyzer/file_list.html'
    context_object_name = 'files'
    ordering = ['-uploaded_at']


def upload_file(request):
    """Handle .aia file upload"""
    if request.method == 'POST':
        form = AiaFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            aia_file = form.save(commit=False)
            if request.user.is_authenticated:
                aia_file.uploaded_by = request.user
            
            # Validate file extension
            if not aia_file.file.name.endswith('.aia'):
                messages.error(request, 'Por favor, envie apenas arquivos .aia')
                return render(request, 'analyzer/upload.html', {'form': form})
            
            aia_file.save()
            messages.success(request, f'Arquivo {aia_file.name} enviado com sucesso!')
            return redirect('file_detail', pk=aia_file.pk)
    else:
        form = AiaFileUploadForm()
    
    return render(request, 'analyzer/upload.html', {'form': form})


def file_detail(request, pk):
    """Show details of an uploaded .aia file"""
    aia_file = get_object_or_404(AiaFile, pk=pk)
    
    context = {
        'aia_file': aia_file,
        'images': aia_file.images.all(),
        'evaluation': getattr(aia_file, 'evaluation', None),
    }
    
    return render(request, 'analyzer/file_detail.html', context)


def analyze_file(request, pk):
    """Trigger analysis of an .aia file"""
    if request.method == 'POST':
        aia_file = get_object_or_404(AiaFile, pk=pk)
        
        # Verifica se é uma reanálise
        is_reanalysis = aia_file.is_analyzed
        
        try:
            # Perform analysis
            analyze_aia_file(aia_file)
            
            if is_reanalysis:
                messages.success(request, '🔄 Reanálise concluída com sucesso! Os scores foram atualizados com o novo sistema de pontuação granular.')
            else:
                messages.success(request, '✅ Análise concluída com sucesso!')
                
        except Exception as e:
            if is_reanalysis:
                messages.error(request, f'❌ Erro durante a reanálise: {str(e)}')
            else:
                messages.error(request, f'❌ Erro durante a análise: {str(e)}')
        
        return redirect('file_detail', pk=pk)
    
    return redirect('file_list')


def analysis_results(request, pk):
    """Show detailed analysis results"""
    aia_file = get_object_or_404(AiaFile, pk=pk)
    
    if not aia_file.is_analyzed:
        messages.warning(request, 'Este arquivo ainda não foi analisado.')
        return redirect('file_detail', pk=pk)
    
    evaluation = get_object_or_404(UsabilityEvaluation, aia_file=aia_file)
    images = aia_file.images.all()
    
    # Categorize images by quality
    high_quality_images = images.filter(quality_rating__in=['high', 'excellent'])
    medium_quality_images = images.filter(quality_rating='medium')
    low_quality_images = images.filter(quality_rating='low')
    
    # Group by asset type
    icons = images.filter(asset_type='icon')
    backgrounds = images.filter(asset_type='background')
    buttons = images.filter(asset_type='button')
    other_images = images.filter(asset_type__in=['image', 'other'])
    
    context = {
        'aia_file': aia_file,
        'evaluation': evaluation,
        'images': images,
        'high_quality_images': high_quality_images,
        'medium_quality_images': medium_quality_images,
        'low_quality_images': low_quality_images,
        'icons': icons,
        'backgrounds': backgrounds,
        'buttons': buttons,
        'other_images': other_images,
    }
    
    return render(request, 'analyzer/analysis_results.html', context)


def image_detail(request, pk):
    """Show detailed information about a specific image"""
    image = get_object_or_404(ImageAsset, pk=pk)
    
    context = {
        'image': image,
        'aia_file': image.aia_file,
    }
    
    return render(request, 'analyzer/image_detail.html', context)


def dashboard(request):
    """Main dashboard with statistics"""
    total_files = AiaFile.objects.count()
    analyzed_files = AiaFile.objects.filter(is_analyzed=True).count()
    total_images = ImageAsset.objects.count()
    
    recent_files = AiaFile.objects.order_by('-uploaded_at')[:5]
    # Ordenar análises recentes pelo score geral em ordem decrescente (maior score primeiro)
    recent_analyses = UsabilityEvaluation.objects.order_by('-overall_usability_score', '-evaluated_at')[:5]
    
    context = {
        'total_files': total_files,
        'analyzed_files': analyzed_files,
        'total_images': total_images,
        'recent_files': recent_files,
        'recent_analyses': recent_analyses,
    }
    
    return render(request, 'analyzer/dashboard.html', context)


def material_design_analysis(request, image_id):
    """Analyze an icon against Material Design guidelines"""
    image = get_object_or_404(ImageAsset, id=image_id)
    
    if image.asset_type != 'icon':
        messages.error(request, 'Esta análise é apenas para ícones.')
        return redirect('image_detail', image_id=image_id)
    
    # Perform Material Design analysis
    material_analysis = analyze_icon_against_material_design(image)
    similar_icons = find_similar_material_icon(image)
    
    context = {
        'image': image,
        'material_analysis': material_analysis,
        'similar_icons': similar_icons,
    }
    
    return render(request, 'analyzer/material_design_analysis.html', context)


def api_material_icons_search(request):
    """API endpoint for searching Material Design icons"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'icons': []})
    
    # This would implement search in the Material Icons database
    # For now, return empty results
    return JsonResponse({
        'icons': [],
        'query': query,
        'message': 'Material Icons search will be implemented when icons are loaded'
    })


def print_analysis(request, pk):
    """Generate printable analysis report"""
    aia_file = get_object_or_404(AiaFile, pk=pk)
    
    if not aia_file.is_analyzed:
        messages.warning(request, 'Este arquivo ainda não foi analisado.')
        return redirect('file_detail', pk=pk)
    
    evaluation = get_object_or_404(UsabilityEvaluation, aia_file=aia_file)
    images = aia_file.images.all()
    
    # Contadores por qualidade
    high_quality_count = images.filter(quality_rating__in=['high', 'excellent']).count()
    medium_quality_count = images.filter(quality_rating='medium').count()
    low_quality_count = images.filter(quality_rating='low').count()
    
    # Contadores por tipo
    total_images = images.count()
    total_icons = images.filter(asset_type='icon').count()
    
    # Usar as recomendações detalhadas do sistema
    detailed_recommendations = evaluation.recommendations if evaluation.recommendations else ""
    
    # Se não há recomendações salvas, gerar recomendações básicas
    if not detailed_recommendations:
        recommendations = []
        
        if evaluation.image_quality_score < 70:
            recommendations.append("Considere otimizar as imagens para melhor qualidade. Use pelo menos 640x480px para garantir qualidade visual em diferentes dispositivos.")
        
        if low_quality_count > 0:
            recommendations.append(f"Substitua as {low_quality_count} imagem(ns) de baixa qualidade por versões com maior resolução e melhor compressão.")
        
        if evaluation.overall_usability_score < 60:
            recommendations.append("O score geral pode ser melhorado. Foque nos assets com pontuação mais baixa para maior impacto.")
        
        if total_icons == 0:
            recommendations.append("Considere adicionar ícones para melhorar a experiência do usuário e facilitar a navegação.")
        
        if evaluation.image_quality_score == 100 and evaluation.overall_usability_score > 80:
            recommendations.append("Excelente trabalho! Seu projeto apresenta alta qualidade de usabilidade.")
        
        # Adicionar recomendações específicas baseadas em proporções
        irregular_proportions = 0
        for image in images:
            if image.aspect_ratio < 0.8 or image.aspect_ratio > 1.25:
                irregular_proportions += 1
        
        if irregular_proportions > 0:
            recommendations.append(f"Ajuste as proporções de {irregular_proportions} imagem(ns) para melhor adaptação em dispositivos móveis. Prefira proporções como 16:9, 4:3 ou 1:1.")
        
        detailed_recommendations = '\n'.join([f"• {rec}" for rec in recommendations])
    
    context = {
        'aia_file': aia_file,
        'evaluation': evaluation,
        'images': images,
        'total_images': total_images,
        'total_icons': total_icons,
        'high_quality_count': high_quality_count,
        'medium_quality_count': medium_quality_count,
        'low_quality_count': low_quality_count,
        'detailed_recommendations': detailed_recommendations,
    }
    
    return render(request, 'analyzer/print_analysis.html', context)
