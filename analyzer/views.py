from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView
from django.core.files.storage import default_storage
from django.conf import settings
from .models import AiaFile, ImageAsset, UsabilityEvaluation
from .forms import AiaFileUploadForm
from .utils import analyze_aia_file
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
        
        try:
            # Perform analysis
            analyze_aia_file(aia_file)
            messages.success(request, 'Análise concluída com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro durante a análise: {str(e)}')
        
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
    recent_analyses = UsabilityEvaluation.objects.order_by('-evaluated_at')[:5]
    
    context = {
        'total_files': total_files,
        'analyzed_files': analyzed_files,
        'total_images': total_images,
        'recent_files': recent_files,
        'recent_analyses': recent_analyses,
    }
    
    return render(request, 'analyzer/dashboard.html', context)
