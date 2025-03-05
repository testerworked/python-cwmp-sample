import socket
import threading
import base64
import xml.etree.ElementTree as ET
import time
import requests
from xml_utils import create_node
from methods import inform
from diagnostics import diagnostics
from manipulations import some_manipulation_function  # Предположим, что мы реализовали необходимые функции

NAMESPACES = {
    "soap-enc": "http://schemas.xmlsoap.org/soap/encoding/",
    "soap-env": "http://schemas.xmlsoap.org/soap/envelope/",
    "xsd": "http://www.w3.org/2001/XMLSchema",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "cwmp": "urn:dslforum-org:cwmp-1-0"
}

class InvalidTaskNameError(Exception):
    def __init__(self, name, request):
        super().__init__(f'TR-069 Method "{name}" not supported')
        self.request = request

class Simulator:
    def __init__(self, device, serial_number, mac, acs_url='http://127.0.0.1:57547/', verbose=False, periodic_informs_disabled=False):
        self.device = device
        self.serial_number = serial_number
        self.mac = mac
        self.acs_url = acs_url
        self.verbose = verbose
        self.periodic_informs_disabled = periodic_informs_disabled
        self.enabled = False
        self.server = None
        self.diagnostics_states = {key: {} for key in diagnostics}
        self.pending_messages = []
        self.pending_actions = []
        self.next_inform_timeout = None
        self.on_going_session = False
        
        # Инициализация результатов диагностики
        for key in diagnostics:
            self.set_result_for_diagnostic(key)

    def create_soap_document(self, id, body):
        header_node = create_node("soap-env:Header", {}, [
            create_node("cwmp:ID", {"soap-env:mustUnderstand": "1"}, id)
        ])
        body_node = create_node("soap-env:Body", {}, body)
        
        namespaces = {f"xmlns:{prefix}": uri for prefix, uri in NAMESPACES.items()}
        env = create_node("soap-env:Envelope", namespaces, [header_node, body_node])
        
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{env}'

    def create_fault_response(self, code, message):
        fault = create_node("detail", {}, [
            create_node("cwmp:Fault", {}, [
                create_node("FaultCode", {}, str(code)),
                create_node("FaultString", {}, message)
            ])
        ])
        soap_fault = create_node("soap-env:Fault", {}, [
            create_node("faultcode", {}, "Client"),
            create_node("faultstring", {}, "CWMP fault"),
            fault
        ])
        return soap_fault

    def start(self):
        if self.enabled:
            print(f"Simulator {self.serial_number} already started")
            return

        self.enabled = True

        # Настройка серийного номера и MAC-адреса
        # Здесь мы просто устанавливаем значения, но в реальности вы можете использовать какие-то методы устройства
        self.device['DeviceID.SerialNumber'] = self.serial_number
        self.device['Device.DeviceInfo.SerialNumber'] = self.serial_number
        self.device['InternetGatewayDevice.DeviceInfo.SerialNumber'] = self.serial_number
        self.device['InternetGatewayDevice.LANDevice.1.LANEthernetInterfaceConfig.1.MACAddress'] = self.mac

        # Настройка аутентификации
        username = self.device.get("Device.ManagementServer.Username", "")
        password = self.device.get("Device.ManagementServer.Password", "")
        self.basic_auth = f"Basic {base64.b64encode(f'{username}:{password}'.encode()).decode()}"

        threading.Thread(target=self.listen_for_connection_requests).start()

    def listen_for_connection_requests(self):
        # Начнем слушать соединения
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.acs_url.split("//")[1].split(":")[0], int(self.acs_url.split(":")[2])))
            server_socket.listen()
            print(f"Simulator {self.serial_number} is listening for connection requests on {self.acs_url}")

            while True:
                conn, addr = server_socket.accept()
                with conn:
                    print(f"Simulator {self.serial_number} got connection request from {addr}")
                    self.on_going_session = True
                    self.handle_connection()

    def handle_connection(self):
        # здесь вы можете обработать соединение
        time.sleep(1)  # имитация обработки
        self.on_going_session = False

    def send_request(self, content, request_id=None):
        if request_id is None:
            request_id = f"{int(time.time())}"

        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "Authorization": self.basic_auth,
            "Content-Length": str(len(content)),
        }

        response = requests.post(self.acs_url, data=content, headers=headers)
        return self.handle_response(response)

    def handle_response(self, response):
        if response.status_code != 200:
            raise Exception(f"Received response with status code {response.status_code}")

        return ET.fromstring(response.content)

    def set_result_for_diagnostic(self, name, result='default'):
        state = self.diagnostics_states[name]
        state['result'] = diagnostics[name].results[result]

    def run_requested_diagnostics(self):
        pass  # Здесь можно реализовать выполнение диагностики

# Пример использования
if __name__ == "__main__":
    device = {
        "Device.ManagementServer.Username": "admin",
        "Device.ManagementServer.Password": "admin"
    }
    simulator = Simulator(device, "123456", "00:11:22:33:44:55")
    simulator.start()