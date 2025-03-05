import random
import time
from threading import Timer

class Diagnostics:
    def __init__(self):
        self.diagnostic_duration = 2  # в секундах
        self.diagnostic_queue = []

    def finish(self, simulator, name, func, after_seconds):
        state = simulator.diagnostics_states[name]

        def execute():
            func(simulator)
            state['running'] = None
            state['reject'] = None
            simulator.run_pending_actions(lambda: simulator.start_session("8 DIAGNOSTICS COMPLETE"))
            simulator.emit('diagnostic', name)

        timer = Timer(after_seconds, execute)
        state['running'] = timer
        timer.start()

    def queue(self, simulator, name, func):
        state = simulator.diagnostics_states[name]
        promise = lambda: self.finish(simulator, name, func, self.diagnostic_duration)

        self.diagnostic_queue.append(promise)
        state['reject'] = None  # Сброс reject функции

    def interrupt(self, simulator, name):
        state = simulator.diagnostics_states[name]
        if state['running']:
            state['running'].cancel()
            state['running'] = None
        if state['reject']:
            state['reject'](name)
            state['reject'] = None

    @staticmethod
    def random_mac():
        return ":".join(["{:02X}".format(random.randint(0, 255)) for _ in range(6)])

    @staticmethod
    def random_n(max_value, min_value=1):
        return random.randint(min_value, max_value)

    @staticmethod
    def get_random_from_array(array):
        return random.choice(array)

class Ping(Diagnostics):
    path = {
        'tr098': 'InternetGatewayDevice.IPPingDiagnostics.',
        'tr181': 'Device.IP.Diagnostics.IPPing.',
    }

    def run(self, simulator, modified):
        path = self.path[simulator.TR]

        diagnostics_state = simulator.device.get(path + 'DiagnosticsState')
        if diagnostics_state is None:
            return

        if modified.get(path + 'DiagnosticsState') is None:
            # Проверяем изменения в параметрах
            if any(modified.get(path + param) is not None for param in [
                'Interface', 'Host', 'Timeout', 'NumberOfRepetitions', 'DataBlockSize', 'DSCP'
            ]):
                self.interrupt(simulator, 'ping')
                simulator.device.get(path + 'DiagnosticsState')[1] = 'None'
            return

        if diagnostics_state[1] != 'Requested':
            return

        self.interrupt(simulator, 'ping')

        host = simulator.device.get(path + 'Host')[1]
        if not host or len(host) > 256:
            self.queue(simulator, 'ping', lambda s: simulator.device.get(path + 'DiagnosticsState')[1] = 'Error_CannotResolveHostName')
            return

        parameters = {
            'interface': simulator.device.get(path + 'Interface')[1] or '',
            'timeout': int(simulator.device.get(path + 'Timeout')[1] or 1000),
            'number_of_repetitions': int(simulator.device.get(path + 'NumberOfRepetitions')[1] or 1),
            'data_block_size': int(simulator.device.get(path + 'DataBlockSize')[1] or 1),
            'dscp': int(simulator.device.get(path + 'DSCP')[1] or 0),
        }

        if any([
            len(parameters['interface']) > 256,
            parameters['timeout'] < 1,
            parameters['number_of_repetitions'] < 1,
            parameters['data_block_size'] < 1 or parameters['data_block_size'] > 65535,
            parameters['dscp'] < 0 or parameters['dscp'] > 63,
        ]):
            self.queue(simulator, 'ping', lambda s: simulator.device.get(path + 'DiagnosticsState')[1] = 'Error_Other')
            return
        
        self.queue(simulator, 'ping', self.results()['default'], self.diagnostic_duration)

    def results(self):
        return {
            'default': lambda simulator: self._set_ping_success(simulator),
            'error': lambda simulator, error_name='Error_Internal': self._set_ping_error(simulator, error_name),
        }

    def _set_ping_success(self, simulator):
        path = self.path[simulator.TR]
        simulator.device.get(path + 'DiagnosticsState')[1] = 'Complete'
        simulator.device.get(path + 'SuccessCount')[1] = simulator.device.get(path + 'NumberOfRepetitions')[1]
        simulator.device.get(path + 'FailureCount')[1] = '0'
        simulator.device.get(path + 'AverageResponseTime')[1] = '11'
        simulator.device.get(path + 'MinimumResponseTime')[1] = '9'
        simulator.device.get(path + 'MaximumResponseTime')[1] = '14'
    
    def _set_ping_error(self, simulator, error_name):
        path = self.path[simulator.TR]
        simulator.device.get(path + 'DiagnosticsState')[1] = error_name

# Аналогично создайте классы для Traceroute, SiteSurvey и SpeedTest с аналогичным шаблоном

