def add_fields_to_path(simulator, path, lan_device, fields, writable=False):
    for k in fields:  # Для всех перечисленных полей в модели
        field = fields[k]
        v = lan_device.get(k)  # Получаем значение из LAN устройства
        if v is not None:
            if not field.valid(v):  # Если значение недопустимо, переходим к следующему полю
                continue
            if hasattr(field, 'format'):
                v = field.format(v)  # Если поле имеет формат, значение должно быть отформатировано
        else:
            v = field.default or ''  # Если нет значения по умолчанию, используем пустую строку
            # Если значение по умолчанию - функция, используем её возвращаемое значение
            if callable(v):
                v = v(lan_device, simulator)
            # Если данное значение равно None, форматировать значение по умолчанию не нужно
        
        simulator.device[path + field.key] = [writable, v, field.type]

def create_nodes_for_path(simulator, full_path):
    steps = full_path.split('.')
    if steps[-1] == '':
        steps.pop()
    
    path = steps[0] + '.'
    for step in steps:
        if simulator.device.get(path) is None:  # Создаем узел только если он не существует
            simulator.device[path] = [False]  # Создание небазового узла
        path += step + '.'  # Обновляем путь для следующего шага

def get_next_index_in_path(simulator, path):
    index = 1
    while simulator.device.get(f"{path}{index}.") is not None:
        index += 1
    return index