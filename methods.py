import http.client
import json
from xml_parser import encode_entities
from xml_utils import node
from diagnostics import Diagnostics
from models import models
from datetime import datetime

INFORM_PARAMS = [
    "Device.DeviceInfo.SpecVersion",
    "InternetGatewayDevice.DeviceInfo.SpecVersion",
    "Device.DeviceInfo.HardwareVersion",
    "InternetGatewayDevice.DeviceInfo.HardwareVersion",
    "Device.DeviceInfo.SoftwareVersion",
    "InternetGatewayDevice.DeviceInfo.SoftwareVersion",
    "Device.DeviceInfo.ProvisioningCode",
    "InternetGatewayDevice.DeviceInfo.ProvisioningCode",
    "Device.ManagementServer.ParameterKey",
    "InternetGatewayDevice.ManagementServer.ParameterKey",
    "Device.ManagementServer.ConnectionRequestURL",
    "InternetGatewayDevice.ManagementServer.ConnectionRequestURL",
    "Device.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.ExternalIPAddress",
    "InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.1.ExternalIPAddress",
    "Device.WANDevice.1.WANConnectionDevice.1.WANIPConnection.1.ExternalIPAddress",
    "InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANIPConnection.1.ExternalIPAddress",
    "InternetGatewayDevice.LANDevice.1.LANEthernetInterfaceConfig.1.MACAddress"
]

def inform(simulator, event=None):
    device = simulator.device
    manufacturer = ""
    v = device.get("DeviceID.Manufacturer") or device.get("Device.DeviceInfo.Manufacturer") or device.get("InternetGatewayDevice.DeviceInfo.Manufacturer")
    if v:
        manufacturer = node("Manufacturer", {}, encode_entities(v[1]))

    oui = ""
    v = device.get("DeviceID.OUI") or device.get("Device.DeviceInfo.ManufacturerOUI") or device.get("InternetGatewayDevice.DeviceInfo.ManufacturerOUI")
    if v:
        oui = node("OUI", {}, encode_entities(v[1]))

    product_class = ""
    v = device.get("DeviceID.ProductClass") or device.get("Device.DeviceInfo.ProductClass") or device.get("InternetGatewayDevice.DeviceInfo.ProductClass")
    if v:
        product_class = node("ProductClass", {}, encode_entities(v[1]))

    serial_number = ""
    v = device.get("DeviceID.SerialNumber") or device.get("Device.DeviceInfo.SerialNumber") or device.get("InternetGatewayDevice.DeviceInfo.SerialNumber")
    if v:
        serial_number = node("SerialNumber", {}, encode_entities(v[1]))

    mac_addr = ""
    v = device.get("InternetGatewayDevice.LANDevice.1.LANEthernetInterfaceConfig.1.MACAddress")
    if v:
        mac_addr = node("MACAddress", {}, encode_entities(v[1]))

    device_id = node("DeviceId", {}, [manufacturer, oui, product_class, serial_number])
    event_struct = node("EventStruct", {}, [
        node("EventCode", {}, event or "2 PERIODIC"),
        node("CommandKey")
    ])

    event_node = node("Event", {"soap-enc:arrayType": "cwmp:EventStruct[1]"}, event_struct)

    params = []
    for p in INFORM_PARAMS:
        param = device.get(p)
        if param:
            params.append(node("ParameterValueStruct", {}, [
                node("Name", {}, p),
                node("Value", {"xsi:type": param[2]}, encode_entities(param[1]))
            ]))

    parameter_list = node("ParameterList", {
        "soap-enc:arrayType": f"cwmp:ParameterValueStruct[{len(INFORM_PARAMS)}]"
    }, params)

    inform = node("cwmp:Inform", {}, [
        device_id,
        event_node,
        node("MaxEnvelopes", {}, "1"),
        node("CurrentTime", {}, datetime.now().isoformat()),
        node("RetryCount", {}, "0"),
        parameter_list
    ])
    
    return inform

def get_sorted_paths(device):
    if hasattr(device, "_sortedPaths"):
        return device._sortedPaths
    
    ignore = {"DeviceID", "Downloads", "Tags", "Events", "Reboot", "FactoryReset", "VirtualParameters"}
    device._sortedPaths = sorted(p for p in device.keys() if p[0] != "_" and p.split(".")[0] not in ignore)
    return device._sortedPaths

def get_parameter_names(simulator, request):
    device = simulator.device
    parameter_names = get_sorted_paths(device)

    parameter_path = None
    next_level = None
    for c in request.children:
        if c.name == "ParameterPath":
            parameter_path = c.text
        elif c.name == "NextLevel":
            next_level = bool(json.loads(c.text))

    parameter_list = []
    
    if next_level:
        for p in parameter_names:
            if p.startswith(parameter_path) and len(p) > len(parameter_path):
                i = p.find(".", len(parameter_path) + 1)
                if i == -1 or i == len(p) - 1:
                    parameter_list.append(p)
    else:
        for p in parameter_names:
            if p.startswith(parameter_path):
                parameter_list.append(p)

    params = []
    for p in parameter_list:
        params.append(node("ParameterInfoStruct", {}, [
            node("Name", {}, p),
            node("Writable", {}, str(device.get(p)[0]))
        ]))
    
    response = node("cwmp:GetParameterNamesResponse", {}, node("ParameterList", {
        "soap-enc:arrayType": f"cwmp:ParameterInfoStruct[{len(parameter_list)}]"
    }, params))
    
    return response

