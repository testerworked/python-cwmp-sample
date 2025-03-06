import asyncio
import random

event = '8 DIAGNOSTICS COMPLETE'
diagnostic_duration = 2  # in seconds

async def finish(simulator, name, func, after_seconds, resolve):
    state = simulator.diagnostics_states[name]

    await asyncio.sleep(after_seconds)
    await func(simulator)
    state.running = None
    state.reject = None

    await simulator.run_pending_actions()
    await simulator.start_session(event)
    await resolve(name)
    simulator.emit('diagnostic', name)

async def queue(simulator, name, func, after_seconds):
    async def inner(resolve, reject):
        simulator.diagnostics_states[name].reject = reject
        await finish(simulator, name, func, after_seconds, resolve)

    simulator.diagnostic_queue.append(lambda: asyncio.create_task(inner()))

async def interrupt(simulator, name):
    state = simulator.diagnostics_states[name]
    if state.running:
        state.running.cancel()
    if state.reject:
        state.reject(name)
        state.reject = None
    state.running = None

# Helper functions
def random_mac():
    return ":".join(["{:02X}".format(random.randint(0, 255)) for _ in range(6)])

def random_n(max_val, min_val=1):
    return random.randint(min_val, max_val)

def get_random_from_array(array):
    return random.choice(array)

# Ping Diagnostic
class Ping:
    path = {
        'tr098': 'InternetGatewayDevice.IPPingDiagnostics.',
        'tr181': 'Device.IP.Diagnostics.IPPing.',
    }

    async def run(self, simulator, modified):
        path = self.path[simulator.TR]

        if modified.get(path + 'DiagnosticsState') is None:
            if (modified.get(path + 'Interface') is not None or
                    modified.get(path + 'Host') is not None or
                    modified.get(path + 'Timeout') is not None or
                    modified.get(path + 'NumberOfRepetitions') is not None or
                    modified.get(path + 'DataBlockSize') is not None or
                    modified.get(path + 'DSCP') is not None):
                
                await interrupt(simulator, 'ping')
                simulator.device.get(path + 'DiagnosticsState')[1] = 'None'
            return
        
        if simulator.device.get(path + 'DiagnosticsState')[1] != 'Requested':
            return

        # ... Логика пинга продолжается ...
        
        host = simulator.device.get(path + 'Host')[1]
        if not host or len(host) > 256:
            await queue(simulator, 'ping', lambda s: setattr(s.device.get(path + 'DiagnosticsState'), 1, 'Error_CannotResolveHostName'), diagnostic_duration)
            return

        interface = (simulator.device.get(path + 'Interface') or ['', ''])[1]
        timeout = int((simulator.device.get(path + 'Timeout') or [None, 1000])[1])
        NumberOfRepetitions = int((simulator.device.get(path + 'NumberOfRepetitions') or [None, 1])[1])
        dataBlockSize = int((simulator.device.get(path + 'DataBlockSize') or [None, 1])[1])
        dscp = int((simulator.device.get(path + 'DSCP') or [None, 0])[1])

        if (len(interface) > 256 or
                timeout < 1 or 
                NumberOfRepetitions < 1 or 
                dataBlockSize < 1 or 
                dataBlockSize > 65535 or 
                dscp < 0 or 
                dscp > 63):
            await queue(simulator, 'ping', lambda s: setattr(s.device.get(path + 'DiagnosticsState'), 1, 'Error_Other'), diagnostic_duration)
            return
        
        await queue(simulator, 'ping', self.results['default'], diagnostic_duration)

    async def default_result(self, simulator):
        path = self.path[simulator.TR]
        simulator.device.get(path + 'DiagnosticsState')[1] = 'Complete'
        simulator.device.get(path + 'SuccessCount')[1] = simulator.device.get(path + 'NumberOfRepetitions')[1]
        simulator.device.get(path + 'FailureCount')[1] = '0'
        simulator.device.get(path + 'AverageResponseTime')[1] = '11'
        simulator.device.get(path + 'MinimumResponseTime')[1] = '9'
        simulator.device.get(path + 'MaximumResponseTime')[1] = '14'

    async def error_result(self, simulator, error_name='Error_Internal'):
        path = self.path[simulator.TR]
        simulator.device.get(path + 'DiagnosticsState')[1] = error_name

ping = Ping()

