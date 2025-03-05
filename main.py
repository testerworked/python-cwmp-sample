import os
import csv
from pathlib import Path
from simulator import Simulator, InvalidTaskNameError
from xml_utils import format_xml  # предположим, что этот модуль создан.

# Функция для парсинга CSV файла
def parse_csv(data):
    rows = []
    reader = csv.DictReader(data.splitlines())
    for row in reader:
        rows.append(row)
    return rows

# Функция для создания симулятора
def create_simulator(acs_url, data_model, serial_number, mac_addr, verbose=False, periodic_informs_disabled=False):
    device = {}  # Структура данных для TR069
    data_model_path = Path(__file__).parent.parent / "models" / f"{data_model}.csv"

    with open(data_model_path, 'r') as f:
        data = f.read()
        rows = parse_csv(data)

    for row in rows:
        is_object = row["Object"] == "true"
        id = row["Parameter"]
        if is_object:
            id += "."

        v = [row["Writable"] == "true"]
        if not is_object:
            v.append(row.get("Value", ""))
            value_type = row.get("Value type")
            if value_type is not None:
                v.append(value_type)
        
        device[id] = v
    
    return Simulator(device, serial_number, mac_addr, acs_url, verbose, periodic_informs_disabled)

# Экспортируем ошибки и функции
InvalidTaskNameError = InvalidTaskNameError