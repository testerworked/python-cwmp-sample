from models import models  # Импортируем модели
from manipulations_utils import get_next_index_in_path, add_fields_to_path, create_nodes_for_path

class Manipulations:
    def __init__(self, device, tr):
        self.device = device
        self.TR = tr

    def add_lan_device(self, lan_device):
        if not lan_device:
            return  # Возвращаем, если 'lan_device' не передан

        device_id = self.device.get('DeviceID.ID')
        model = models.get(device_id[1]) if device_id else models.get('')

        # Проверка радиомодуля
        radio = lan_device.get('radio')
        if model and (radio not in {2, 5, None}):
            return

        # Очистка списка путей
        if '_sortedPaths' in self.device:
            del self.device['_sortedPaths']

        # Определяем путь для hosts
        hosts_path = model.hosts.path if model else ('InternetGatewayDevice.LANDevice.1.Hosts.' if self.TR == 'tr098' else 'Device.Hosts.')

        # Добавляем в раздел Hosts
        hosts = model.hosts if model else None  # Структура параметров хостов
        host_path = f"{hosts_path}Host." if hosts else None
        host_index = get_next_index_in_path(self, host_path)
        lan_device['hostIndex'] = host_index
        self.device[hosts_path + 'HostNumberOfEntries'][1] = str(host_index)  # Сохраняем увеличенное количество записей

        # 'InternetGatewayDevice.LANDevice.1.Hosts.Host' уже существует, создаем родительский узел хоста по i-му индексу
        host_path += f"{host_index}."
        self.device[host_path] = [False]  # Создаем родительский узел для хоста в i-м индексе

        if hosts:
            add_fields_to_path(self, host_path, lan_device, hosts.fields)

        # Добавляем в раздел AssociatedDevice
        if not model or not radio:
            return
        associated_device = model.associated_device
        associated_device_path = associated_device['path' + str(radio)]
        associated_device_index = get_next_index_in_path(self, associated_device_path)
        lan_device['associatedDeviceIndex'] = associated_device_index
        associated_device_path += f"{associated_device_index}."
        
        create_nodes_for_path(self, associated_device_path)
        add_fields_to_path(self, associated_device_path, lan_device, associated_device.fields)