def get_parameter_values(simulator, request):
    device = simulator.device
    parameter_names = request.children[0].children

    params = []
    for p in parameter_names:
        name = p.text
        _, value, type_ = device.get(name)
        value_struct = node("ParameterValueStruct", {}, [
            node("Name", {}, name),
            node("Value", {"xsi:type": type_}, encode_entities(value))
        ])
        params.append(value_struct)

    response = node("cwmp:GetParameterValuesResponse", {}, node("ParameterList", {
        "soap-enc:arrayType": f"cwmp:ParameterValueStruct[{len(parameter_names)}]"
    }, params))

    return response

def set_parameter_values(simulator, request):
    device = simulator.device
    parameter_values = request.children[0].children

    modified = {}
    for p in parameter_values:
        name = ""
        value = None
        for c in p.children:
            if c.localName == "Name":
                name = c.text
            elif c.localName == "Value":
                value = c

        v = device.get(name)
        v[1] = encode_entities(value.text)
        v[2] = next(attr.value for attr in parse_attrs(value.attrs) if attr.localName == "type")
        modified[name] = True

    for key in diagnostics:
        diagnostics[key].run(simulator, modified)

    response = node("cwmp:SetParameterValuesResponse", {}, node("Status", {}, "0"))
    return response

def add_object(simulator, request):
    device = simulator.device
    object_name = request.children[0].text
    instance_number = None

    device_id = device.get('DeviceID.ID')
    model = models.get(device_id and device_id[1])

    if model and model.addObject and object_name in model.addObject:
        instance_number = model.addObject[object_name](simulator, object_name)
    else:
        instance_number = 1
        while device.has(f"{object_name}{instance_number}."):
            instance_number += 1
        
        device.set(f"{object_name}{instance_number}.", [True])

        default_values = {
            "xsd:boolean": "false",
            "xsd:int": "0",
            "xsd:unsignedInt": "0",
            "xsd:dateTime": "0001-01-01T00:00:00Z"
        }

        for p in get_sorted_paths(device):
            if p.startswith(object_name) and len(p) > len(object_name):
                n = f"{object_name}{instance_number}{p[p.index('.'):]}"
                if not device.has(n):
                    v = device.get(p)
                    device.set(n, [v[0], default_values.get(v[2], ""), v[2]])
    
    response = node("cwmp:AddObjectResponse", {}, [
        node("InstanceNumber", {}, str(instance_number)),
        node("Status", {}, "0")
    ])
    del device._sortedPaths
    return response

def delete_object(simulator, request):
    device = simulator.device
    object_name = request.children[0].text

    keys_to_delete = [p for p in device.keys() if p.startswith(object_name)]
    for key in keys_to_delete:
        device.delete(key)

    response = node("cwmp:DeleteObjectResponse", {}, node("Status", {}, "0"))
    del device._sortedPaths
    return response

def download(simulator, request):
    command_key = None
    url = None
    for c in request.children:
        if c.name == "CommandKey":
            command_key = decode_entities(c.text)
        elif c.name == "URL":
            url = decode_entities(c.text)

    fault_code = "9010"
    fault_string = "Download timeout"

    client = None
    if url.startswith("http://"):
        client = http.client.HTTPConnection
    elif url.startswith("https://"):
        client = http.client.HTTPSConnection

    if client:
        conn = client(url)
        conn.request("GET", "/")
        res = conn.getresponse()
        if res.status == 200:
            fault_code = "0"
            fault_string = ""
        else:
            fault_code = "9016"
            fault_string = f"Unexpected response {res.status}"

        body = res.read()

        try:
            data = json.loads(body.decode('utf-8'))
            if isinstance(data, dict) and "version" in data:
                simulator.device.get("InternetGatewayDevice.DeviceInfo.SoftwareVersion")[1] = data["version"]
        except json.JSONDecodeError:
            print("Error parsing Download body to JSON.")

        # создаем новое событие, ожидая завершения передачи
        # (ждем 2 секунды перед отправкой сообщения о завершении передачи)
        simulator.pending_messages.append(lambda send: send(node("cwmp:TransferComplete", {}, [
            node("CommandKey", {}, command_key),
            node("StartTime", {}, datetime.now().isoformat()),
            node("CompleteTime", {}, datetime.now().isoformat()),
            node("FaultStruct", {}, [
                node("FaultCode", {}, fault_code),
                node("FaultString", {}, encode_entities(fault_string))
            ])
        ])))

    response = node("cwmp:DownloadResponse", {}, [
        node("Status", {}, "1"),
        node("StartTime", {}, "0001-01-01T00:00:00Z"),
        node("CompleteTime", {}, "0001-01-01T00:00:00Z")
    ])

    return response

# Экспорт функций
inform = inform
get_parameter_names = get_parameter_names
get_parameter_values = get_parameter_values
set_parameter_values = set_parameter_values
add_object = add_object
delete_object = delete_object
download = download