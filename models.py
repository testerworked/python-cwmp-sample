import re
import random
from manipulations_utils import get_next_index_in_path

# Validation functions.
def is_boolean(v):
    return isinstance(v, bool)

def is_string(v):
    return isinstance(v, str)

def is_number(v):
    return isinstance(v, (int, float))

def is_positive_number(v):
    return is_number(v) and v > 0

def is_mac_address(v):
    return is_string(v) and re.match(r'^(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', v)

def is_ipv4(v):
    return is_string(v) and re.match(r'^(?:25[0-5]|2[0-4]\d|1?\d{0,2})(?:\.(?:25[0-5]|2[0-4]\d|1?\d{0,2})){3}$', v)

bandwidths = {'20': True, '40': True, '80': True, '160': True}
def is_bandwidth(v):
    return is_number(v) and str(v) in bandwidths

modes = {'n': True, 'ac': True, 'ax': True, 'a': True, 'b': True, 'g': True}
def is_mode(v):
    return v in modes

def is_rssi(v):
    return is_number(v) and v < 0

# Formatting functions.
def to_string(v):
    return str(v)

def to_integer(v):
    return int(v)

def to_bandwidth(v):
    return f"{v}MHz"

# Default value generators.
def random_mac():
    return ":".join(random.choice("0123456789abcdef") for _ in range(6))

def basic_default_radio_mode(land_device):
    return 'n' if land_device['radio'] == 2 else 'ac'

def basic_default_interface(land_device):
    return '802.11' if 'radio' in land_device else 'Ethernet'

def tplink_default_interface(land_device):
    return 'Wi-Fi' if 'radio' in land_device else ''

def default_ipv4(land_device, simulator):
    ip_parts = simulator.device.get('InternetGatewayDevice.LANDevice.1.LANHostConfigManagement.IPInterface.1.IPInterfaceIPAddress' if simulator.TR == 'tr098' else 'Device.IP.Interface.1.IPv4Address.1.IPAddress')[1].split('.')
    last_part = int(ip_parts[3]) + land_device['hostIndex']
    if last_part > 255:
        raise ValueError('IP overflow when adding new device.')
    ip_parts[3] = str(last_part)
    return '.'.join(ip_parts)

# Utility functions.
def copy(obj, modifications=None):
    if modifications is None:
        modifications = {}
    return {k: modifications.get(k, obj[k]) for k in obj}

def merge(obj1, obj2):
    ret = {**obj1, **obj2}
    return {k: v for k, v in ret.items() if v is not None}

def add_device_block_wlan_access_control(simulator, path, paths_with_shared_index):
    new_index = max(get_next_index_in_path(simulator, p) for p in paths_with_shared_index)
    path += f"{new_index}."

    simulator.device.set(path, [True])
    simulator.device.set(path + 'Name', [True, '', 'xsd:string'])
    simulator.device.set(path + 'MACAddress', [True, '00:00:00:00:00:00', 'xsd:string'])

    return new_index

def add_device_block_multilaser(simulator, path):
    return add_device_block_wlan_access_control(simulator, path, [
        'InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.X_ZTE-COM_AccessControl.',
        'InternetGatewayDevice.LANDevice.1.WLANConfiguration.5.X_ZTE-COM_AccessControl.',
    ])

def add_device_block_mac_access_control(simulator, path):
    new_index = get_next_index_in_path(simulator, path)
    path += f"{new_index}."

    simulator.device.set(path, [True])
    simulator.device.set(path + 'Enable', [True, 'false', 'xsd:boolean'])
    simulator.device.set(path + 'Mode', [True, '', 'xsd:string'])
    simulator.device.set(path + 'Name', [True, '', 'xsd:string'])
    simulator.device.set(path + 'DestinationMACAddress', [True, '00:00:00:00:00:00', 'xsd:string'])
    simulator.device.set(path + 'Protocol', [True, '', 'xsd:string'])
    simulator.device.set(path + 'SourceMACAddress', [True, '00:00:00:00:00:00', 'xsd:string'])
    simulator.device.set(path + 'Type', [True, '', 'xsd:string'])

    return new_index

