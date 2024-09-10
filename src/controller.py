import paho.mqtt.client as mqtt
import json
import threading
import math
import numpy as np
import random


class TemperatureController:
    """Controls heating based on temperature readings and target settings using MQTT for communication."""
    def __init__(self, target_temperature, broken_heaters, stop_time):
        """Initializes the temperature controller with target settings and operational parameters."""
        self.target_temperature = target_temperature
        self.broken_heaters = broken_heaters
        self.stop_time = stop_time
        self.current_temperatures = {**{f'Z{i}': 15 for i in range(1, 4)}, **{f'T{i}': 0 for i in 'ABCD'}}
        self.temperature_history = {zone: [] for zone in self.current_temperatures}
        self.heater_status = {f'Z{i}': 0 for i in range(1, 4)}
        self.time_history = []
        self.adjustment_mode = 'advanced'  # Default mode
        self.environment_temperature = 15
        self.comparison_temperatures = {**{f'Z{i}': 15 for i in range(1, 4)}, **{f'T{i}': 0 for i in 'ABCD'}}
        self.zone_sensor_map = {
            'Z1': ('TA', 'TB'),
            'Z2': ('TB', 'TC'),
            'Z3': ('TC', 'TD')
        }
        self.predicted_temperatures_history = [{'TA': 0, 'TB': 0, 'TC': 0, 'TD': 0} ]
        # constants for the _real_ system
        self.capacity = {'Z1': 1e6, 'Z2': 1e6, 'Z3': 1e6}
        self.heat_transfer_external = {'Z1': 1000, 'Z2': 500, 'Z3': 1042}
        self.heat_transfer_zones = {
            'Z1': {'Z2': 500},
            'Z2': {'Z1': 500, 'Z3': 500},
            'Z3': {'Z2': 500}
        }
        # constants for the controller simulation
        self.capacity_controller_simulation = {'Z1': 1e6, 'Z2': 1e6, 'Z3': 1e6}
        self.heat_transfer_external_controller_simulation = {'Z1': 1000, 'Z2': 500, 'Z3': 1042}
        self.heat_transfer_zones_controller_simulation = {
            'Z1': {'Z2': 500},
            'Z2': {'Z1': 500, 'Z3': 500},
            'Z3': {'Z2': 500}
        }
        self.RMSE = 0

    def set_adjustment_mode(self, mode):
        """Sets the heating adjustment mode."""
        valid_modes = ['simple', 'advanced']
        if mode in valid_modes:
            self.adjustment_mode = mode
        else:
            raise ValueError(f"Invalid mode. Available modes are: {valid_modes}")

    def on_connect(self, client, userdata, flags, rc):
        """Handles MQTT connection setup."""
        print(f"Connected with result code {rc}")
        client.subscribe("simulation/temperatures")
        self.send_initial_request(client)

    def on_message(self, client, userdata, msg):
        """Processes incoming MQTT messages with temperature data."""
        data = json.loads(msg.payload.decode())
        environment_temp = data.pop('environment')
        self.environment_temperature.append(environment_temp)

        for key, temp in data.items():
            if key in self.current_temperatures:
                self.current_temperatures[key] = temp
                self.temperature_history[key].append(temp)

        self.time_history.append(len(self.time_history) * DELTA_T)

         # adjust the heater status based on the current mode
        getattr(self, f'adjust_heater_status_{self.adjustment_mode}')(client)

        if len(self.time_history) * DELTA_T >= self.stop_time:
            client.disconnect()

    def send_initial_request(self, client):
        """Sends an initial request to set all heaters off."""
        self.publish_heater_status(client, {zone: 0 for zone in self.heater_status})

    def adjust_heater_status_simple(self, client):
        """Adjusts heater status based on simple average calculations of neighboring sensors."""
        zone_sensor_map = {
            'Z1': ('TA', 'TB'), 'Z2': ('TB', 'TC'), 'Z3': ('TC', 'TD')
        }
        for zone, (sensor1, sensor2) in zone_sensor_map.items():
            if all(sensor in self.current_temperatures for sensor in (sensor1, sensor2)):
                avg_temp = (self.current_temperatures[sensor1] + self.current_temperatures[sensor2]) / 2
                self.heater_status[zone] = 10000 if avg_temp < self.target_temperature else 0
            # If a heater is broken, set the heater status to 0 from the time of fault
            if zone in self.broken_heaters and len(self.time_history) * DELTA_T >= self.broken_heaters[zone]:
                self.heater_status[zone] = 0
        temperatures = self.real_system(client)
        for key, temp in temperatures.items():
            if key in self.current_temperatures:
                self.current_temperatures[key] = temp
                self.temperature_history[key].append(temp)
        self.environment_temperature = temperatures['environment']
        self.time_history.append(len(self.time_history) * DELTA_T)

    def adjust_heater_status_advanced(self, client):
        # Get the predicted temperatures without heating
        # self.heater_status = {zone: 0 for zone in self.heater_status}
        predicted_temperatures = self.predict_heater_effects(client)  # Get the predicted temperatures

        # Use the class attribute for sensor-zone mapping and predicted temperatures
        for zone, (sensor1, sensor2) in self.zone_sensor_map.items():
            if sensor1 in predicted_temperatures and sensor2 in predicted_temperatures:
                average_temp = (predicted_temperatures[sensor1] + predicted_temperatures[sensor2]) / 2
                self.heater_status[zone] = 10000 if average_temp < self.target_temperature else 0
        
        predicted_temperatures = self.predict_heater_effects(client)  # Get the predicted temperatures with new heater settings
        real_temperatures = self.real_system(client)

        for key, temp in real_temperatures.items():
            if key in self.comparison_temperatures:
                self.comparison_temperatures[key] = temp

        # compare the predicted temperatures with the actual temperatures to adjust the constants if necessary; 
        rmse = math.sqrt(sum((real_temperatures[sensor] - predicted_temperatures[sensor]) ** 2 for sensor in ['TA', 'TB', 'TC', 'TD']) / 4)

        if rmse < 10: # filter out unrealistic RMSE values
            self.RMSE = rmse

        print(f"RMSE: {rmse:.2f}")
        if rmse > 0.45 and rmse < 10:
            print("RMSE is too high, updating constants for the controller simulation")
            # print the latest predictions
            for sensor in ['TA', 'TB', 'TC', 'TD']:
                print(f"prediction for {sensor}: {predicted_temperatures[sensor]}, actual: {self.current_temperatures[sensor]}")
            # use the gradient descent function to update the constants
            new_constants = self.gradient_descent(client)
            self.capacity_controller_simulation = new_constants['capacity']
            self.heat_transfer_external_controller_simulation = new_constants['heat_transfer_external']
            self.heat_transfer_zones_controller_simulation = new_constants['heat_transfer_zones']
        
        
        self.predicted_temperatures_history.append(predicted_temperatures)
        for key, temp in real_temperatures.items():
            if key in self.current_temperatures:
                self.current_temperatures[key] = temp
                self.temperature_history[key].append(temp)
        self.environment_temperature = real_temperatures['environment']
        self.time_history.append(len(self.time_history) * DELTA_T)
       
        if True:
            # add parameter drift to real system (simulation) with a random factor betwenen 1 and 1.1
            for zone in self.heat_transfer_external:
                self.heat_transfer_external[zone] = self.heat_transfer_external[zone] * (1 + random.random() * 0.1)
                # print(f"Heat transfer external for {zone}: {self.heat_transfer_external[zone]}")
        

    def compare_predictions_with_actuals(self, client):
        """Compares predicted temperatures with actual temperatures."""
        # get a new prediction
        predicted_temperatures = self.predict_heater_effects(client, timestep = -2)
        # calculate the RMSE
        rmse = math.sqrt(sum((self.current_temperatures[sensor] - predicted_temperatures[sensor]) ** 2 for sensor in ['TA', 'TB', 'TC', 'TD']) / 4)
        # print the RMSE rounded to 2 decimal places 
        print(f"RMSE: {rmse:.2f}")
    
        # if the RMSE is too high, the constants for the controller simulation need to be updated
        if rmse > 0.45 and rmse < 10:
            print("RMSE is too high, updating constants for the controller simulation")
            # print the latest predictions
            for sensor in ['TA', 'TB', 'TC', 'TD']:
                print(f"prediction for {sensor}: {predicted_temperatures[sensor]}, actual: {self.current_temperatures[sensor]}")
            # use the gradient descent function to update the constants
            new_constants = self.gradient_descent(client)
            self.capacity_controller_simulation = new_constants['capacity']
            self.heat_transfer_external_controller_simulation = new_constants['heat_transfer_external']
            self.heat_transfer_zones_controller_simulation = new_constants['heat_transfer_zones']
        if rmse < 10: # filter out unrealistic RMSE values
            self.RMSE = rmse

    def predict_heater_effects(self, client):
        # Initialize the event
        self.prediction_event = threading.Event()

        # Message to be sent; the constants are flexible, and can diverge from reality, so they need to be resynced sometimes
        message = {
            'heater_status': self.heater_status,
            'current_temperatures': self.current_temperatures,
            'delta_t': DELTA_T,
            'capacity': self.capacity_controller_simulation,
            'heat_transfer_external': self.heat_transfer_external_controller_simulation,
            'heat_transfer_zones': self.heat_transfer_zones_controller_simulation
        }        
        
        response_data = {}
        def on_message(client, userdata, msg):
            nonlocal response_data
            try:
                response_data = json.loads(msg.payload.decode())
                self.prediction_event.set()
            except Exception as e:
                print(f"Error processing reply: {e}")

        client = mqtt.Client()
        client.on_message = on_message
        client.connect("localhost", 1883, 60)
        client.subscribe('controller_simulation/temperatures')
        client.loop_start()
        client.publish("controller/heater_simulation", json.dumps(message))

        self.prediction_event.wait(timeout=10)
        client.loop_stop()
        client.disconnect()
        return response_data

    def real_system(self, client):
        # Initialize the event
        self.prediction_event = threading.Event()

        # Message to be sent; the constants are flexible, and can diverge from reality, so they need to be resynced sometimes
        message = {
            'heater_status': self.heater_status,
            'current_temperatures': self.current_temperatures,
            'delta_t': DELTA_T,
            'capacity': self.capacity,
            'heat_transfer_external': self.heat_transfer_external,
            'heat_transfer_zones': self.heat_transfer_zones,
            'RMSE': self.RMSE,
            'Simulated Temperature Sensor A': self.predicted_temperatures_history[-1]['TA'],
            'Simulated Temperature Sensor B': self.predicted_temperatures_history[-1]['TB'],
            'Simulated Temperature Sensor C': self.predicted_temperatures_history[-1]['TC'],
            'Simulated Temperature Sensor D': self.predicted_temperatures_history[-1]['TD'],
            'environment': self.environment_temperature
        }       
        
        response_data = {}
        def on_message(client, userdata, msg):
            nonlocal response_data
            try:
                response_data = json.loads(msg.payload.decode())
                self.prediction_event.set()
            except Exception as e:
                print(f"Error processing reply: {e}")

        client = mqtt.Client()
        client.on_message = on_message
        client.connect("localhost", 1883, 60)
        client.subscribe('simulation/temperatures')
        client.loop_start()
        client.publish("controller/heater_status", json.dumps(message))

        self.prediction_event.wait(timeout=10)
        client.loop_stop()
        client.disconnect()
        return response_data

    def on_disconnect(self, client, userdata, rc):
        """Handles MQTT disconnection."""
        print(f"Disconnected with result code {rc}")

    def gradient_descent(self, client):
        params = {
            'capacity': self.capacity_controller_simulation,
            'heat_transfer_external': self.heat_transfer_external_controller_simulation,
            'heat_transfer_zones': self.heat_transfer_zones_controller_simulation
        }
        learning_rate = 200
        predicted_temperatures = self.predicted_temperatures_history[-1]

        for iteration in range(5):
            # new simulation
            predicted_temperatures = self.predict_heater_effects(client)
            # self.predicted_temperatures_history.append(predicted_temperatures)

            # Calculate the RMSE and print it rounded to 2 decimal places
            rmse = math.sqrt(sum((self.comparison_temperatures[sensor] - predicted_temperatures[sensor]) ** 2 for sensor in ['TA', 'TB', 'TC', 'TD']) / 4)
            
            print(f"Iteration {iteration}: RMSE = {rmse:.2f}")

            # Check if the target temperature is close enough
            if abs(rmse) < 0.4:
                print(f"Target temperature reached within tolerance.")
                break

           # for each parameter find out, if the error shrinks if increased or decreased or left unchanged
            for param_type in params:
                for zone in params[param_type]:
                    original_value = params[param_type][zone]
                    
                    if isinstance(original_value, dict):
                        # If the value is a dictionary (like for heat_transfer_zones), handle each sub_zone individually
                        for sub_zone in original_value:
                            original_sub_value = original_value[sub_zone]
                            best_sub_value = original_sub_value
                            best_rmse = rmse

                            for change in [-1, 0, 1]:
                                # Adjust sub_zone value
                                params[param_type][zone][sub_zone] = original_sub_value + learning_rate * change
                                if params[param_type][zone][sub_zone] < 0:
                                    params[param_type][zone][sub_zone] = 0
                                params['heat_transfer_zones'][zone][sub_zone] = params[param_type][zone][sub_zone]

                                # Predict temperatures and calculate the RMSE
                                predicted_temperature = self.predict_heater_effects(client)
                                # only use temperature sensors
                                new_rmse = math.sqrt(sum((self.comparison_temperatures[sensor] - predicted_temperatures[sensor]) ** 2 for sensor in ['TA', 'TB', 'TC', 'TD']) / 4)

                                if new_rmse < best_rmse:
                                    best_sub_value = params[param_type][zone][sub_zone]
                                    best_rmse = new_rmse
                                else:
                                    # Revert to the original sub_zone value
                                    params[param_type][zone][sub_zone] = original_sub_value

                            # Update the best sub_zone value in the controller simulation
                            params['heat_transfer_zones'][zone][sub_zone] = best_sub_value

                    else:
                        # For non-dict values (like capacity and heat_transfer_external), handle as usual
                        best_value = original_value
                        best_rmse = rmse

                        for change in [-1, 0, 1]:
                            params[param_type][zone] = original_value + learning_rate * change
                            # check if the value is still positive
                            if params[param_type][zone] < 0:
                                params[param_type][zone] = 0

                            if param_type == 'capacity':
                                params['capacity'][zone] = params[param_type][zone]
                            elif param_type == 'heat_transfer_external':
                                params['heat_transfer_external'][zone] = params[param_type][zone]

                            # Predict temperatures and calculate the RMSE
                            predicted_temperatures = self.predict_heater_effects(client)
                            # only use temperature sensors
                            new_rmse = math.sqrt(sum((self.comparison_temperatures[sensor] - predicted_temperatures[sensor]) ** 2 for sensor in ['TA', 'TB', 'TC', 'TD']) / 4)

                            if new_rmse < best_rmse:
                                best_value = params[param_type][zone]
                                best_rmse = new_rmse
                            else:
                                # Revert to the original value
                                params[param_type][zone] = original_value

                        # Update the best value in the controller simulation
                        if param_type == 'capacity':
                            params['capacity'][zone] = best_value
                        elif param_type == 'heat_transfer_external':
                            params['heat_transfer_external'][zone] = best_value
            
                        # adaptive learning rate
            
            learning_rate = learning_rate * 0.75

        return params

    def deep_copy_params(self, params):
        return {key: {k: v for k, v in value.items()} for key, value in params.items()}

# Configuration and main execution
TARGET_TEMPERATURE = 20
BROKEN_HEATERS = {} # {'Z1': 1500}
STOP_TIME = 5000
DELTA_T = 200

client = mqtt.Client()
controller = TemperatureController(TARGET_TEMPERATURE, BROKEN_HEATERS, STOP_TIME)
controller.set_adjustment_mode('advanced') # simple or advanced

for i in range(STOP_TIME // DELTA_T):
    # if the controller mode is advanced, the advanced adjustment function needs to be called
    if controller.adjustment_mode == 'advanced':
        controller.adjust_heater_status_advanced(client)
    else:
        controller.adjust_heater_status_simple(client)
print('end')
client.disconnect()
