#!/usr/bin/env python3
import os
import sys
import time
import argparse
from multiprocessing import Process
from src.main import create_simulator, format_xml

def parse_args():
    parser = argparse.ArgumentParser(description="GenieACS Simulator", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-u", "--acs-url", default="http://127.0.0.1:57547/", help="ACS URL to contact")
    parser.add_argument("-m", "--data-model", default="device-00259E-EG8145V5-48575443A94196A5-2023-03-28T154335106Z", help="Data model template")
    parser.add_argument("-p", "--processes", type=int, default=1, help="Number of devices to simulate")
    parser.add_argument("-w", "--wait", type=float, default=1000, help="Waiting period between process spawning")
    parser.add_argument("-s", "--serial", type=int, default=0, help="Base serial number")
    return parser.parse_args()

def validate_url(url):
    if not url.startswith(("http://", "https://")):
        print(f'Invalid ACS URL: "{url}"', file=sys.stderr)
        sys.exit(1)

def worker(env):
    """Worker function for the simulator process."""
    acs_url = env.get("ACS_URL")
    data_model = env.get("DATA_MODEL")
    serial_number = env.get("SERIAL_NUMBER")
    mac_addr = env.get("MAC_ADDR")

    simulator = create_simulator(acs_url, data_model, serial_number, mac_addr, True)

    def print_log(message):
        print(f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}]", message)

    def extract_cwmp_from_xml(xml):
        if not xml:
            return ''
        match = re.search(r'<cwmp:\w+>[^]+(\n\s+)<\/cwmp:\w+>', xml)
        if match:
            return match.group(1) + match.group(0)
        return ''

    def print_xml(prefix, xml, full=False):
        content = full_format_xml(xml) if full else extract_cwmp_from_xml(xml)
        print_log(f"{prefix} '{content}'.")

    simulator.on('error', lambda e: print_log(f"Error: {e}\nExiting...") or sys.exit(1))

    # Simulator event handlers can be uncommented and used as needed
    # simulator.on('requested', lambda request: print_log('RECEIVED REQUEST FROM ACS'))
    # simulator.on('sent', lambda request: print_xml('SENT BODY:', request.body))
    # simulator.on('response', lambda response: print_xml('RECEIVED RESPONSE BODY:', response.body))
    # simulator.on('task', lambda task: print_log(f'PROCESSED task: {task.name}.'))
    # simulator.on('diagnostic', lambda name: print_log(f'FINISHED diagnostic: "{name}".'))
    # simulator.on('sessionStart', lambda event: print_log(f'started SESSION with event: "{event}".'))
    # simulator.on('sessionEnd', lambda event: print_log(f'finished SESSION for event: "{event}".'))

    try:
        simulator.start()
    except Exception as e:
        print_log(f"Error starting simulator: {e}")
        sys.exit(1)

def main():
    args = parse_args()
    validate_url(args.acs_url)

    base_mac = int(os.getenv('GENIEACS_SIM_BASE_MAC_ADDRESS', 281474959933440))

    processes = []
    for i in range(args.processes):
        used_mac = hex(base_mac)[2:].zfill(12).upper()
        used_mac = ':'.join(used_mac[i:i+2] for i in range(0, len(used_mac), 2))

        env = {
            "MAC_ADDR": used_mac,
            "SERIAL_NUMBER": f"{args.serial+i:06}",
            "ACS_URL": args.acs_url,
            "DATA_MODEL": args.data_model,
        }

        process = Process(target=worker, args=(env,))
        processes.append(process)
        process.start()
        
        print(f"Simulator {env['SERIAL_NUMBER']} started")
        time.sleep(args.wait / 1000)  # Convert milliseconds to seconds

    for process in processes:
        process.join()  # Wait for all processes to finish

if __name__ == "__main__":
    main()