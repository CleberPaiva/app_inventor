from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def markdown_to_html(text):
    """Convert simple markdown-like text to HTML for print"""
    if not text:
        return ""
    
    # Ensure text is a string and handle any encoding issues
    if isinstance(text, bytes):
        text = text.decode('utf-8')
    text = str(text)
    
    # Convert headers with emojis
    text = re.sub(r'^([📊🎯🏆🥇🥈🥉❌✅⚠️🔴💾📐🎨💡🚨])\s+\*\*(.+?)\*\*', r'<h3><span class="emoji">\1</span> <strong>\2</strong></h3>', text, flags=re.MULTILINE)
    
    # Convert regular headers
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
    
    # Convert line breaks to paragraphs, but preserve existing structure
    lines = text.split('\n')
    formatted_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            formatted_lines.append('<br>')
            continue
            
        if line.startswith('<li>'):
            if not in_list:
                formatted_lines.append('<ul>')
                in_list = True
            formatted_lines.append(line)
        else:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            if not line.startswith('<h') and not line.startswith('<hr'):
                formatted_lines.append(f'<p>{line}</p>')
            else:
                formatted_lines.append(line)
    
    if in_list:
        formatted_lines.append('</ul>')
    
    result = '\n'.join(formatted_lines)
    
    # Clean up multiple breaks
    result = re.sub(r'(<br>\s*){3,}', '<br><br>', result)
    result = re.sub(r'<p></p>', '', result)
    
    return mark_safe(result)

@register.filter
def format_report(text):
    """Format the usability report for better print display"""
    if not text:
        return ""
    
    # Ensure we have a proper string
    if isinstance(text, bytes):
        text = text.decode('utf-8')
    text = str(text)
    
    # Apply markdown conversion
    return markdown_to_html(text)
