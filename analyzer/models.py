from django.db import models
from django.contrib.auth.models import User
import os


class AiaFile(models.Model):
    """Model for storing uploaded .aia files and their analysis results"""
    
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='aia_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Analysis results
    is_analyzed = models.BooleanField(default=False)
    total_images = models.IntegerField(default=0)
    total_icons = models.IntegerField(default=0)
    analysis_completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    @property
    def file_size(self):
        """Get file size in bytes"""
        if self.file:
            return self.file.size
        return 0
    
    @property
    def file_size_mb(self):
        """Get file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)


class ImageAsset(models.Model):
    """Model for storing individual image assets from .aia files"""
    
    QUALITY_CHOICES = [
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
        ('excellent', 'Excelente'),
    ]
    
    ASSET_TYPE_CHOICES = [
        ('image', 'Imagem'),
        ('icon', 'Ícone'),
        ('background', 'Fundo'),
        ('button', 'Botão'),
        ('other', 'Outro'),
    ]
    
    aia_file = models.ForeignKey(AiaFile, on_delete=models.CASCADE, related_name='images')
    name = models.CharField(max_length=255)
    original_path = models.CharField(max_length=500)  # Path within the .aia file
    extracted_file = models.ImageField(upload_to='extracted_images/')
    
    # Image properties
    width = models.IntegerField()
    height = models.IntegerField()
    file_size = models.IntegerField()  # in bytes
    format = models.CharField(max_length=10)  # PNG, JPG, etc.
    
    # Quality assessment
    quality_score = models.FloatField(null=True, blank=True)  # 0-100 scale
    quality_rating = models.CharField(max_length=10, choices=QUALITY_CHOICES, null=True, blank=True)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPE_CHOICES, default='image')
    
    # Usability metrics
    resolution_adequate = models.BooleanField(null=True, blank=True)
    aspect_ratio_appropriate = models.BooleanField(null=True, blank=True)
    file_size_optimized = models.BooleanField(null=True, blank=True)
    
    # Material Design Icon analysis
    material_icon_style = models.CharField(max_length=20, null=True, blank=True)  # filled, outlined, round, sharp, twotone
    is_material_icon = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.aia_file.name} - {self.name}"
    
    @property
    def aspect_ratio(self):
        """Calculate aspect ratio"""
        if self.height > 0:
            return round(self.width / self.height, 2)
        return 0
    
    @property
    def megapixels(self):
        """Calculate megapixels"""
        return round((self.width * self.height) / 1000000, 2)

    @property
    def bytes_per_pixel(self):
        if self.width > 0 and self.height > 0:
            return round(self.file_size / (self.width * self.height), 2)
        return 0


class UsabilityEvaluation(models.Model):
    """Model for storing usability evaluation results"""
    
    aia_file = models.OneToOneField(AiaFile, on_delete=models.CASCADE, related_name='evaluation')
    
    # Overall scores (0-100)
    image_quality_score = models.FloatField(default=0)
    icon_quality_score = models.FloatField(default=0)
    overall_usability_score = models.FloatField(default=0)
    
    # Detailed metrics
    high_quality_images_count = models.IntegerField(default=0)
    low_quality_images_count = models.IntegerField(default=0)
    oversized_images_count = models.IntegerField(default=0)
    undersized_images_count = models.IntegerField(default=0)
    
    # Recommendations
    recommendations = models.TextField(blank=True)
    
    # Evaluation metadata
    evaluated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Avaliação - {self.aia_file.name}"
    
    @property
    def total_issues(self):
        """Count total issues found"""
        return (self.low_quality_images_count + 
                self.oversized_images_count + 
                self.undersized_images_count)
