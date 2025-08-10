from django.contrib import admin
from .models import AiaFile, ImageAsset, UsabilityEvaluation


@admin.register(AiaFile)
class AiaFileAdmin(admin.ModelAdmin):
    list_display = ['name', 'uploaded_at', 'uploaded_by', 'is_analyzed', 'total_images', 'total_icons']
    list_filter = ['is_analyzed', 'uploaded_at']
    search_fields = ['name']
    readonly_fields = ['uploaded_at', 'analysis_completed_at', 'total_images', 'total_icons']


@admin.register(ImageAsset)
class ImageAssetAdmin(admin.ModelAdmin):
    list_display = ['name', 'aia_file', 'asset_type', 'quality_rating', 'width', 'height', 'file_size']
    list_filter = ['asset_type', 'quality_rating', 'format']
    search_fields = ['name', 'aia_file__name']
    readonly_fields = ['created_at']


@admin.register(UsabilityEvaluation)
class UsabilityEvaluationAdmin(admin.ModelAdmin):
    list_display = ['aia_file', 'overall_usability_score', 'image_quality_score', 'icon_quality_score', 'evaluated_at']
    readonly_fields = ['evaluated_at']
