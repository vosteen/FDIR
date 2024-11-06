import paho.mqtt.client as mqtt
import json
import numpy as np
import config

class HeatingSimulation:
    def __init__(self):
        self.delta_t = None
        self.capacity = {}
        self.heat_transfer_external = {}
        self.heat_transfer_zones = {}
        self.zones_neighbors = {}
        self.current_time = 0
        initial_temperature = self.generate_environment_temperature(self.current_time)
        self.temperatures = {'Z1': initial_temperature, 'Z2': initial_temperature, 'Z3': initial_temperature}

    def simulate_step(self, heater_status, current_temps, delta_t):
        new_temps = self.calculate_new_temps(current_temps, heater_status, self.current_time, delta_t)
        self.temperatures.update(new_temps)
        self.publish_temperatures()
        self.current_time += 1
    
    def generate_environment_temperature(self, current_time):
        base_temp = 15
        fluctuation = 2 * np.sin(2 * np.pi * current_time / SIMULATION_DURATION)
        #return base_temp + 2 * (current_time / SIMULATION_DURATION) + fluctuation
        return base_temp

    def calculate_new_temps(self, current_temps, heater_status, current_time, delta_t):
        new_temps = {}
        env_temp = self.generate_environment_temperature(current_time)
        for zone in self.capacity.keys():  # Sicherstellen, dass nur die Zonen verwendet werden, die in der Nachricht enthalten sind
            if zone in current_temps:  # Überprüfen, ob die Zone existiert
                heat_loss = current_temps[zone] * (
                    self.heat_transfer_external[zone] + 
                    sum(self.heat_transfer_zones[zone].get(nbr, 0) for nbr in self.zones_neighbors[zone])
                )
                heat_gain = (
                    self.heat_transfer_external[zone] * env_temp +
                    sum(self.heat_transfer_zones[zone].get(nbr, 0) * current_temps.get(nbr, 0) for nbr in self.zones_neighbors[zone])
                )
                new_temps[zone] = current_temps[zone] + (delta_t / self.capacity[zone]) * (heater_status[zone] + heat_gain - heat_loss)
        return new_temps

    def update_heater_status(self, message):
        status = json.loads(message.payload.decode())
        heater_status = status['heater_status']
        current_temps = status['current_temperatures']
        self.delta_t = status['delta_t']  # Make sure to assign delta_t
        self.capacity = status['capacity']
        self.heat_transfer_external = status['heat_transfer_external']
        self.heat_transfer_zones = status['heat_transfer_zones']
        self.zones_neighbors = {zone: list(self.heat_transfer_zones[zone].keys()) for zone in self.heat_transfer_zones}
        self.simulate_step(heater_status, current_temps, self.delta_t)
        print(status)


    def publish_temperatures(self):
        Z1 = self.temperatures['Z1']
        Z2 = self.temperatures['Z2']
        Z3 = self.temperatures['Z3']
        
        temp_data = {
            'Z1': Z1,
            'Z2': Z2,
            'Z3': Z3,
            'TA': Z1,
            'TB': (Z1 + Z2) / 2,
            #'TB': 25, # Faulty component
            'TC': (Z2 + Z3) / 2,
            'TD': Z3,
            'environment': self.generate_environment_temperature(self.current_time),
            'delta_t': self.delta_t
        }
        
        client.publish("simulation/temperatures", json.dumps(temp_data))

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("controller/heater_status")

def on_message(client, userdata, msg):
    simulation.update_heater_status(msg)

def on_disconnect(client, userdata, rc):
    print("Disconnected with result code " + str(rc))

# Constants and initial settings
SIMULATION_DURATION = 7200  # Use this for calculating environment temperature fluctuation


# MQTT Client setup
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect
client.username_pw_set(config.Mqtt.MQTT_SERVER_USER, config.Mqtt.MQTT_SERVER_PASS)

# Start simulation
simulation = HeatingSimulation()
client.connect(config.Mqtt.MQTT_SERVER_URL, config.Mqtt.MQTT_SERVER_PORT, 60)
client.loop_start()

try:
    while True:
        pass  # Keep the script running to listen for messages
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
