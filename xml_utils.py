import re

def node(key, attrs=None, value=""):
    """Создание XML-узла."""
    if attrs is None:
        attrs = {}
    if isinstance(value, list):
        value = ''.join(value)
    
    attrs_str = ''.join(f' {k}="{v}"' for k, v in attrs.items())
    if not value:
        return f'<{key}{attrs_str}/>'
    return f'<{key}{attrs_str}>{value}</{key}>'

def create_node(key, attrs=None, value=""):
    """Создание XML-узла (аналогична функции node)."""
    return node(key, attrs, value)  # Просто перенаправляем это на node

def format_xml(xml, tab='\t', nl='\n'):
    """Форматирование XML-строки с отступами."""
    if '<' not in xml:
        return xml
    
    formatted = ''
    indent = ''
    nodes = re.split(r'>\s*<', xml[1:-1])  # +1 для исключения первого символа '<' и -1 для исключения последнего символа '>'
    
    if nodes[0][0] == '?':
        formatted += '<' + nodes.pop(0) + '>' + nl
    
    for node in nodes:
        if node[0] == '/':
            indent = indent[:-len(tab)]  # Уменьшаем отступ
        formatted += f"{indent}<{node}>" + nl
        if (
            node[0] != '/' and 
            node[-1] != '/' and 
            '</' not in node
        ):
            indent += tab  # Увеличиваем отступ
    
    return formatted

# Экспортируем функции
if __name__ == "__main__":
    pass