# Default port mapping parameters.
port_mapping_default_params = {
    'PortMappingEnabled': {'value': 'false', 'type': 'xsd:boolean'},
    'ExternalPort': {'value': '0', 'type': 'xsd:unsignedInt'},
    'InternalPort': {'value': '0', 'type': 'xsd:unsignedInt'},
    'InternalClient': {'value': '', 'type': 'xsd:string'},
    'ExternalPortEndRange': {'value': '0', 'type': 'xsd:unsignedInt'},
    'PortMappingLeaseDuration': {'value': '0', 'type': 'xsd:unsignedInt'},
    'PortMappingDescription': {'value': '', 'type': 'xsd:string'},
}

# Model-specific port mapping parameters.
port_mapping_tp_link_tr098_params = merge(port_mapping_default_params, {
    'X_TP_ExternalPortEnd': {'value': '0', 'type': 'xsd:unsignedInt'},
    'X_TP_InternalPortEnd': {'value': '0', 'type': 'xsd:unsignedInt'},
    'ServiceName': {'value': '', 'type': 'xsd:string'},
})

port_mapping_tp_link_tr181_params = merge(port_mapping_default_params, {
    'PortMappingEnabled': None,
    'PortMappingDescription': None,
    'Enable': {'value': 'false', 'type': 'xsd:boolean'},
    'Protocol': {'value': '', 'type': 'xsd:string'},
    'Alias': {'value': '', 'type': 'xsd:string'},
    'RemoteHost': {'value': '', 'type': 'xsd:string'},
    'Interface': {'value': '', 'type': 'xsd:string'},
})

port_mapping_huawei_params = merge(port_mapping_default_params, {
    'X_HW_InternalEndPort': {'value': '0', 'type': 'xsd:unsignedInt'},
})

port_mapping_multilaser_params = merge(port_mapping_default_params, {
    'X_ZTE-COM_InternalPortEndRange': {'value': '0', 'type': 'xsd:unsignedInt'},
    'RemoteHost': {'value': '', 'type': 'xsd:string'},
})

port_mapping_nokia_params = merge(port_mapping_default_params, {
    'X_ASB_COM_InternalPortEnd': {'value': '0', 'type': 'xsd:unsignedInt'},
    'RemoteHost': {'value': '', 'type': 'xsd:string'},
})

def add_port_mapping(simulator, path, port_mapping_params):
    parent_path = '.'.join(path.split('.')[:-2]) + '.'
    new_index = get_next_index_in_path(simulator, path)
    path += f"{new_index}."

    simulator.device.set(path, [True])
    simulator.device.get(f"{parent_path}PortMappingNumberOfEntries")[1] = str(new_index)

    for key, param in port_mapping_params.items():
        if param is not None:
            simulator.device.set(path + key, [True, param['value'], param['type']])

    return new_index

# Model-specific port mapping AddObject logic functions.
def add_port_mapping_tp_link_tr098(simulator, path):
    return add_port_mapping(simulator, path, port_mapping_tp_link_tr098_params)

def add_port_mapping_tp_link_tr181(simulator, path):
    return add_port_mapping(simulator, path, port_mapping_tp_link_tr181_params)

def add_port_mapping_huawei(simulator, path):
    return add_port_mapping(simulator, path, port_mapping_huawei_params)

def add_port_mapping_multilaser(simulator, path):
    return add_port_mapping(simulator, path, port_mapping_multilaser_params)

def add_port_mapping_nokia(simulator, path):
    return add_port_mapping(simulator, path, port_mapping_nokia_params)

