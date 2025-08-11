# main.py - Configuração principal para análise de ícones Material Design

import os
from django.conf import settings

# Caminho para os ícones do Material Design
PATH_TO_MATERIAL_ICONS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 
    'source', 
    'src'
)

# Configurações para análise de ícones
ICON_ANALYSIS_CONFIG = {
    'supported_formats': ['.svg'],  # Material Design icons são em SVG
    'similarity_threshold': 0.8,    # Threshold para considerar ícones similares
    'max_icon_size': 512,          # Tamanho máximo recomendado para ícones
    'min_icon_size': 16,           # Tamanho mínimo recomendado para ícones
}

# Mapeamento de estilos de ícones Material Design
MATERIAL_ICON_STYLES = {
    'materialicons': 'filled',
    'materialiconsoutlined': 'outlined', 
    'materialiconsround': 'round',
    'materialiconssharp': 'sharp',
    'materialiconstwotone': 'twotone'
}

if __name__ == "__main__":
    print(f"Material Design Icons Path: {PATH_TO_MATERIAL_ICONS}")
    print(f"Path exists: {os.path.exists(PATH_TO_MATERIAL_ICONS)}")
