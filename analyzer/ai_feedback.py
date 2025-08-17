"""
Sistema de Feedback Inteligente com IA para Análise de Usabilidade
================================================================

Este módulo implementa análise contextual avançada e geração de feedback personalizado
usando técnicas de IA para melhorar significativamente a qualidade das recomendações.

Características:
- Análise contextual do tipo de aplicativo
- Feedback personalizado baseado no perfil da aplicação
- Sugestões específicas e acionáveis
- Comparações com benchmarks de qualidade
- Detecção de padrões e tendências

Autor: Sistema de Análise App Inventor
Data: 2025
"""

import json
import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import numpy as np


@dataclass
class AppContext:
    """Contexto da aplicação detectado pela IA"""
    category: str  # game, educational, utility, social, etc.
    target_audience: str  # kids, teens, adults, seniors, professional
    complexity_level: str  # simple, moderate, complex, advanced
    visual_style: str  # minimalist, playful, professional, artistic
    confidence_score: float  # 0-1


class AIFeedbackEngine:
    """
    Motor de IA para análise contextual e geração de feedback personalizado
    """
    
    def __init__(self):
        self.app_patterns = self._load_app_patterns()
        self.design_benchmarks = self._load_design_benchmarks()
        self.feedback_templates = self._load_feedback_templates()
    
    def _load_app_patterns(self) -> Dict:
        """Carrega padrões para detecção do tipo de aplicativo"""
        return {
            'games': {
                'keywords': ['game', 'play', 'score', 'level', 'player', 'win', 'lose', 'points', 'vida', 'jogo'],
                'image_indicators': ['game_over', 'player', 'enemy', 'coin', 'power_up', 'background'],
                'layout_patterns': ['high_image_density', 'bright_colors', 'large_buttons']
            },
            'educational': {
                'keywords': ['learn', 'study', 'quiz', 'test', 'lesson', 'education', 'ensino', 'aula', 'estudar'],
                'image_indicators': ['book', 'pencil', 'school', 'teacher', 'blackboard', 'academic'],
                'layout_patterns': ['clean_layout', 'readable_fonts', 'structured_content']
            },
            'utility': {
                'keywords': ['calculator', 'tool', 'converter', 'utility', 'helper', 'ferramenta', 'calculadora'],
                'image_indicators': ['icons', 'minimal_graphics', 'functional_buttons'],
                'layout_patterns': ['minimal_design', 'function_focused', 'clear_navigation']
            },
            'social': {
                'keywords': ['chat', 'message', 'friend', 'share', 'social', 'post', 'comentar', 'amigo'],
                'image_indicators': ['profile', 'avatar', 'heart', 'like', 'comment', 'share'],
                'layout_patterns': ['feed_layout', 'profile_pictures', 'interaction_buttons']
            },
            'business': {
                'keywords': ['business', 'work', 'professional', 'company', 'office', 'negócio', 'empresa'],
                'image_indicators': ['logo', 'professional', 'charts', 'documents', 'corporate'],
                'layout_patterns': ['professional_colors', 'structured_layout', 'minimal_decoration']
            }
        }
    
    def _load_design_benchmarks(self) -> Dict:
        """Carrega benchmarks de qualidade por categoria"""
        return {
            'games': {
                'min_image_quality': 85,
                'recommended_icon_count': 15,
                'color_vibrancy_target': 0.8,
                'material_design_compliance': 0.7
            },
            'educational': {
                'min_image_quality': 90,
                'recommended_icon_count': 8,
                'accessibility_target': 0.95,
                'readability_score': 0.9
            },
            'utility': {
                'min_image_quality': 88,
                'recommended_icon_count': 6,
                'simplicity_score': 0.9,
                'material_design_compliance': 0.9
            },
            'social': {
                'min_image_quality': 87,
                'recommended_icon_count': 12,
                'visual_consistency': 0.85,
                'brand_recognition': 0.8
            },
            'business': {
                'min_image_quality': 92,
                'recommended_icon_count': 10,
                'professional_appearance': 0.95,
                'accessibility_target': 0.9
            }
        }
    
    def _load_feedback_templates(self) -> Dict:
        """Carrega templates de feedback personalizados"""
        return {
            'games': {
                'excellent': [
                    "🎮 **Jogo visualmente impressionante!** Seus assets capturam perfeitamente a essência gaming.",
                    "🌟 **Qualidade de jogo profissional!** Os elementos visuais criam uma experiência envolvente.",
                    "🚀 **Game design de alta qualidade!** Parabéns pela atenção aos detalhes visuais."
                ],
                'good': [
                    "🎯 **Jogo bem desenvolvido!** Alguns ajustes podem tornar a experiência ainda mais polida.",
                    "🎨 **Bom progresso no design!** Com pequenos refinamentos, seu jogo pode se destacar.",
                    "⭐ **Jogo promissor!** Continue aprimorando os elementos visuais para máximo impacto."
                ],
                'needs_improvement': [
                    "🔧 **Potencial de jogo detectado!** Melhore a qualidade visual para aumentar o engajamento.",
                    "🎲 **Base sólida de jogo!** Foque na consistência visual para uma experiência mais profissional.",
                    "🎮 **Jogo em desenvolvimento!** Priorize a qualidade dos assets para melhor imersão."
                ]
            },
            'educational': {
                'excellent': [
                    "📚 **Material educacional exemplar!** Interface clara e acessível para aprendizado efetivo.",
                    "🎓 **Qualidade pedagógica superior!** Design otimizado para maximizar a compreensão.",
                    "✨ **Excelência educacional!** Seus elementos visuais facilitam o processo de aprendizagem."
                ],
                'good': [
                    "📖 **Boa ferramenta educacional!** Pequenos ajustes podem melhorar a experiência de aprendizado.",
                    "🌟 **Material bem estruturado!** Continue refinando para atingir excelência pedagógica.",
                    "📝 **Progresso educacional sólido!** Foque na acessibilidade para incluir mais estudantes."
                ],
                'needs_improvement': [
                    "📚 **Potencial educacional identificado!** Melhore a clareza visual para facilitar o aprendizado.",
                    "🎯 **Base educacional boa!** Priorize legibilidade e acessibilidade dos elementos visuais.",
                    "📖 **Em desenvolvimento educacional!** Foque na qualidade visual para engajar estudantes."
                ]
            },
            'utility': {
                'excellent': [
                    "🛠️ **Ferramenta profissional de alta qualidade!** Interface limpa e funcional.",
                    "⚡ **Utilidade excepcional!** Design focado em eficiência e usabilidade.",
                    "🎯 **Ferramenta bem executada!** Excelente equilíbrio entre função e forma."
                ],
                'good': [
                    "🔧 **Boa ferramenta!** Alguns refinamentos podem aumentar a eficiência da interface.",
                    "⭐ **Utilidade bem desenvolvida!** Continue simplificando para máxima usabilidade.",
                    "🛠️ **Progresso sólido!** Foque na consistência para uma experiência mais profissional."
                ],
                'needs_improvement': [
                    "🔨 **Ferramenta promissora!** Simplifique elementos visuais para melhor usabilidade.",
                    "⚙️ **Base funcional boa!** Priorize clareza e eficiência na interface.",
                    "🛠️ **Em desenvolvimento!** Foque na qualidade visual para uma ferramenta mais profissional."
                ]
            },
            'social': {
                'excellent': [
                    "💬 **App social envolvente!** Design que promove interação e engajamento.",
                    "🌟 **Qualidade social superior!** Interface atrativa que conecta pessoas efetivamente.",
                    "✨ **Experiência social excepcional!** Elementos visuais que facilitam a comunicação."
                ],
                'good': [
                    "📱 **Boa plataforma social!** Alguns ajustes podem aumentar o engajamento dos usuários.",
                    "💫 **App social bem desenvolvido!** Continue refinando para máxima interação.",
                    "🎨 **Progresso social sólido!** Foque na consistência visual para fortalecer a marca."
                ],
                'needs_improvement': [
                    "💬 **Potencial social identificado!** Melhore elementos visuais para maior engajamento.",
                    "📲 **Base social boa!** Priorize qualidade visual para atrair mais usuários.",
                    "🌐 **Em desenvolvimento social!** Foque na experiência visual para conectar pessoas."
                ]
            },
            'business': {
                'excellent': [
                    "💼 **Aplicação empresarial de alto nível!** Interface profissional e confiável.",
                    "🏢 **Qualidade corporativa excepcional!** Design que transmite seriedade e competência.",
                    "⭐ **Solução empresarial exemplar!** Excelente representação visual da marca."
                ],
                'good': [
                    "💻 **Boa solução empresarial!** Alguns refinamentos podem elevar o profissionalismo.",
                    "🎯 **App corporativo bem estruturado!** Continue aprimorando para máxima credibilidade.",
                    "📊 **Progresso empresarial sólido!** Foque na consistência para fortalecer a imagem."
                ],
                'needs_improvement': [
                    "💼 **Potencial empresarial detectado!** Melhore qualidade visual para maior credibilidade.",
                    "🏢 **Base corporativa boa!** Priorize profissionalismo nos elementos visuais.",
                    "📈 **Em desenvolvimento empresarial!** Foque na qualidade para transmitir confiança."
                ]
            }
        }
    
    def detect_app_context(self, aia_file, images: List, project_name: str = "") -> AppContext:
        """
        Detecta o contexto da aplicação usando IA
        """
        # Análise textual do nome do projeto
        text_indicators = self._analyze_text_indicators(project_name, aia_file)
        
        # Análise visual dos assets
        visual_indicators = self._analyze_visual_indicators(images)
        
        # Análise estrutural do layout
        layout_indicators = self._analyze_layout_patterns(images)
        
        # Combinar evidências para determinar contexto
        context = self._combine_evidence(text_indicators, visual_indicators, layout_indicators)
        
        return context
    
    def _analyze_text_indicators(self, project_name: str, aia_file) -> Dict:
        """Analisa indicadores textuais"""
        scores = {}
        text_content = project_name.lower()
        
        for category, patterns in self.app_patterns.items():
            score = 0
            for keyword in patterns['keywords']:
                if keyword in text_content:
                    score += 1
            scores[category] = score / len(patterns['keywords'])
        
        return scores
    
    def _analyze_visual_indicators(self, images: List) -> Dict:
        """Analisa indicadores visuais nos assets"""
        scores = {}
        
        for category in self.app_patterns.keys():
            scores[category] = 0
        
        # Análise baseada em nomes de arquivos e características
        for image in images:
            image_name = image.name.lower()
            
            for category, patterns in self.app_patterns.items():
                for indicator in patterns['image_indicators']:
                    if indicator in image_name:
                        scores[category] += 1
        
        # Normalizar scores
        total_images = len(images) if images else 1
        for category in scores:
            scores[category] = scores[category] / total_images
        
        return scores
    
    def _analyze_layout_patterns(self, images: List) -> Dict:
        """Analisa padrões de layout"""
        scores = {}
        
        if not images:
            return {category: 0 for category in self.app_patterns.keys()}
        
        # Métricas básicas
        total_images = len(images)
        icons = [img for img in images if img.asset_type == 'icon']
        large_images = [img for img in images if img.width > 500 or img.height > 500]
        
        # Densidade de imagens (games tendem a ter mais)
        image_density = total_images / 10  # Normalizado
        
        # Proporção de ícones vs imagens
        icon_ratio = len(icons) / total_images if total_images > 0 else 0
        
        # Análise por categoria
        scores['games'] = min(1.0, image_density * 0.7 + (1 - icon_ratio) * 0.3)
        scores['educational'] = min(1.0, icon_ratio * 0.6 + (1 - image_density) * 0.4)
        scores['utility'] = icon_ratio * 0.8
        scores['social'] = min(1.0, image_density * 0.5 + icon_ratio * 0.5)
        scores['business'] = icon_ratio * 0.7
        
        return scores
    
    def _combine_evidence(self, text_scores: Dict, visual_scores: Dict, layout_scores: Dict) -> AppContext:
        """Combina evidências para determinar contexto final"""
        combined_scores = {}
        
        for category in self.app_patterns.keys():
            # Peso para cada tipo de evidência
            combined_scores[category] = (
                text_scores.get(category, 0) * 0.4 +
                visual_scores.get(category, 0) * 0.4 +
                layout_scores.get(category, 0) * 0.2
            )
        
        # Encontrar categoria com maior score
        best_category = max(combined_scores, key=combined_scores.get)
        confidence = combined_scores[best_category]
        
        # Determinar público-alvo baseado na categoria
        target_mapping = {
            'games': 'teens',
            'educational': 'kids',
            'utility': 'adults',
            'social': 'teens',
            'business': 'professional'
        }
        
        # Determinar complexidade baseado no número de assets
        complexity_mapping = {
            'simple': 'few assets, clean design',
            'moderate': 'balanced complexity',
            'complex': 'many features and assets',
            'advanced': 'sophisticated design patterns'
        }
        
        return AppContext(
            category=best_category,
            target_audience=target_mapping.get(best_category, 'adults'),
            complexity_level='moderate',  # Simplificado por agora
            visual_style='modern',  # Simplificado por agora
            confidence_score=confidence
        )
    
    def generate_intelligent_feedback(self, context: AppContext, scores: Dict, images: List, aia_file) -> List[str]:
        """
        Gera feedback inteligente baseado no contexto da aplicação
        """
        feedback = []
        overall_score = scores.get('overall_score', 0)
        
        # Determinar nível de qualidade
        if overall_score >= 85:
            quality_level = 'excellent'
        elif overall_score >= 70:
            quality_level = 'good'
        else:
            quality_level = 'needs_improvement'
        
        # Feedback contextual principal
        templates = self.feedback_templates.get(context.category, {})
        if quality_level in templates:
            import random
            main_feedback = random.choice(templates[quality_level])
            feedback.append(main_feedback)
        
        # Análise específica por categoria
        category_feedback = self._generate_category_specific_feedback(context, scores, images)
        feedback.extend(category_feedback)
        
        # Comparação com benchmarks
        benchmark_feedback = self._generate_benchmark_comparison(context, scores, images)
        feedback.extend(benchmark_feedback)
        
        # Sugestões acionáveis
        actionable_suggestions = self._generate_actionable_suggestions(context, scores, images)
        feedback.extend(actionable_suggestions)
        
        # Priorização de melhorias
        priority_feedback = self._generate_priority_recommendations(context, scores, images)
        feedback.extend(priority_feedback)
        
        return feedback
    
    def _generate_category_specific_feedback(self, context: AppContext, scores: Dict, images: List) -> List[str]:
        """Gera feedback específico para a categoria da aplicação"""
        feedback = []
        category = context.category
        overall_score = scores.get('overall_score', 0)
        
        if category == 'games':
            if overall_score < 80:
                feedback.append(
                    "🎮 **Dica para Games:** Jogos se beneficiam de assets visuais de alta qualidade. "
                    "Considere investir em sprites e backgrounds mais detalhados para aumentar o engajamento."
                )
            
            icons = [img for img in images if img.asset_type == 'icon']
            if len(icons) > 10:
                feedback.append(
                    "🎨 **Riqueza Visual:** Seu jogo tem uma boa variedade de ícones! "
                    "Certifique-se de que todos seguem um estilo visual consistente."
                )
        
        elif category == 'educational':
            accessibility_issues = sum(1 for img in images if getattr(img, 'accessibility_score', 80) < 85)
            if accessibility_issues > 0:
                feedback.append(
                    f"♿ **Acessibilidade Educacional:** {accessibility_issues} elemento(s) podem ser "
                    "melhorados para inclusão de estudantes com necessidades especiais. "
                    "Apps educacionais devem ser acessíveis a todos."
                )
            
            if overall_score >= 85:
                feedback.append(
                    "📚 **Excelência Pedagógica:** Qualidade visual adequada para ambiente educacional. "
                    "Seus estudantes terão uma experiência de aprendizado mais efetiva."
                )
        
        elif category == 'utility':
            if len(images) > 15:
                feedback.append(
                    "🔧 **Simplicidade:** Ferramentas se beneficiam de design minimalista. "
                    "Considere reduzir elementos visuais desnecessários para foco na funcionalidade."
                )
            
            material_compliance = sum(1 for img in images if getattr(img, 'is_material_icon', False))
            if material_compliance > len(images) * 0.8:
                feedback.append(
                    "✨ **Consistência Material:** Excelente uso de ícones Material Design! "
                    "Isso garante familiaridade e usabilidade para os usuários."
                )
        
        elif category == 'social':
            profile_related = sum(1 for img in images if 'profile' in img.name.lower() or 'avatar' in img.name.lower())
            if profile_related == 0:
                feedback.append(
                    "👥 **Apps Sociais:** Considere adicionar elementos visuais relacionados a perfis "
                    "e interação social para melhorar a experiência do usuário."
                )
        
        elif category == 'business':
            if overall_score >= 90:
                feedback.append(
                    "💼 **Credibilidade Empresarial:** Excelente qualidade visual que transmite "
                    "profissionalismo e confiança aos usuários corporativos."
                )
            else:
                feedback.append(
                    "🏢 **Imagem Corporativa:** Para aplicações empresariais, considere investir "
                    "em assets de alta qualidade para fortalecer a credibilidade da marca."
                )
        
        return feedback
    
    def _generate_benchmark_comparison(self, context: AppContext, scores: Dict, images: List) -> List[str]:
        """Compara com benchmarks da categoria"""
        feedback = []
        category = context.category
        benchmarks = self.design_benchmarks.get(category, {})
        
        overall_score = scores.get('overall_score', 0)
        target_score = benchmarks.get('min_image_quality', 85)
        
        if overall_score >= target_score:
            feedback.append(
                f"📊 **Benchmark Atingido:** Seu score ({overall_score:.1f}) supera o mínimo "
                f"recomendado para apps {category} ({target_score})."
            )
        else:
            gap = target_score - overall_score
            feedback.append(
                f"🎯 **Meta de Qualidade:** Para excelência em apps {category}, "
                f"melhore {gap:.1f} pontos para atingir o benchmark de {target_score}."
            )
        
        # Análise específica de ícones
        recommended_icons = benchmarks.get('recommended_icon_count', 10)
        actual_icons = len([img for img in images if img.asset_type == 'icon'])
        
        if actual_icons < recommended_icons * 0.7:
            feedback.append(
                f"🎨 **Variedade de Ícones:** Apps {category} se beneficiam de "
                f"aproximadamente {recommended_icons} ícones. Você tem {actual_icons}."
            )
        elif actual_icons > recommended_icons * 1.5:
            feedback.append(
                f"🎯 **Simplificação:** Considere reduzir a quantidade de ícones "
                f"({actual_icons}) para o recomendado em apps {category} (~{recommended_icons})."
            )
        
        return feedback
    
    def _generate_actionable_suggestions(self, context: AppContext, scores: Dict, images: List) -> List[str]:
        """Gera sugestões específicas e acionáveis"""
        suggestions = []
        
        # Análise de assets problemáticos
        low_quality = [img for img in images if self._calculate_image_score(img) < 60]
        if low_quality:
            suggestions.append(
                f"🔧 **Ação Imediata:** Substitua ou melhore {len(low_quality)} asset(s) com baixa qualidade: "
                f"{', '.join([img.name for img in low_quality[:3]])}"
                f"{'...' if len(low_quality) > 3 else ''}"
            )
        
        # Sugestões de otimização
        large_files = [img for img in images if img.file_size > 500*1024]  # > 500KB
        if large_files:
            total_size = sum(img.file_size for img in large_files) / (1024*1024)
            suggestions.append(
                f"💾 **Otimização de Performance:** Comprima {len(large_files)} arquivo(s) grandes "
                f"(total: {total_size:.1f}MB) para melhorar o carregamento do app."
            )
        
        # Sugestões de acessibilidade
        accessibility_issues = sum(1 for img in images if getattr(img, 'accessibility_score', 90) < 80)
        if accessibility_issues > 0:
            suggestions.append(
                f"♿ **Melhoria de Acessibilidade:** {accessibility_issues} elemento(s) precisam "
                "de ajustes de contraste ou legibilidade para melhor acessibilidade."
            )
        
        # Sugestões Material Design
        non_material = [img for img in images if img.asset_type == 'icon' and not getattr(img, 'is_material_icon', False)]
        if len(non_material) > 3:
            suggestions.append(
                f"🎨 **Consistência Visual:** Substitua {len(non_material)} ícone(s) por equivalentes "
                "do Material Design para melhor consistência e familiaridade."
            )
        
        return suggestions
    
    def _generate_priority_recommendations(self, context: AppContext, scores: Dict, images: List) -> List[str]:
        """Gera recomendações priorizadas por impacto"""
        priorities = []
        overall_score = scores.get('overall_score', 0)
        
        # Prioridade 1: Problemas críticos
        critical_issues = [img for img in images if self._calculate_image_score(img) < 40]
        if critical_issues:
            priorities.append(
                f"🚨 **PRIORIDADE 1 - CRÍTICO:** {len(critical_issues)} asset(s) com problemas graves "
                "que afetam significativamente a qualidade do app. Corrija imediatamente."
            )
        
        # Prioridade 2: Melhorias de alto impacto
        if overall_score < 70:
            priorities.append(
                "⚡ **PRIORIDADE 2 - ALTO IMPACTO:** Foque primeiro nos assets com menor pontuação "
                "para obter melhorias rápidas e significativas no score geral."
            )
        
        # Prioridade 3: Otimizações
        if len(images) > 20:
            priorities.append(
                "🎯 **PRIORIDADE 3 - OTIMIZAÇÃO:** Com muitos assets, priorize qualidade sobre "
                "quantidade. Considere remover elementos desnecessários."
            )
        
        # Prioridade 4: Polimento
        if overall_score >= 75:
            priorities.append(
                "✨ **PRIORIDADE 4 - POLIMENTO:** Boa base de qualidade! Foque em detalhes "
                "como consistência de estilo e conformidade com Material Design."
            )
        
        return priorities
    
    def _calculate_image_score(self, image) -> float:
        """Calcula score simplificado de uma imagem"""
        # Implementação simplificada - seria expandida com métricas reais
        base_score = 70
        
        # Ajustes baseados em características
        if hasattr(image, 'width') and hasattr(image, 'height'):
            if image.width >= 300 and image.height >= 300:
                base_score += 10
            elif image.width < 100 or image.height < 100:
                base_score -= 20
        
        if hasattr(image, 'file_size'):
            if image.file_size > 1024*1024:  # > 1MB
                base_score -= 15
            elif image.file_size < 10*1024:  # < 10KB
                base_score -= 10
        
        if hasattr(image, 'is_material_icon') and image.is_material_icon:
            base_score += 15
        
        return max(0, min(100, base_score))


