CHAR_DOUBLE_QUOTE = 34
CHAR_CR = 13
CHAR_LF = 10
CHAR_COMMA = 44

def parse_csv(data):
    rows = []
    row = []
    field = ""
    escaped_state = False
    i = 0

    data = data.strip() + "\n"  # Убираем лишние пробелы и добавляем перевод строки

    while i < len(data):
        char = data[i]
        char_code = ord(char)  # Получаем ASCII-код символа

        if char_code == CHAR_DOUBLE_QUOTE:
            if not escaped_state:
                if field:
                    raise ValueError("Invalid CSV format")
                escaped_state = True
            else:
                next_char_code = ord(data[i + 1]) if i + 1 < len(data) else None
                if next_char_code == CHAR_DOUBLE_QUOTE:  # escaping quote
                    field += char
                    i += 1
                elif next_char_code and next_char_code not in (CHAR_COMMA, CHAR_CR, CHAR_LF):
                    raise ValueError("Invalid CSV format")
                else:
                    escaped_state = False  # end of quoted field
        elif char_code == CHAR_COMMA:
            if not escaped_state:
                row.append(field)
                field = ""
            else:
                field += char
        elif char_code in (CHAR_CR, CHAR_LF):
            if not escaped_state:
                row.append(field)
                rows.append(row)
                row = []
                # Игнорируем пустые строки
                while i + 1 < len(data) and data[i + 1] in ("\r", "\n"):
                    i += 1
            else:
                field += char
        else:
            field += char
        
        i += 1

    if escaped_state:
        raise ValueError("Invalid CSV format")
    
    return rows

def reduce(rows, header_first_row=True):
    if header_first_row:
        headers = rows.pop(0)  # Извлекаем заголовки из первой строки
        return [dict(zip(headers, row)) for row in rows]
    else:
        return [dict(row) for row in rows]  # Создаем словарь для каждой строки

# Пример использования
if __name__ == "__main__":
    sample_data = '"Name","Age"\n"John Doe",30\n"Jane Doe",25\n'
    parsed_data = parse_csv(sample_data)
    print(parsed_data)  # [['Name', 'Age'], ['John Doe', '30'], ['Jane Doe', '25']]
    reduced_data = reduce(parsed_data)
    print(reduced_data)  # [{'Name': 'John Doe', 'Age': '30'}, {'Name': 'Jane Doe', 'Age': '25'}]