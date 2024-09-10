from pysat.solvers import Solver
from itertools import combinations
import paho.mqtt.client as mqtt
import json
import threading

DEBUG = False
PRINT_ALL_CLAUSES = False
MONITORED_DEVICES = {'TA+1', 'TB+1', 'TC+1', 'TD+1'}
FAILING_MONITORS = {'TA', 'TC'} 

# Initialisierung des Caches
diagnosis_cache = {}

def get_graph(dtdl_file_path, broker_address="localhost", request_topic="dtdl2graph/request", reply_topic="dtdl2graph/reply", timeout=10):
    with open(dtdl_file_path, 'r') as file:
        dtdl_data = file.read()
    
    message_received_event = threading.Event()
    response_data = {}

    def on_message(client, userdata, msg):
        nonlocal response_data
        try:
            response_data = json.loads(msg.payload.decode())
            message_received_event.set()
        except Exception as e:
            print(f"Error processing reply: {e}")

    client = mqtt.Client()
    client.on_message = on_message
    client.connect(broker_address, 1883, 60)
    client.subscribe(reply_topic)
    client.loop_start()
    client.publish(request_topic, dtdl_data)

    message_received_event.wait(timeout=timeout)
    client.loop_stop()
    client.disconnect()
    return response_data

def get_var(name, var_map):
    if name not in var_map:
        var_map[name] = len(var_map) + 1
    return var_map[name]

def get_name(var, var_map):
    for name, v in var_map.items():
        if v == var:
            return name
    return None

class Component:
    def __init__(self, name):
        self.name = name
        self.faulty = False

    def set_faulty(self, faulty):
        self.faulty = faulty

class TemperatureSensor(Component):
    def read_temperature(self):
        return not self.faulty

class Heater(Component):
    def heat(self):
        return not self.faulty

class HeaterController(Component):
    def control(self):
        return not self.faulty

class Zone(Component):
    def manage_zone(self):
        return not self.faulty

class Monitor:
    def __init__(self, component, expected_function):
        self.component = component
        self.expected_function = expected_function

    def check(self):
        result = self.component.heat()
        expected = self.expected_function()
        return result == expected

class Diagnoser:
    def __init__(self, components):
        self.components = components
        self.var_map = {}
        self.system_description = []
        self.observations = []

    def add_system_description(self, description):
        for clause in description:
            translated_clause = [get_var(lit, self.var_map) if isinstance(lit, str) else lit for lit in clause]
            self.system_description.append(translated_clause)

    def add_observation(self, observation):
        for clause in observation:
            translated_clause = [get_var(lit, self.var_map) if isinstance(lit, str) else lit for lit in clause]
            self.observations.append(translated_clause)

    def diagnose(self):
        diagnoses = []
        all_components = [f'AB({comp.name})' for comp in self.components]

        if self._is_consistent([]):
            diagnoses.append(set())

        for i in range(1, len(all_components) + 1):
            for combo in combinations(all_components, i):
                if self._is_consistent(combo):
                    diagnoses.append(set(combo))

        minimal_diagnoses = self._get_minimal_diagnoses(diagnoses)
        return minimal_diagnoses

    def _is_consistent(self, faulty_components):
        solver = Solver()
        for clause in self.system_description:
            solver.add_clause(clause)

        for clause in self.observations:
            solver.add_clause(clause)

        for comp in self.components:
            if f'AB({comp.name})' in faulty_components:
                solver.add_clause([get_var(f'AB({comp.name})', self.var_map)])
            else:
                solver.add_clause([-get_var(f'AB({comp.name})', self.var_map)])

        result = solver.solve()
        
        if DEBUG and PRINT_ALL_CLAUSES:
            if result:
                print(f"Combination {faulty_components} is consistent.")
            else:
                print(f"Combination {faulty_components} is not consistent.")

        solver.delete()
        return result

    def _get_minimal_diagnoses(self, diagnoses):
        minimal_diagnoses = []
        for diag in diagnoses:
            diag_set = set(diag)
            is_minimal = True
            for other in diagnoses:
                if diag != other:
                    other_set = set(other)
                    if other_set.issubset(diag_set):
                        is_minimal = False
                        break
            if is_minimal:
                minimal_diagnoses.append(diag_set)
        return minimal_diagnoses

    def print_var_map(self):
        print("Variable-to-name mapping (var_map):")
        for name, var in self.var_map.items():
            print(f"{name}: {var}")

    def print_system_description(self):
        print("System Description:")
        for clause in self.system_description:
            print([get_name(var, self.var_map) if var > 0 else f"-{get_name(-var, self.var_map)}" for var in clause])

    def print_observations(self):
        print("Observations:")
        for clause in self.observations:
            print([get_name(var, self.var_map) if var > 0 else f"-{get_name(-var, self.var_map)}" for var in clause])

