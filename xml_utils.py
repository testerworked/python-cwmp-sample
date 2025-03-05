def node(key, attrs=None, value=""):
    if attrs is None:
        attrs = {}
    if isinstance(value, list):
        value = ''.join(value)
    
    attrs_str = ''.join(f' {k}="{v}"' for k, v in attrs.items())
    if not value:
        return f'<{key}{attrs_str}/>'
    return f'<{key}{attrs_str}>{value}</{key}>'

def format_xml(xml, tab='\t', nl='\n'):
    if '<' not in xml:
        return xml
    
    formatted = ''
    indent = ''
    nodes = xml[1:-1].split(/>\s*</)
    
    if nodes[0][0] == '?':
        formatted += '<' + nodes.pop(0) + '>' + nl
    
    for i, node in enumerate(nodes):
        if node[0] == '/':
            indent = indent[:-len(tab)]  # decrease indent
        formatted += indent + '<' + node + '>' + nl
        if (
            node[0] != '/' and 
            node[-1] != '/' and 
            '</' not in node
        ):
            indent += tab  # increase indent
    
    return formatted

# Экспортируем функции
if __name__ == "__main__":
    pass