def generate_ai_enhanced_feedback(aia_file, images: List, scores: Dict, project_name: str = "") -> List[str]:
    """
    Função principal para gerar feedback aprimorado com IA
    """
    ai_engine = AIFeedbackEngine()
    
    # Detectar contexto da aplicação
    context = ai_engine.detect_app_context(aia_file, images, project_name)
    
    # Gerar feedback inteligente
    feedback = ai_engine.generate_intelligent_feedback(context, scores, images, aia_file)
    
    # Adicionar informações do contexto detectado
    confidence_emoji = "🎯" if context.confidence_score > 0.7 else "🔍"
    context_info = (
        f"{confidence_emoji} **Contexto Detectado:** App {context.category} "
        f"para público {context.target_audience} "
        f"(confiança: {context.confidence_score:.0%})"
    )
    
    return [context_info] + feedback


# Integração com o sistema existente
def enhance_existing_recommendations(existing_recommendations: List[str], aia_file, images: List, scores: Dict) -> List[str]:
    """
    Melhora recomendações existentes com análise de IA
    """
    # Gerar novo feedback com IA
    ai_feedback = generate_ai_enhanced_feedback(aia_file, images, scores)
    
    # Combinar com recomendações existentes, priorizando IA
    enhanced = ai_feedback.copy()
    
    # Adicionar recomendações existentes que não são redundantes
    for rec in existing_recommendations:
        if not any(keyword in rec.lower() for keyword in ['score', 'qualidade', 'recomend']):
            enhanced.append(rec)
    
    return enhanced
