"""
Integração com Google Gemini AI para Análise Avançada de Usabilidade - Versão 2.0
==================================================================================

MELHORIAS BASEADAS EM PESQUISA ACADÊMICA E DIRETRIZES INTERNACIONAIS:

📚 FUNDAMENTAÇÃO ACADÊMICA:
- Baseado nos trabalhos da pasta "trabalhos" sobre avaliação de design no App Inventor
- Incorpora heurísticas de Nielsen adaptadas para contexto educacional
- Considera o App Inventor como ferramenta pedagógica

🔍 WCAG 2.1 AA COMPLIANCE:
- Critérios específicos de contraste (4.5:1 para texto normal)
- Tamanhos mínimos de toque (44x44px)
- Verificação de independência de cor
- Análise de compatibilidade com tecnologias assistivas

🎨 MATERIAL DESIGN 3:
- Sistema de cores moderno e acessível
- Tipografia hierárquica clara
- Componentes com estados visuais definidos
- Elevação e sombras apropriadas

🎓 CONTEXTO EDUCACIONAL:
- Feedback construtivo e motivacional
- Explicações incluem fundamentação teórica
- Sugestões adaptadas para iniciantes
- Foco no aprendizado de conceitos de IHC

Características:
- Análise de imagens com Gemini Vision + WCAG 2.1 AA
- Geração de feedback contextual inteligente baseado em pesquisa
- Análise de padrões de design com fundamentação acadêmica
- Sugestões específicas baseadas em Material Design 3

Instalação:
pip install google-generativeai

Configuração:
1. Obtenha uma API key gratuita em: https://makersuite.google.com/app/apikey
2. Configure a variável de ambiente: GEMINI_API_KEY=sua_chave_aqui
3. Ou adicione no Django settings.py: GEMINI_API_KEY = 'sua_chave_aqui'
"""

import os
import base64
import json
import logging
from typing import Dict, List, Optional, Tuple
from PIL import Image
import io

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Google Gemini não disponível. Instale: pip install google-generativeai")

from django.conf import settings


