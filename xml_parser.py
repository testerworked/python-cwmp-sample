import re

# Константы
CHAR_SINGLE_QUOTE = 39
CHAR_DOUBLE_QUOTE = 34
CHAR_LESS_THAN = 60
CHAR_GREATER_THAN = 62
CHAR_COLON = 58
CHAR_SPACE = 32
CHAR_TAB = 9
CHAR_CR = 13
CHAR_LF = 10
CHAR_SLASH = 47
CHAR_EXMARK = 33
CHAR_QMARK = 63
CHAR_EQUAL = 61

STATE_LESS_THAN = 1
STATE_SINGLE_QUOTE = 2
STATE_DOUBLE_QUOTE = 3

def parse_xml_declaration(buffer):
    for enc in ["utf-16", "utf-8", "latin-1", "ascii"]:
        try:
            str_buffer = buffer.decode(enc).strip()
            if str_buffer.startswith("<?xml"):
                str_buffer = str_buffer.split("\n")[0].strip()
                return parse_attrs(str_buffer[5:-2])
        except (UnicodeDecodeError, ValueError):
            continue
    return None

def parse_attrs(string):
    attrs = []
    length = len(string)

    state = 0
    name = ""
    namespace = ""
    local_name = ""
    idx = 0
    colon_idx = 0

    for i in range(length):
        c = ord(string[i])
        if c in (CHAR_SINGLE_QUOTE, CHAR_DOUBLE_QUOTE):
            if state == c:
                state = 0
                if name:
                    value = string[idx + 1:i]
                    attrs.append({'name': name, 'namespace': namespace, 'localName': local_name, 'value': value})
                    name = ""
                    idx = i + 1
            else:
                state = c
                idx = i
            continue

        if c == CHAR_COLON:
            if idx >= colon_idx:
                colon_idx = i
            continue

        if c == CHAR_EQUAL:
            if name:
                raise ValueError(f"Unexpected character at {i}")
            name = string[idx:i].strip()
            if colon_idx > idx:
                namespace = string[idx:colon_idx].strip()
                local_name = string[colon_idx + 1:i].strip()
            else:
                namespace = ""
                local_name = name

    if name:
        raise ValueError(f"Attribute must have value at {idx}")

    tail = string[idx:]
    if tail.strip():
        raise ValueError(f"Unexpected string at {length - len(tail)}")

    return attrs

def decode_entities(string):
    entities = {
        "&quot;": '"',
        "&amp;": "&",
        "&apos;": "'",
        "&lt;": "<",
        "&gt;": ">"
    }
    def replace_entity(match):
        entity = match.group(0)
        if entity in entities:
            return entities[entity]
        if entity.startswith("&#x"):
            n = int(entity[3:-1], 16)
            return chr(n)
        elif entity.startswith("&#"):
            n = int(entity[2:-1])
            return chr(n)
        return entity
    return re.sub(r'&[0-9a-z#]+;', replace_entity, string)

def encode_entities(string):
    entities = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&apos;",
        "<": "&lt;",
        ">": "&gt;"
    }
    if not isinstance(string, str):
        string = str(string)
    return re.sub(r'[&"\'<>]', lambda match: entities[match.group(0)], string)

