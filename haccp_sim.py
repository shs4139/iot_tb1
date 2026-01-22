import time
import sys
import random
import logging
import threading
try:
    from tb_device_mqtt import TBDeviceMqttClient
except ImportError:
    print("Please install tb-mqtt-client: pip install tb-mqtt-client")
    sys.exit(1)

# Configuration - Change these to match your environment
THINGSBOARD_SERVER = 'demo.thingsboard.io'
ACCESS_TOKEN = 'HACCP_DEVICE_TOKEN_001'

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HACCPCookerSimulation:
    def __init__(self, host, token):
        self.client = TBDeviceMqttClient(host, token)
        self.current_temp = 25.0
        self.target_temp = 100.0
        self.heater_on = False
        self.running = True
        self.mode = "IDLE" # IDLE, HEATING, HOLDING, COOLING

        # Connect
        self.client.connect()
        self.client.subscribe_to_all_attributes(self.attribute_callback)
        self.client.request_attributes(shared_keys=['targetTemp', 'upperLimit', 'lowerLimit'])

    def attribute_callback(self, result, exception=None):
        if exception:
            logging.error("Attribute update error: %s", exception)
        else:
            logging.info("Received attributes: %s", result)
            if 'targetTemp' in result:
                self.target_temp = float(result['targetTemp'])
                logging.info(f"Target Temp updated to: {self.target_temp}")

    def update_physics(self):
        """Simulate temperature change based on heater state."""
        noise = random.uniform(-0.5, 0.5)

        if self.heater_on:
            # Heating up
            if self.current_temp < self.target_temp:
                self.current_temp += (1.5 + noise) # Rise rate
            else:
                # Holding (with some overshoot/undershoot)
                self.current_temp += (random.uniform(-1.0, 1.0))
        else:
            # Cooling down to room temp (25)
            if self.current_temp > 25.0:
                self.current_temp -= (0.5 + noise)

        # Rounding
        self.current_temp = round(self.current_temp, 2)

    def send_telemetry(self):
        telemetry = {
            "temperature": self.current_temp,
            "heaterState": "ON" if self.heater_on else "OFF"
        }
        self.client.send_telemetry(telemetry)
        logging.info(f"Reported: {telemetry}")

    def run(self):
        logging.info("Starting Simulation...")
        logging.info(f"Connecting to {THINGSBOARD_SERVER} with token {ACCESS_TOKEN}")

        # Background thread for input
        input_thread = threading.Thread(target=self.handle_input)
        input_thread.daemon = True
        input_thread.start()

        try:
            while self.running:
                self.update_physics()
                self.send_telemetry()
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def handle_input(self):
        print("\n--- Simulation Controls ---")
        print("1: Turn Heater ON (Heat to Target)")
        print("2: Turn Heater OFF (Cool down)")
        print("3: Simulate OVERHEAT (Jump to Target + 20)")
        print("4: Simulate UNDERHEAT (Drop to Target - 20)")
        print("q: Quit")

        while self.running:
            cmd = input()
            if cmd == '1':
                self.heater_on = True
                logging.info("Heater turned ON")
            elif cmd == '2':
                self.heater_on = False
                logging.info("Heater turned OFF")
            elif cmd == '3':
                self.current_temp = self.target_temp + 20
                logging.info("Simulated SUDDEN HEAT SPIKE")
            elif cmd == '4':
                self.current_temp = self.target_temp - 20
                logging.info("Simulated SUDDEN DROP")
            elif cmd == 'q':
                self.running = False
                self.client.disconnect()

    def stop(self):
        self.running = False
        self.client.disconnect()
        logging.info("Simulation stopped.")

if __name__ == '__main__':
    sim = HACCPCookerSimulation(THINGSBOARD_SERVER, ACCESS_TOKEN)
    sim.run()