class GeminiAnalyzer:
    """
    Analisador inteligente usando Google Gemini AI
    """
    
    def __init__(self):
        self.model = None
        self.vision_model = None
        self.api_key = None
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Inicializa a conexão com Gemini AI"""
        if not GEMINI_AVAILABLE:
            return
        
        # Buscar API key (Google prefere GOOGLE_API_KEY)
        self.api_key = (
            os.getenv('GOOGLE_API_KEY') or 
            os.getenv('GEMINI_API_KEY') or 
            getattr(settings, 'GOOGLE_API_KEY', None) or
            getattr(settings, 'GEMINI_API_KEY', None)
        )
        
        if not self.api_key:
            print("⚠️ API key não configurada. Configure GOOGLE_API_KEY ou GEMINI_API_KEY.")
            return
        
        try:
            genai.configure(api_key=self.api_key)
            
            # Modelo para texto (usar modelo mais recente e estável)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Modelo para visão (tentar modelo multimodal)
            try:
                self.vision_model = genai.GenerativeModel('gemini-1.5-pro')
            except:
                # Fallback para modelo principal se visão não disponível
                self.vision_model = self.model
            
            print("✅ Gemini AI inicializado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar Gemini: {e}")
            self.model = None
            self.vision_model = None
    
    def is_available(self) -> bool:
        """Verifica se Gemini está disponível e configurado"""
        return self.model is not None and self.vision_model is not None
    
    def _clean_json_response(self, text: str) -> str:
        """Limpa resposta do Gemini removendo markdown formatting"""
        text = text.strip()
        
        # Remover marcações de código markdown se existirem
        if text.startswith('```json'):
            text = text[7:]  # Remove ```json
        if text.startswith('```'):
            text = text[3:]   # Remove ```
        if text.endswith('```'):
            text = text[:-3]  # Remove ``` no final
        
        return text.strip()
    
    def analyze_app_context_with_ai(self, project_name: str, images: List, aia_file) -> Dict:
        """
        Analisa o contexto da aplicação usando IA generativa
        Baseado em trabalhos acadêmicos e contexto educacional do App Inventor
        """
        if not self.is_available():
            return self._fallback_context_analysis(project_name, images)
        
        try:
            # Preparar tipos de arquivo
            file_types = list(set(img.name.split('.')[-1] for img in images[:10] if '.' in img.name))
            
            # Prompt melhorado baseado em pesquisa acadêmica
            prompt = f"""
            Você é um especialista em Interação Humano-Computador (IHC) e Design de Interfaces 
            com foco no contexto educacional do MIT App Inventor.
            
            CONTEXTO EDUCACIONAL:
            O App Inventor é uma ferramenta pedagógica visual que permite ensinar programação 
            e design de interfaces através de blocos visuais. O público inclui estudantes 
            iniciantes, professores e desenvolvedores em formação.
            
            PROJETO PARA ANÁLISE:
            - Nome: {project_name}
            - Total de imagens: {len(images)}
            - Tipos de arquivo: {', '.join(file_types)}
            - Arquivos: {', '.join([img.name for img in images[:15]])}
            
            CRITÉRIOS DE AVALIAÇÃO (baseados em Nielsen e trabalhos acadêmicos):
            1. CATEGORIA DE APLICAÇÃO:
               - Educacional: Apps para ensino/aprendizagem
               - Jogos: Jogos educativos ou entretenimento
               - Utilitários: Ferramentas e utilidades
               - Social: Comunicação e interação social
               - Produtividade: Produtividade e organização
            
            2. PÚBLICO-ALVO EDUCACIONAL:
               - Ensino Fundamental (6-11 anos): Interface muito simples, cores vibrantes
               - Ensino Médio Inicial (12-14 anos): Elementos visuais atraentes, navegação clara
               - Ensino Médio Final (15-18 anos): Interface mais sofisticada, funcionalidades avançadas
               - Adultos Aprendizes (18+ anos): Foco em usabilidade e eficiência
               - Professores: Ferramentas educacionais para sala de aula
            
            3. COMPLEXIDADE TÉCNICA:
               - Iniciante: Poucos elementos, interface simples
               - Intermediário: Navegação estruturada, múltiplas telas
               - Avançado: Funcionalidades complexas, integração com sensores/APIs
               - Especialista: Arquitetura sofisticada, otimizações avançadas
            
            4. ESTILO VISUAL (Material Design 3 + Contexto Educacional):
               - Amigável Educacional: Cores suaves, elementos lúdicos apropriados
               - Profissional: Design limpo, cores neutras, tipografia clara
               - Divertido: Cores vibrantes, elementos divertidos, animações
               - Minimalista: Interface clean, foco no conteúdo
               - Criativo: Design artístico, elementos visuais únicos
            
            DIRETRIZES DE ANÁLISE:
            - Considere que o App Inventor é usado em contexto educacional
            - Avalie se o design facilita o aprendizado de conceitos de IHC
            - Observe se há elementos que demonstram aplicação de boas práticas
            - Considere a progressão pedagógica do usuário/desenvolvedor
            
            Responda APENAS em formato JSON válido:
            {{
                "category": "categoria_detectada",
                "target_audience": "publico_alvo_educacional", 
                "complexity_level": "nivel_complexidade",
                "visual_style": "estilo_visual",
                "confidence_score": 0.85,
                "educational_context": "como este app se relaciona com aprendizado",
                "pedagogical_level": "nível pedagógico observado",
                "reasoning": "justificativa baseada em princípios de IHC e contexto educacional"
            }}
            
            IMPORTANTE: Responda todos os campos com valores em PORTUGUÊS, seguindo estas opções:
            
            - category: "Educacional", "Jogos", "Utilitários", "Social", "Produtividade"
            - target_audience: "Ensino Fundamental", "Ensino Médio Inicial", "Ensino Médio Final", "Adultos Aprendizes", "Professores"
            - complexity_level: "Iniciante", "Intermediário", "Avançado", "Especialista"
            - visual_style: "Amigável Educacional", "Profissional", "Divertido", "Minimalista", "Criativo"
            """
            
            response = self.model.generate_content(prompt)
            text = self._clean_json_response(response.text)
            result = json.loads(text)
            
            return result
            
        except Exception as e:
            print(f"⚠️ Erro na análise contextual com Gemini: {e}")
            return self._fallback_context_analysis(project_name, images)
    
    def analyze_image_quality_with_ai(self, image_path: str, image_name: str) -> Dict:
        """
        Analisa qualidade de uma imagem específica usando Gemini Vision
        Baseado em WCAG 2.1 AA e Material Design 3
        """
        if not self.is_available():
            return {"score": 75, "issues": [], "suggestions": []}
        
        try:
            # Carregar e preparar imagem
            img = Image.open(image_path)
            
            # Redimensionar se muito grande (Gemini tem limite)
            if img.width > 1024 or img.height > 1024:
                img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            
            prompt = f"""
            Você é um especialista em Design Visual e Acessibilidade Digital, com conhecimento 
            profundo das diretrizes WCAG 2.1 AA e Material Design 3.
            
            IMAGEM PARA ANÁLISE: {image_name}
            
            CRITÉRIOS WCAG 2.1 AA:
            1. CONTRASTE:
               - Texto normal: mínimo 4.5:1
               - Texto grande (18pt+): mínimo 3:1
               - Elementos de interface: mínimo 3:1
            
            2. TAMANHOS MÍNIMOS:
               - Alvos de toque: 44x44 pixels CSS (Android) / 44x44 pontos (iOS)
               - Espaçamento entre elementos interativos: mínimo 8px
            
            3. IDENTIFICAÇÃO POR COR:
               - Informação não deve depender apenas de cor
               - Estados (erro, sucesso) devem ter indicadores visuais extras
            
            DIRETRIZES MATERIAL DESIGN 3:
            1. SISTEMA DE CORES:
               - Paleta coerente com roles definidos (primary, secondary, surface)
               - Suporte a temas claro/escuro
               - Cores semanticamente apropriadas
            
            2. TIPOGRAFIA:
               - Hierarquia clara (Display, Headline, Title, Body, Label)
               - Legibilidade em diferentes tamanhos de tela
               - Peso e espaçamento apropriados
            
            3. COMPONENTES:
               - Uso correto de elevation/sombras
               - Estados visuais claros (pressed, focused, disabled)
               - Consistência com padrões Material
            
            CONTEXTO EDUCACIONAL APP INVENTOR:
            - Interface deve ensinar boas práticas visuais
            - Elementos devem ser reconhecíveis por estudantes
            - Cores e ícones apropriados para contexto educacional
            
            Responda em JSON válido:
            {{
                "overall_score": 85,
                "wcag_compliance": {{
                    "contrast_score": 90,
                    "touch_targets": 85,
                    "color_independence": 80,
                    "overall_accessibility": 85
                }},
                "material_design": {{
                    "color_system": 80,
                    "typography": 85,
                    "components": 75,
                    "elevation": 80,
                    "overall_md3": 80
                }},
                "educational_appropriateness": {{
                    "age_appropriate": 90,
                    "clarity": 85,
                    "learning_support": 80,
                    "overall_educational": 85
                }},
                "technical_quality": {{
                    "resolution": 90,
                    "compression": 85,
                    "format_appropriateness": 80,
                    "overall_technical": 85
                }},
                "critical_issues": ["problemas que violam WCAG 2.1 AA"],
                "material_design_issues": ["problemas com MD3"],
                "educational_concerns": ["questões pedagógicas"],
                "strengths": ["pontos fortes identificados"],
                "priority_fixes": ["correções prioritárias com justificativa"],
                "suggestions": ["melhorias específicas baseadas nas diretrizes"]
            }}
            """
            
            response = self.vision_model.generate_content([prompt, img])
            text = self._clean_json_response(response.text)
            result = json.loads(text)
            
            return result
            
        except Exception as e:
            print(f"⚠️ Erro na análise de imagem com Gemini: {e}")
            return {"score": 75, "issues": [], "suggestions": []}
    
    def generate_intelligent_recommendations(self, context: Dict, scores: Dict, images: List, detailed_analysis: List) -> List[str]:
        """
        Gera recomendações inteligentes usando IA generativa
        Baseado em fundamentação acadêmica e pedagógica
        """
        if not self.is_available():
            return self._fallback_recommendations(context, scores, images)
        
        try:
            # Preparar dados para análise
            image_summary = self._prepare_image_summary(images, detailed_analysis)
            
            prompt = f"""
            Você é um consultor especializado em UX/UI com PhD em Interação Humano-Computador 
            e experiência em Design Educacional. Seu papel é fornecer feedback construtivo 
            para estudantes e educadores usando o MIT App Inventor.
            
            PRINCÍPIOS PEDAGÓGICOS:
            - Feedback deve ser motivacional e construtivo
            - Explicações devem incluir o "porquê" das recomendações
            - Sugestões devem ser implementáveis por iniciantes
            - Foco no aprendizado progressivo de conceitos de IHC
            
            CONTEXTO DA APLICAÇÃO:
            - Categoria: {context.get('category', 'unknown')}
            - Público-alvo: {context.get('target_audience', 'unknown')}
            - Nível de complexidade: {context.get('complexity_level', 'unknown')}
            - Contexto educacional: {context.get('educational_context', 'unknown')}
            - Score geral: {scores.get('overall_score', 0):.1f}/100
            
            ANÁLISE DETALHADA DAS IMAGENS:
            {image_summary}
            
            FUNDAMENTAÇÃO TEÓRICA PARA RECOMENDAÇÕES:
            
            1. HEURÍSTICAS DE NIELSEN (adaptadas para contexto educacional):
               - Visibilidade do status do sistema
               - Correspondência entre sistema e mundo real
               - Controle e liberdade do usuário
               - Consistência e padrões
               - Prevenção de erros
               - Reconhecimento em vez de memorização
               - Flexibilidade e eficiência de uso
               - Design estético e minimalista
               - Ajuda aos usuários no reconhecimento e recuperação de erros
               - Ajuda e documentação
            
            2. WCAG 2.1 AA (Critérios de Sucesso):
               - Perceptível: Texto alternativo, contraste, redimensionamento
               - Operável: Navegação por teclado, tempo suficiente, sem convulsões
               - Compreensível: Legível, previsível, assistência de entrada
               - Robusto: Compatível com tecnologias assistivas
            
            3. MATERIAL DESIGN 3 (Princípios):
               - Personal: Adaptável e expressivo
               - Accessible: Inclusivo e usável
               - Expressive: Design belo e intuitivo
            
            4. CONTEXTO EDUCACIONAL:
               - Scaffolding: Suporte gradual para aprendizagem
               - Feedback imediato e específico
               - Progressão de complexidade apropriada
               - Transferência de aprendizagem para outros contextos
            
            FORMATO DAS RECOMENDAÇÕES:
            
            Para cada recomendação, formate como:
            - 🎯 [PRIORIDADE] OBJETIVO - JUSTIFICATIVA - AÇÃO PRÁTICA
            
            PRIORIZAÇÃO:
            1. 🔴 CRÍTICO: Violações de acessibilidade ou usabilidade graves
            2. 🟡 IMPORTANTE: Melhorias significativas na experiência
            3. 🟢 OPCIONAL: Refinamentos e otimizações
            
            Gere 6-8 recomendações priorizadas, focando no crescimento educacional
            do usuário e na aplicação prática de conceitos de IHC.
            
            Mantenha tom encorajador e educativo, adequado para ambiente de aprendizagem.
            """
            
            response = self.model.generate_content(prompt)
            
            # Processar resposta
            recommendations = self._process_ai_recommendations(response.text)
            
            return recommendations
            
        except Exception as e:
            print(f"⚠️ Erro na geração de recomendações com Gemini: {e}")
            return self._fallback_recommendations(context, scores, images)
    
    def analyze_accessibility_with_ai(self, images: List) -> Dict:
        """
        Análise específica de acessibilidade usando IA
        Baseado em WCAG 2.1 AA e contexto educacional inclusivo
        """
        if not self.is_available():
            return {"score": 80, "issues": [], "recommendations": []}
        
        try:
            # Preparar dados sobre imagens
            image_info = []
            for img in images[:10]:  # Limitar para não sobrecarregar
                info = {
                    "name": img.name,
                    "type": getattr(img, 'asset_type', 'unknown'),
                    "dimensions": f"{getattr(img, 'width', 'N/A')}x{getattr(img, 'height', 'N/A')}",
                    "size": f"{getattr(img, 'file_size', 0)/1024:.1f}KB"
                }
                image_info.append(info)
            
            prompt = f"""
            Você é um especialista certificado em Acessibilidade Digital (WCAG 2.1 AA) 
            e Tecnologia Assistiva, com experiência em avaliação de aplicativos móveis 
            educacionais.
            
            CONTEXTO EDUCACIONAL:
            O MIT App Inventor é usado em ambientes educacionais diversos, incluindo 
            estudantes com deficiências. É crucial que os apps criados sejam acessíveis 
            e que o processo ensine desenvolvimento inclusivo.
            
            ASSETS PARA ANÁLISE:
            {json.dumps(image_info, indent=2)}
            
            CRITÉRIOS WCAG 2.1 AA (Nível AA):
            
            1. PERCEPTÍVEL:
               1.1.1 Conteúdo Não-textual: Imagens devem ter texto alternativo
               1.3.3 Características Sensoriais: Não depender apenas de cor/forma
               1.4.3 Contraste (Mínimo): 4.5:1 para texto normal, 3:1 para texto grande
               1.4.4 Redimensionar Texto: Até 200% sem perda de funcionalidade
               1.4.10 Reflow: Conteúdo deve se adaptar a 320px CSS
               1.4.11 Contraste Não-textual: 3:1 para elementos de interface
            
            2. OPERÁVEL:
               2.1.1 Teclado: Toda funcionalidade acessível via teclado
               2.1.2 Sem Armadilha do Teclado: Navegação deve ser fluida
               2.4.3 Ordem do Foco: Sequência lógica e significativa
               2.4.7 Foco Visível: Indicação clara do elemento focado
               2.5.5 Tamanho do Alvo: Mínimo 44x44 pixels CSS
            
            3. COMPREENSÍVEL:
               3.1.1 Idioma da Página: Idioma deve ser identificável
               3.2.1 Ao Receber Foco: Não causar mudanças inesperadas
               3.2.2 Ao Inserir Dados: Mudanças devem ser previsíveis
               3.3.2 Rótulos ou Instruções: Campos devem ter rótulos claros
            
            4. ROBUSTO:
               4.1.1 Análise: Código deve ser válido
               4.1.2 Nome, Função, Valor: Elementos devem ser interpretáveis
            
            VERIFICAÇÕES ESPECÍFICAS PARA APPS MÓVEIS:
            - Tamanhos de toque adequados (44x44px mínimo)
            - Contraste suficiente em diferentes condições de luz
            - Compatibilidade com leitores de tela (TalkBack/VoiceOver)
            - Navegação sequencial lógica
            - Feedback tátil e auditivo quando apropriado
            - Suporte a gestos de acessibilidade
            - Tempo adequado para interações
            
            CONTEXTO APP INVENTOR:
            - Elementos visuais devem ser exportáveis com metadados acessíveis
            - Cores devem seguir paletas com contraste adequado
            - Ícones devem ser semanticamente claros
            - Interface deve ensinar princípios de design inclusivo
            
            Responda em JSON:
            {{
                "wcag_compliance_score": 85,
                "compliance_by_principle": {{
                    "perceivable": 80,
                    "operable": 85,
                    "understandable": 90,
                    "robust": 75
                }},
                "critical_violations": [
                    {{
                        "criterion": "1.4.3 Contraste (Mínimo)",
                        "description": "Texto com contraste insuficiente",
                        "impact": "Alto - impede leitura por pessoas com baixa visão",
                        "fix": "Aumentar contraste para pelo menos 4.5:1"
                    }}
                ],
                "warnings": [
                    {{
                        "criterion": "2.5.5 Tamanho do Alvo", 
                        "description": "Botões muito pequenos",
                        "impact": "Médio - dificulta uso por pessoas com dificuldades motoras",
                        "fix": "Aumentar tamanho mínimo para 44x44px"
                    }}
                ],
                "strengths": ["Aspectos que seguem bem as diretrizes"],
                "educational_opportunities": ["Como usar isso para ensinar acessibilidade"],
                "priority_fixes": ["Correções mais importantes"],
                "improvement_suggestions": ["Melhorias específicas com base WCAG"],
                "assistive_technology_compatibility": "Análise de compatibilidade",
                "inclusive_design_score": 80
            }}
            """
            
            response = self.model.generate_content(prompt)
            text = self._clean_json_response(response.text)
            result = json.loads(text)
            
            return result
            
        except Exception as e:
            print(f"⚠️ Erro na análise de acessibilidade com Gemini: {e}")
            return {"score": 80, "issues": [], "recommendations": []}
    
    def generate_priority_matrix(self, context: Dict, scores: Dict, issues: List) -> Dict:
        """
        Gera matriz de prioridades usando IA
        """
        if not self.is_available():
            return self._basic_priority_matrix(issues)
        
        try:
            prompt = f"""
            Como consultor de UX, crie uma matriz de prioridades para melhorias:
            
            CONTEXTO: {context.get('category', 'app')} para {context.get('target_audience', 'usuários')}
            SCORE ATUAL: {scores.get('overall_score', 0):.1f}/100
            
            PROBLEMAS IDENTIFICADOS:
            {chr(10).join(f"- {issue}" for issue in issues[:15])}
            
            Organize em 4 níveis de prioridade considerando:
            - Impacto na experiência do usuário
            - Facilidade de implementação  
            - Relevância para o público-alvo
            - Conformidade com padrões de acessibilidade
            
            Responda em JSON:
            {{
                "critical": ["melhorias críticas urgentes"],
                "high": ["melhorias de alto impacto"],
                "medium": ["otimizações importantes"],
                "low": ["polimentos e refinamentos"]
            }}
            """
            
            response = self.model.generate_content(prompt)
            text = self._clean_json_response(response.text)
            result = json.loads(text)
            
            return result
            
        except Exception as e:
            print(f"⚠️ Erro na matriz de prioridades com Gemini: {e}")
            return self._basic_priority_matrix(issues)
    
    def _prepare_image_summary(self, images: List, detailed_analysis: List) -> str:
        """Prepara resumo das imagens para análise"""
        summary = []
        
        for i, img in enumerate(images[:10]):
            analysis = detailed_analysis[i] if i < len(detailed_analysis) else {}
            summary.append(f"- {img.name}: {img.width}x{img.height}, {img.file_size/1024:.1f}KB, score: {analysis.get('overall_score', 'N/A')}")
        
        return "\n".join(summary)
    
    def _process_ai_recommendations(self, ai_response: str) -> List[str]:
        """Processa resposta da IA para extrair recomendações"""
        recommendations = []
        
        # Dividir por linhas e filtrar
        lines = ai_response.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                # Remover marcadores
                clean_line = line.lstrip('-•* ').strip()
                if clean_line:
                    recommendations.append(clean_line)
        
        # Se não encontrou formato de lista, dividir por frases
        if not recommendations:
            sentences = ai_response.split('.')
            for sentence in sentences[:8]:
                sentence = sentence.strip()
                if sentence and len(sentence) > 20:
                    recommendations.append(sentence + '.')
        
        return recommendations[:8]  # Limitar a 8 recomendações
    
    def _fallback_context_analysis(self, project_name: str, images: List) -> Dict:
        """Análise básica quando Gemini não está disponível"""
        # Análise simples baseada em palavras-chave
        name_lower = project_name.lower()
        
        # Calcular confiança baseada em evidências
        confidence_factors = []
        
        # Fator 1: Clareza do nome (0.0 a 0.4)
        specific_words = ['educativo', 'jogo', 'quiz', 'calculadora', 'agenda', 'chat', 'social', 'musica']
        generic_words = ['app', 'teste', 'projeto', 'exemplo', 'demo']
        
        name_clarity = 0.2  # Base
        if any(word in name_lower for word in specific_words):
            name_clarity += 0.2
        if any(word in name_lower for word in generic_words):
            name_clarity -= 0.1
        
        confidence_factors.append(min(0.4, max(0.0, name_clarity)))
        
        # Fator 2: Quantidade de imagens (0.0 a 0.3)
        image_count = len(images)
        if image_count >= 5:
            image_factor = 0.3
        elif image_count >= 3:
            image_factor = 0.2
        elif image_count >= 1:
            image_factor = 0.1
        else:
            image_factor = 0.0
        
        confidence_factors.append(image_factor)
        
        # Fator 3: Diversidade de tipos de arquivo (0.0 a 0.2)
        file_types = set()
        for img in images[:10]:
            if '.' in img.name:
                file_types.add(img.name.split('.')[-1].lower())
        
        type_diversity = min(0.2, len(file_types) * 0.05)
        confidence_factors.append(type_diversity)
        
        # Fator 4: Consistência temática (0.0 a 0.1)
        theme_consistency = 0.1 if image_count > 0 else 0.0
        confidence_factors.append(theme_consistency)
        
        # Calcular confiança total
        total_confidence = sum(confidence_factors)
        
        # Classificação baseada em palavras-chave
        if any(word in name_lower for word in ['game', 'jogo', 'play', 'puzzle', 'quiz']):
            category = 'Jogos'
            audience = 'Ensino Médio Inicial'
            total_confidence += 0.1  # Bonus por palavra-chave clara
        elif any(word in name_lower for word in ['school', 'edu', 'educativ', 'learn', 'ensino', 'aula']):
            category = 'Educacional'
            audience = 'Ensino Fundamental'
            total_confidence += 0.15  # Bonus maior por contexto educacional
        elif any(word in name_lower for word in ['calc', 'tool', 'util', 'converter', 'agenda']):
            category = 'Utilitários'
            audience = 'Adultos Aprendizes'
            total_confidence += 0.05
        elif any(word in name_lower for word in ['chat', 'social', 'rede', 'comunic']):
            category = 'Social'
            audience = 'Ensino Médio Final'
            total_confidence += 0.08
        else:
            category = 'Utilitários'
            audience = 'Adultos Aprendizes'
            total_confidence -= 0.1  # Penalidade por categoria indefinida
        
        # Garantir que confiança esteja entre 0.1 e 1.0
        final_confidence = min(1.0, max(0.1, total_confidence))
        
        return {
            "category": category,
            "target_audience": audience,
            "complexity_level": "Intermediário",
            "visual_style": "Profissional",
            "confidence_score": round(final_confidence, 2),
            "educational_context": "Ferramenta criada com App Inventor para fins educacionais",
            "pedagogical_level": "Nível intermediário de desenvolvimento",
            "reasoning": f"Análise baseada em: nome ({confidence_factors[0]:.2f}), imagens ({confidence_factors[1]:.2f}), diversidade ({confidence_factors[2]:.2f}), consistência ({confidence_factors[3]:.2f})"
        }
    
    def _fallback_recommendations(self, context: Dict, scores: Dict, images: List) -> List[str]:
        """Recomendações básicas quando Gemini não está disponível"""
        return [
            f"🎯 Detectado app {context.get('category', 'genérico')} - otimize para esse contexto específico",
            f"📊 Score atual: {scores.get('overall_score', 0):.1f}/100 - há bom espaço para melhorias",
            "🎨 Considere seguir diretrizes Material Design 3 para maior consistência visual",
            "♿ Verifique critérios de acessibilidade WCAG 2.1 AA e contraste de cores adequado",
            "💾 Otimize tamanho e formato das imagens para melhor performance do app",
            "🎓 Aproveite o contexto educacional do App Inventor para ensinar boas práticas de IHC"
        ]
    
    def _basic_priority_matrix(self, issues: List) -> Dict:
        """Matriz básica de prioridades"""
        return {
            "critical": issues[:2] if issues else [],
            "high": issues[2:5] if len(issues) > 2 else [],
            "medium": issues[5:8] if len(issues) > 5 else [],
            "low": issues[8:] if len(issues) > 8 else []
        }


# Função principal para integração com o sistema existente
def analyze_with_gemini_ai(aia_file, images: List, scores: Dict, project_name: str = "") -> Dict:
    """
    Função principal para análise completa com Gemini AI
    """
    analyzer = GeminiAnalyzer()
    
    if not analyzer.is_available():
        print("⚠️ Gemini AI não disponível. Usando análise básica.")
        return {
            "context": analyzer._fallback_context_analysis(project_name, images),
            "recommendations": analyzer._fallback_recommendations({}, scores, images),
            "ai_powered": False
        }
    
    # Análise contextual
    context = analyzer.analyze_app_context_with_ai(project_name, images, aia_file)
    
    # Análise detalhada de imagens (primeiras 5 para não sobrecarregar API)
    detailed_analysis = []
    for img in images[:5]:
        if hasattr(img, 'file') and img.file:
            try:
                analysis = analyzer.analyze_image_quality_with_ai(img.file.path, img.name)
                detailed_analysis.append(analysis)
            except:
                detailed_analysis.append({"score": 75, "issues": [], "suggestions": []})
    
    # Análise de acessibilidade
    accessibility = analyzer.analyze_accessibility_with_ai(images)
    
    # Gerar recomendações inteligentes
    recommendations = analyzer.generate_intelligent_recommendations(
        context, scores, images, detailed_analysis
    )
    
    # Coletar todos os problemas para matriz de prioridades
    all_issues = []
    for analysis in detailed_analysis:
        all_issues.extend(analysis.get('issues', []))
    all_issues.extend(accessibility.get('issues', []))
    
    # Matriz de prioridades
    priority_matrix = analyzer.generate_priority_matrix(context, scores, all_issues)
    
    return {
        "context": context,
        "recommendations": recommendations,
        "detailed_analysis": detailed_analysis,
        "accessibility": accessibility,
        "priority_matrix": priority_matrix,
        "ai_powered": True
    }


# Função para configuração rápida
def setup_gemini_api_key():
    """
    Guia para configurar a API key do Gemini
    """
    print("""
    🔑 CONFIGURAÇÃO DO GOOGLE GEMINI AI
    ===================================
    
    1. Acesse: https://makersuite.google.com/app/apikey
    2. Faça login com sua conta Google
    3. Clique em "Create API Key"
    4. Copie a chave gerada
    
    5. Configure no sistema:
    
    OPÇÃO A - Variável de ambiente (recomendado):
    export GEMINI_API_KEY=sua_chave_aqui
    
    OPÇÃO B - Django settings.py:
    GEMINI_API_KEY = 'sua_chave_aqui'
    
    OPÇÃO C - Arquivo .env:
    GEMINI_API_KEY=sua_chave_aqui
    
    💡 NÍVEL GRATUITO:
    - 60 requisições por minuto
    - 1000 requisições por dia
    - Suficiente para uso educacional e desenvolvimento
    
    ✅ Após configurar, reinicie o Django para aplicar as mudanças.
    """)


if __name__ == "__main__":
    setup_gemini_api_key()