def indentificator(failing_monitors):
    # Definition der Komponenten
    components = [
        TemperatureSensor('TA'), TemperatureSensor('TB'), TemperatureSensor('TC'), TemperatureSensor('TD'),
        TemperatureSensor('TA+1'), TemperatureSensor('TB+1'), TemperatureSensor('TC+1'), TemperatureSensor('TD+1'), # temperature one minute later
        Heater('H1'), Heater('H2'), Heater('H3'),
        HeaterController('C1'), HeaterController('C2'), HeaterController('C3')
    ]
    
    # Definition der Verbindungen
    connections = {
        'TA+1': ['H1'], # the temperature measure after some time is influenced by the existance of faults (too low temperatures and not rising) in Zone 1 now
        'TB+1': ['H1', 'H2'],
        'TC+1': ['H2', 'H3'],
        'TD+1': ['H3'],
        'C1': ['TA', 'TB'], 
        'C2': ['TB', 'TC'],
        'C3': ['TC', 'TD'],
        'H1': ['C1'],
        'H2': ['C2'],
        'H3': ['C3']
    }
    dtdl_file_path = 'heating_twin.dtdl'
    connections = get_graph(dtdl_file_path)
    
    # todo: sliding window for components; move to next layer (?) 
    updated_connections = {}
    for key, value in connections.items():
        new_key = key + "+1" if key.startswith("T") else key
        updated_connections[new_key] = value

    connections = updated_connections


    diagnoser = Diagnoser(components)
    
    # Erzeugung der Systembeschreibung basierend auf dem Graphen
    system_description = []
    for parent, children in connections.items():
        clause = [get_var(f'output_ok({parent})', diagnoser.var_map), get_var(f'AB({parent})', diagnoser.var_map)]
        for child in children:
            if child in connections:
                clause.append(-get_var(f'output_ok({child})', diagnoser.var_map))
            else:
                clause.append(get_var(f'AB({child})', diagnoser.var_map))
        system_description.append(clause)

    diagnoser.add_system_description(system_description)
    
    observations = []
    # append "+1" on every element in  failing_monitors to get the corresponding temperature sensor 
    failing_monitors = [f'{monitor}+1' for monitor in failing_monitors]
    for failing_monitor in failing_monitors:
        observations.append([-get_var(f'output_ok({failing_monitor})', diagnoser.var_map)])
    
    monitors = []
    for device in MONITORED_DEVICES:
        monitors.append(Monitor(device, lambda: True))
    observations = []
    for i, monitor in enumerate(monitors):
        if monitor.component in failing_monitors:
            observations.append([-get_var(f'output_ok({monitor.component})', diagnoser.var_map)])
        else:
            pass #observations.append([get_var(f'output_ok({monitor.component})', diagnoser.var_map)])
    diagnoser.add_observation(observations)

    # Debug-Informationen ausgeben
    if DEBUG:
        diagnoser.print_var_map()
        diagnoser.print_system_description()
        diagnoser.print_observations()

    diagnoses = diagnoser.diagnose()
    if DEBUG:
        print(f"Minimal Diagnoses: {diagnoses}")
    return [list(diag) for diag in diagnoses]


# MQTT-Einstellungen
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_INPUT = "monitor/alert"
TOPIC_OUTPUT = "diagnosis/output"

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(TOPIC_INPUT)

def on_message(client, userdata, msg):
    if msg.topic == TOPIC_INPUT:
        try:
            data = json.loads(msg.payload.decode())
            if data["alert"]:  # Überprüfen, ob alert true ist
                failing_monitors = data.get("problematic_sensors", [])
                if failing_monitors:
                    # Sortiere die Liste für konsistente Hashwerte
                    failing_monitors_sorted = tuple(sorted(failing_monitors))
                    # Überprüfen, ob das Ergebnis bereits im Cache vorhanden ist
                    if failing_monitors_sorted in diagnosis_cache:
                        diagnosis_results = diagnosis_cache[failing_monitors_sorted]
                    else:
                        # Diagnose durchführen und Ergebnis im Cache speichern
                        diagnosis_results = indentificator(failing_monitors)
                        diagnosis_cache[failing_monitors_sorted] = diagnosis_results
                        # print problematic sensors and diagnosis results
                        print("")
                        print(f"Monitoring results: {failing_monitors}")
                        print(f"Diagnosis results: {diagnosis_results}")

                    send_diagnosis_results(client, diagnosis_results)
                else:
                    # print("No problematic sensor streams reported.")
                    pass
            else:
                print("Alert is false, no diagnosis needed.")
        except Exception as e:
            print(f"Error processing message: {e}")

# Initialisierung des Caches
diagnosis_cache = {}


def send_diagnosis_results(client, diagnosis_results):
    # Umwandeln der Set-Objekte (Diagnoseergebnisse) in Listen
    diagnosis_results_list = [list(result) if isinstance(result, set) else result for result in diagnosis_results]
    message = {
        "diagnosis_results": diagnosis_results_list
    }
    client.publish(TOPIC_OUTPUT, json.dumps(message))


# MQTT Client setup
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# for testing this script
# diagnosis_results = indentificator(FAILING_MONITORS)

# Verbindung zum MQTT Broker
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Schleife starten
client.loop_forever()