def parse_xml(string):
    length = len(string)
    state1 = 0
    state1_index = 0
    state2 = 0
    state2_index = 0

    root = {
        'name': 'root',
        'namespace': '',
        'localName': 'root',
        'attrs': '',
        'text': '',
        'bodyIndex': 0,
        'children': []
    }

    stack = [root]

    for i in range(length):
        char_code = ord(string[i])
        if char_code == CHAR_SINGLE_QUOTE:
            if (state1 & 0xff) == STATE_SINGLE_QUOTE:
                state1 = state2
                state1_index = state2_index
                state2 = 0
                continue
            elif (state1 & 0xff) == STATE_LESS_THAN:
                state2 = state1
                state2_index = state1_index
                state1 = STATE_SINGLE_QUOTE
                state1_index = i
                continue

        elif char_code == CHAR_DOUBLE_QUOTE:
            if (state1 & 0xff) == STATE_DOUBLE_QUOTE:
                state1 = state2
                state1_index = state2_index
                state2 = 0
                continue
            elif (state1 & 0xff) == STATE_LESS_THAN:
                state2 = state1
                state2_index = state1_index
                state1 = STATE_DOUBLE_QUOTE
                state1_index = i
                continue

        elif char_code == CHAR_LESS_THAN:
            if (state1 & 0xff) == 0:
                state2 = state1
                state2_index = state1_index
                state1 = STATE_LESS_THAN
                state1_index = i
            continue

        elif char_code == CHAR_COLON:
            if (state1 & 0xff) == STATE_LESS_THAN:
                colon_index = (state1 >> 8) & 0xff
                if colon_index == 0:
                    state1 ^= ((i - state1_index) & 0xff) << 8
            continue

        elif char_code in (CHAR_SPACE, CHAR_TAB, CHAR_CR, CHAR_LF):
            if (state1 & 0xff) == STATE_LESS_THAN:
                ws_index = (state1 >> 16) & 0xff
                if ws_index == 0:
                    state1 ^= ((i - state1_index) & 0xff) << 16
            continue

        elif char_code == CHAR_GREATER_THAN:
            if (state1 & 0xff) == STATE_LESS_THAN:
                second_char = ord(string[state1_index + 1])
                ws_index = (state1 >> 16) & 0xff
                name, colon_index, e, parent, self_closing, local_name, namespace = None, None, None, None, None, None, None

                if second_char == CHAR_SLASH:
                    e = stack.pop()
                    name = string[state1_index + 2:i] if ws_index == 0 else string[state1_index + 2:state1_index + ws_index]
                    if e['name'] != name:
                        raise ValueError(f"Unmatched closing tag at {i}")
                    if not e['children']:
                        e['text'] = string[e['bodyIndex']:state1_index]
                    state1 = state2
                    state1_index = state2_index
                    state2 = 0
                    continue

                elif second_char == CHAR_EXMARK:
                    if string.startswith("![CDATA[", state1_index + 1):
                        if string.endswith("]]", i):
                            raise ValueError(f"CDATA nodes are not supported at {i}")
                    elif string.startswith("!--", state1_index + 1):
                        if string.endswith("--", i):
                            state1 = state2
                            state1_index = state2_index
                            state2 = 0
                    continue

                elif second_char == CHAR_QMARK:
                    if ord(string[i - 1]) == CHAR_QMARK:
                        state1 = state2
                        state1_index = state2_index
                        state2 = 0
                    continue

                else:
                    self_closing = (ord(string[i - 1]) == CHAR_SLASH)
                    parent = stack[-1]
                    colon_index = (state1 >> 8) & 0xff

                    name = string[state1_index + 1:i - self_closing] if ws_index == 0 else string[state1_index + 1:state1_index + ws_index]
                    if colon_index and (not ws_index or colon_index < ws_index):
                        local_name = name[colon_index:]
                        namespace = name[:colon_index - 1]
                    else:
                        local_name = name
                        namespace = ""

                    e = {
                        'name': name,
                        'namespace': namespace,
                        'localName': local_name,
                        'attrs': string[state1_index + ws_index + 1:i - self_closing] if ws_index else "",
                        'text': "",
                        'bodyIndex': i + 1,
                        'children': []
                    }
                    parent['children'].append(e)
                    if not self_closing:
                        stack.append(e)

                    state1 = state2
                    state1_index = state2_index
                    state2 = 0
                    continue

    if state1:
        raise ValueError(f"Unclosed token at {state1_index}")

    if len(stack) > 1:
        e = stack[-1]
        raise ValueError(f"Unclosed XML element at {e['bodyIndex']}")

    if not root['children']:
        root['text'] = string
    
    return root

# Экспортируем функции
if __name__ == "__main__":
    pass