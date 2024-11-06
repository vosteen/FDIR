class Mqtt:
    MQTT_SERVER_URL="localhost"
    MQTT_SERVER_PORT=1883
    MQTT_SERVER_USER=None
    MQTT_SERVER_PASS=None

class Controller:
    ADJUSTMENT_MODE="simple"
    SIM_STOP_TIME=5000
    SIM_DELTA_T=200
    TARGET_TEMP=20
    BROKEN_HEATER_TIMES={'Z1': 1500, 'Z2': 2000}
    
class Model:
    ENVIRONMENT_TEMP=15
    HEAT_CAPACITY={'Z1': 1e6, 'Z2': 1e6, 'Z3': 1e6}
    HEAT_TRANSFER_EXTERNAL={'Z1': 1000, 'Z2': 500, 'Z3': 1042}
    HEAT_TRANSFER_ZONES={
            'Z1': {'Z2': 500},
            'Z2': {'Z1': 500, 'Z3': 500},
            'Z3': {'Z2': 500}
        }