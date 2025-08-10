from django import forms
from .models import AiaFile


class AiaFileUploadForm(forms.ModelForm):
    """Form for uploading .aia files"""
    
    class Meta:
        model = AiaFile
        fields = ['name', 'file']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do projeto (será preenchido automaticamente se deixado em branco)'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.aia'
            })
        }
        labels = {
            'name': 'Nome do Projeto',
            'file': 'Arquivo .aia'
        }
    
    def clean_file(self):
        """Validate uploaded file"""
        file = self.cleaned_data.get('file')
        
        if file:
            # Check file extension
            if not file.name.endswith('.aia'):
                raise forms.ValidationError('Por favor, envie apenas arquivos com extensão .aia')
            
            # Check file size (50MB limit)
            if file.size > 50 * 1024 * 1024:
                raise forms.ValidationError('O arquivo é muito grande. Tamanho máximo: 50MB')
        
        return file
    
    def clean_name(self):
        """Auto-generate name from filename if not provided"""
        name = self.cleaned_data.get('name')
        file = self.cleaned_data.get('file')
        
        if not name and file:
            # Extract name from filename, removing .aia extension
            name = file.name.replace('.aia', '').replace('_', ' ').replace('-', ' ').title()
        
        return name or 'Projeto sem nome'
