# Analisador de Apps .aia

Uma aplicação Django para upload e análise de usabilidade de arquivos .aia do MIT App Inventor, com foco especial na avaliação da qualidade de imagens e ícones.

## Funcionalidades

### 📁 Upload de Arquivos
- Upload de arquivos .aia (projetos do MIT App Inventor)
- Validação automática de formato e tamanho
- Preenchimento automático do nome do projeto

### 🔍 Análise Automática
- Extração automática de imagens e ícones dos arquivos .aia
- Análise de qualidade baseada em múltricos critérios:
  - Resolução e dimensões
  - Tamanho do arquivo e otimização
  - Proporções adequadas para dispositivos móveis
  - Classificação por tipo (ícone, fundo, botão, etc.)

### 📊 Avaliação de Usabilidade
- Score geral de usabilidade (0-100%)
- Score específico para qualidade de imagens
- Score específico para qualidade de ícones
- Detecção automática de problemas comuns
- Recomendações personalizadas para melhorias

### 🎯 Interface Intuitiva
- Dashboard com estatísticas gerais
- Visualização detalhada de cada arquivo
- Galeria de imagens extraídas
- Análise visual por categorias de qualidade

## Tecnologias Utilizadas

- **Backend**: Django 5.2.5
- **Frontend**: Bootstrap 5.1.3 + Bootstrap Icons
- **Processamento de Imagens**: Pillow
- **Banco de Dados**: SQLite (padrão, pode ser alterado)
- **Manipulação de Arquivos**: zipfile (nativo do Python)

## Estrutura do Projeto

```
aia_analyzer/
├── analyzer/                 # App principal
│   ├── models.py            # Modelos (AiaFile, ImageAsset, UsabilityEvaluation)
│   ├── views.py             # Views para upload, análise e visualização
│   ├── forms.py             # Formulários de upload
│   ├── utils.py             # Funções de análise e extração
│   ├── admin.py             # Interface administrativa
│   └── templates/           # Templates HTML
├── media/                   # Arquivos de upload (criado automaticamente)
├── static/                  # Arquivos estáticos
└── manage.py               # Script de gerenciamento Django
```

## Como os Arquivos .aia são Processados

1. **Upload**: O arquivo .aia é armazenado no sistema
2. **Extração**: O arquivo (que é um ZIP) é extraído temporariamente
3. **Identificação**: Imagens são identificadas por extensão (.png, .jpg, etc.)
4. **Análise**: Cada imagem é analisada para:
   - Dimensões e resolução
   - Tamanho do arquivo
   - Tipo de asset (ícone, fundo, botão)
   - Qualidade geral
5. **Avaliação**: Métricas de usabilidade são calculadas
6. **Recomendações**: Sugestões específicas são geradas

## Critérios de Avaliação

### Qualidade das Imagens
- **Resolução**: Mínimo 640x480 para adequação
- **Tamanho do arquivo**: Entre 1-4 bytes por pixel (otimizado)
- **Proporção**: Adequação para dispositivos móveis (16:9, 4:3, 1:1, etc.)

### Classificação de Assets
- **Ícones**: Pequenos e quadrados (≤128x128)
- **Fundos**: Grandes (≥800px ou ≥600px)
- **Botões**: Retangulares pequenos
- **Outros**: Imagens gerais

### Scores de Qualidade
- **Excelente**: 80-100% (verde)
- **Alta**: 65-79% (azul)
- **Média**: 40-64% (amarelo)
- **Baixa**: 0-39% (vermelho)

## Instalação e Execução

### Pré-requisitos
- Python 3.8+
- pip

### Instalação
1. Clone ou baixe o projeto
2. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   ```
3. Ative o ambiente virtual:
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```
4. Instale as dependências:
   ```bash
   pip install django pillow zipfile-deflate64 python-magic-bin
   ```
5. Execute as migrações:
   ```bash
   python manage.py migrate
   ```
6. (Opcional) Crie um superusuário:
   ```bash
   python manage.py createsuperuser
   ```
7. Execute o servidor:
   ```bash
   python manage.py runserver
   ```

### Acesso
- Aplicação: http://localhost:8000
- Admin: http://localhost:8000/admin (se criou superusuário)

## Uso

1. **Upload**: Acesse a página de upload e envie um arquivo .aia
2. **Análise**: Clique em "Analisar Arquivo" na página de detalhes
3. **Resultados**: Visualize os resultados da análise e recomendações
4. **Dashboard**: Acompanhe estatísticas gerais no dashboard

## Contribuição

Este projeto foi desenvolvido como parte de um mestrado na UFSC (2024-2026) para pesquisa em usabilidade de aplicativos móveis criados com App Inventor.

## Estrutura de Dados

### AiaFile
- Informações do arquivo .aia enviado
- Status da análise
- Contadores de imagens e ícones

### ImageAsset
- Dados de cada imagem extraída
- Propriedades técnicas (dimensões, formato, tamanho)
- Métricas de qualidade e usabilidade

### UsabilityEvaluation
- Scores gerais e específicos
- Contadores de problemas
- Recomendações personalizadas