# Standard fields configuration.
standard = {
    'active': {'key': 'Active', 'type': 'xsd:boolean', 'default': 'true', 'valid': is_boolean, 'format': to_string},
    'source': {'key': 'AddressSource', 'type': 'xsd:string', 'default': 'DHCP', 'valid': is_string},
    'name': {'key': 'HostName', 'type': 'xsd:string', 'valid': is_string},
    'mac': {'key': 'MACAddress', 'type': 'xsd:string', 'default': random_mac, 'valid': is_mac_address},
    'ip': {'key': 'IPAddress', 'type': 'xsd:string', 'default': default_ipv4, 'valid': is_ipv4},
    'interface': {'key': 'InterfaceType', 'type': 'xsd:string', 'default': basic_default_interface, 'valid': is_string},
    'leaseTime': {'key': 'LeaseTimeRemaining', 'type': 'xsd:int', 'default': '86207', 'valid': is_positive_number, 'format': to_integer},
    'band': {'key': 'Bandwidth', 'type': 'xsd:string', 'default': '20MHz', 'valid': is_bandwidth, 'format': to_bandwidth},
    'mode': {'key': 'Standard', 'type': 'xsd:string', 'default': basic_default_radio_mode, 'valid': is_mode},
    'rssi': {'key': 'SignalStrength', 'type': 'xsd:int', 'default': '-57', 'valid': is_rssi, 'format': to_integer},
    'snr': {'key': 'SignalNoiseRatio', 'type': 'xsd:int', 'default': '42', 'valid': is_positive_number, 'format': to_integer},
    'rate': {'key': 'LastDataTransmitRate', 'type': 'xsd:unsignedInt', 'default': '144000', 'valid': is_positive_number, 'format': to_integer},
}

# Complete model configurations.
models = {
    '9CA2F4-IGD-22282X5007025': {  # tplink EC220-G5 V2
        'hosts': {
            'path': 'InternetGatewayDevice.LANDevice.1.Hosts.',
            'fields': {
                'active': standard['active'],
                'source': standard['source'],
                'name': standard['name'],
                'mac': standard['mac'],
                'ip': standard['ip'],
                'interface': copy(standard['interface'], {'default': tplink_default_interface}),
                'leaseTime': standard['leaseTime'],
            },
        },
        'associated_device': {
            'path2': 'InternetGatewayDevice.LANDevice.1.WLANConfiguration.1.AssociatedDevice.',
            'path5': 'InternetGatewayDevice.LANDevice.1.WLANConfiguration.2.AssociatedDevice.',
            'fields': {
                'mac': copy(standard['mac'], {'key': 'AssociatedDeviceMACAddress'}),
                'band': copy(standard['band'], {'key': 'X_TP_StaBandWidth', 'default': '20M', 'format': lambda v: f"{v}M"}),
                'mode': copy(standard['mode'], {
                    'key': 'X_TP_StaStandard',
                    'default': lambda land_device: '11' + basic_default_radio_mode(land_device),
                    'format': lambda v: '11' + v,
                }),
                'rssi': copy(standard['rssi'], {'key': 'X_TP_StaSignalStrength', 'type': 'xsd:string'}),
                'rate': copy(standard['rate'], {'key': 'X_TP_StaConnectionSpeed'}),
            },
        },
        'addObject': {
            'InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANIPConnection.1.PortMapping.': add_port_mapping_tp_link_tr098,
        }
    },
    '9CA2F4-EC220%2DG5-22275K2000315': {  # tplink EC220-G5 V3
        'hosts': {
            'path': 'Device.Hosts.',
            'fields': {
                'active': standard['active'],
                'name': standard['name'],
                'ip': standard['ip'],
                'leaseTime': standard['leaseTime'],
                'mac': copy(standard['mac'], {'key': 'PhysAddress'}),
            },
        },
        'associated_device': {
            'path2': 'Device.WiFi.AccessPoint.1.AssociatedDevice.',
            'path5': 'Device.WiFi.AccessPoint.3.AssociatedDevice.',
            'fields': {
                'mac': standard['mac'],
                'band': standard['band'],
                'mode': standard['mode'],
                'rssi': standard['rssi'],
                'rate': copy(standard['rate'], {'key': 'LastDataDownlinkRate'}),
            },
        },
    },
    # (Остальные модели следует добавить сюда)
}

# Экспортируем модель
if __name__ == "__main__":
    pass  # основной код не требуется