# Traceroute Diagnostic
class Traceroute:
    path = {
        'tr098': 'InternetGatewayDevice.TraceRouteDiagnostics.',
        'tr181': 'Device.IP.Diagnostics.TraceRoute.',
    }

    async def run(self, simulator, modified):
        path = self.path[simulator.TR]
        
        if modified.get(path + 'DiagnosticsState') is None:
            if (modified.get(path + 'Interface') is not None or
                    modified.get(path + 'Host') is not None or
                    modified.get(path + 'NumberOfTries') is not None or
                    modified.get(path + 'Timeout') is not None or
                    modified.get(path + 'DataBlockSize') is not None or
                    modified.get(path + 'MaxHopCount') is not None):
                
                await interrupt(simulator, 'traceroute')
                simulator.device.get(path + 'DiagnosticsState')[1] = 'None'
            return

        if simulator.device.get(path + 'DiagnosticsState')[1] != 'Requested':
            return
        
        await interrupt(simulator, 'traceroute')
        
        host = simulator.device.get(path + 'Host')[1]
        if not host or len(host) > 256:
            await queue(simulator, 'traceroute', lambda s: setattr(s.device.get(path + 'DiagnosticsState'), 1, 'Error_CannotResolveHostName'), diagnostic_duration)
            return
        
        interface = (simulator.device.get(path + 'Interface') or ['', ''])[1]
        number_of_tries = int((simulator.device.get(path + 'NumberOfTries') or [None, 1])[1])
        timeout = int((simulator.device.get(path + 'Timeout') or [None, 1000])[1])
        data_block_size = int((simulator.device.get(path + 'DataBlockSize') or [None, 1])[1])
        dscp = int((simulator.device.get(path + 'DSCP') or [None, 0])[1])
        max_hop_count = int((simulator.device.get(path + 'MaxHopCount') or [None, 30])[1])
        
        if (len(interface) > 256 or
                number_of_tries < 1 or 
                number_of_tries > 3 or 
                timeout < 1 or 
                data_block_size < 1 or 
                data_block_size > 65535 or 
                dscp < 0 or 
                dscp > 63 or 
                max_hop_count < 1 or 
                max_hop_count > 64):
            await queue(simulator, 'traceroute', lambda s: setattr(s.device.get(path + 'DiagnosticsState'), 1, 'Error_MaxHopCountExceeded'), diagnostic_duration)
            return

        await queue(simulator, 'traceroute', self.results['default'], diagnostic_duration)

    async def default_result(self, simulator):
        path = self.path[simulator.TR]
        await self.produce_hop_results(simulator, path, False, 8)

    async def produce_hop_results(self, simulator, path, forced_max_hops_error=False, amount_of_hops=8):
        # Логика генерации результатов маршрута...
        pass

traceroute = Traceroute()

# Sitesurvey Diagnostic
class SiteSurvey:
    path = {
        'tr181': 'Device.WiFi.NeighboringWiFiDiagnostic.',
    }

    async def run(self, simulator, modified):
        path = self.path[simulator.TR]
        if modified.get(path + 'DiagnosticsState') is None:
            return
        
        field = simulator.device.get(path + 'DiagnosticsState')
        if not field:
            return

        if field[1] != 'Requested':
            return
        
        await interrupt(simulator, 'sitesurvey')
        await queue(simulator, 'sitesurvey', self.results['default'], diagnostic_duration)

    async def default_result(self, simulator):
        path = self.path[simulator.TR]
        # Логика проведения обследования...
        pass

sitesurvey = SiteSurvey()

# Speedtest Diagnostic
class SpeedTest:
    path = {
        'tr098': 'InternetGatewayDevice.DownloadDiagnostics.',
        'tr181': 'Device.IP.Diagnostics.DownloadDiagnostics.',
    }

    async def run(self, simulator, modified):
        path = self.path[simulator.TR]

        if modified.get(path + 'DiagnosticsState') is None:
            if (modified.get(path + 'Interface') is not None or
                    modified.get(path + 'DownloadURL') is not None or
                    modified.get(path + 'DSCP') is not None or
                    modified.get(path + 'EthernetPriority') is not None or
                    modified.get(path + 'TimeBasedTestDuration') is not None or
                    modified.get(path + 'TimeBasedTestMeasurementInterval') is not None or
                    modified.get(path + 'TimeBasedTestMeasurementOffset') is not None or
                    modified.get(path + 'NumberOfConnections') is not None or
                    modified.get(path + 'EnablePerConnectionResults') is not None):
                
                await interrupt(simulator, 'speedtest')
                simulator.device.get(path + 'DiagnosticsState')[1] = 'None'
            return
        
        if simulator.device.get(path + 'DiagnosticsState')[1] != 'Requested':
            return
        
        await interrupt(simulator, 'speedtest')

        download_url = simulator.device.get(path + 'DownloadURL')[1]
        if not download_url or len(download_url) > 2048:
            await queue(simulator, 'speedtest', lambda s: setattr(s.device.get(path + 'DiagnosticsState'), 1, 'Error_CannotResolveHostName'), diagnostic_duration)
            return
        
        # ... Остальная логика...
        
        await queue(simulator, 'speedtest', self.results['default'], diagnostic_duration)

    async def default_result(self, simulator):
        path = self.path[simulator.TR]
        simulator.device.get(path + 'DiagnosticsState')[1] = 'Complete'
        # ... Логика обработки результата...
        pass

speedtest = SpeedTest()

# Здесь можно добавить экспорт или использование созданных классов.