class Traceroute(Diagnostics):
    path = {
        'tr098': 'InternetGatewayDevice.TraceRouteDiagnostics.',
        'tr181': 'Device.IP.Diagnostics.TraceRoute.',
    }

    def run(self, simulator, modified):
        path = self.path[simulator.TR]

        diagnostics_state = simulator.device.get(path + 'DiagnosticsState')
        if diagnostics_state is None:
            return

        if modified.get(path + 'DiagnosticsState') is None:
            if any(modified.get(path + param) is not None for param in [
                'Interface', 'Host', 'NumberOfTries', 'Timeout', 'DataBlockSize', 'MaxHopCount'
            ]):
                self.interrupt(simulator, 'traceroute')
                simulator.device.get(path + 'DiagnosticsState')[1] = 'None'
            return

        if diagnostics_state[1] != 'Requested':
            return

        self.interrupt(simulator, 'traceroute')

        host = simulator.device.get(path + 'Host')[1]
        if not host or len(host) > 256:
            self.queue(simulator, 'traceroute', lambda s: simulator.device.get(path + 'DiagnosticsState')[1] = 'Error_CannotResolveHostName')
            return

        parameters = {
            'interface': simulator.device.get(path + 'Interface')[1] or '',
            'number_of_tries': int(simulator.device.get(path + 'NumberOfTries')[1] or 1),
            'timeout': int(simulator.device.get(path + 'Timeout')[1] or 1000),
            'data_block_size': int(simulator.device.get(path + 'DataBlockSize')[1] or 1),
            'dscp': int(simulator.device.get(path + 'DSCP')[1] or 0),
            'max_hop_count': int(simulator.device.get(path + 'MaxHopCount')[1] or 30),
        }

        if any([
            len(parameters['interface']) > 256,
            parameters['number_of_tries'] < 1 or parameters['number_of_tries'] > 3,
            parameters['timeout'] < 1,
            parameters['data_block_size'] < 1 or parameters['data_block_size'] > 65535,
            parameters['dscp'] < 0 or parameters['dscp'] > 63,
            parameters['max_hop_count'] < 1 or parameters['max_hop_count'] > 64,
        ]):
            self.queue(simulator, 'traceroute', lambda s: simulator.device.get(path + 'DiagnosticsState')[1] = 'Error_MaxHopCountExceeded')
            return

        self.queue(simulator, 'traceroute', self.results()['default'], self.diagnostic_duration)

    def results(self):
        return {
            'default': lambda simulator: self._set_traceroute_success(simulator),
            'error_max_hop_count_exceeded': lambda simulator: self._set_traceroute_error(simulator, 'Error_MaxHopCountExceeded'),
            'error': lambda simulator, error_name='Error_Internal': self._set_traceroute_error(simulator, error_name),
        }

    def _set_traceroute_success(self, simulator):
        path = self.path[simulator.TR]
        # Здесь установите логику успешной трассировки

    def _set_traceroute_error(self, simulator, error_name):
        path = self.path[simulator.TR]
        simulator.device.get(path + 'DiagnosticsState')[1] = error_name

# Экспортируем диагностические тесты
exports = {
    'ping': Ping(),
    'traceroute': Traceroute()
    #SiteSurvey и SpeedTest
}

# Пример использования
if __name__ == "__main__":
    class Simulator:
        def __init__(self):
            self.diagnostics_states = {
                'ping': {'running': None, 'reject': None},
                'traceroute': {'running': None, 'reject': None},
                # Добавьте дополнительные состояния для других диагностик
            }
            self.device = {
                'Device.IP.Diagnostics.IPPing.DiagnosticsState': [False, 'Requested'],
                'Device.IP.Diagnostics.TraceRoute.DiagnosticsState': [False, 'Requested'],
                # .... другие параметры
            }

        def get(self, key):
            return self.device.get(key)

        def set(self, key, value):
            self.device[key] = value

        def emit(self, event, name):
            print(f'Event emitted: {event} for {name}')

        def run_pending_actions(self, action):
            action()  # Исполняем действие

        def start_session(self, message):
            print(f'Starting session: {message}')

    # Пример запуска
    simulator = Simulator()
    # Тестируем ping
    ping_test = exports['ping']
    modified_ping = {
        'Device.IP.Diagnostics.IPPing.DiagnosticsState': 'Requested',
        'Device.IP.Diagnostics.IPPing.Host': ['example.com']
    }
    ping_test.run(simulator, modified_ping)

    # Тестируем traceroute
    traceroute_test = exports['traceroute']
    modified_traceroute = {
        'Device.IP.Diagnostics.TraceRoute.DiagnosticsState': 'Requested',
        'Device.IP.Diagnostics.TraceRoute.Host': ['example.com']
    }
    traceroute_test.run(simulator, modified_traceroute)