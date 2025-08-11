from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def markdown_to_html(text):
    """Convert simple markdown-like text to HTML for print"""
    if not text:
        return ""
    
    # Convert headers
    text = re.sub(r'^#\s+(.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    text = re.sub(r'^##\s+(.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^###\s+(.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^####\s+(.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    
    # Convert bold text
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    
    # Convert bullet points
    text = re.sub(r'^•\s+(.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'^-\s+(.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    
    # Convert horizontal lines
    text = re.sub(r'^═+$', r'<hr class="double-line">', text, flags=re.MULTILINE)
    text = re.sub(r'^─+$', r'<hr class="single-line">', text, flags=re.MULTILINE)
    
    # Convert emoji headers (like 📊, 🎯, etc.)
    text = re.sub(r'^([📊🎯🏆🥇🥈🥉❌✅⚠️🔴💾📐🎨])\s+\*\*(.+?)\*\*', r'<h3><span class="emoji">\1</span>\2</h3>', text, flags=re.MULTILINE)
    
    # Convert paragraphs (double line breaks)
    text = re.sub(r'\n\n+', '</p><p>', text)
    text = '<p>' + text + '</p>'
    
    # Clean up empty paragraphs
    text = re.sub(r'<p></p>', '', text)
    text = re.sub(r'<p>\s*</p>', '', text)
    
    # Wrap lists in ul tags
    text = re.sub(r'(<li>.*?</li>)', lambda m: '<ul>' + m.group(1) + '</ul>', text, flags=re.DOTALL)
    
    # Convert line breaks to <br>
    text = text.replace('\n', '<br>')
    
    return mark_safe(text)

@register.filter
def format_report(text):
    """Format the usability report for better print display"""
    if not text:
        return ""
    
    # Split into sections
    sections = text.split('\n\n')
    formatted_sections = []
    
    for section in sections:
        if not section.strip():
            continue
            
        # Add section wrapper
        if section.startswith('📊') or section.startswith('🎯') or section.startswith('✅'):
            formatted_sections.append(f'<div class="section">{section}</div>')
        else:
            formatted_sections.append(section)
    
    result = '\n\n'.join(formatted_sections)
    return markdown_to_html(result)
