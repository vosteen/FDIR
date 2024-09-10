import paho.mqtt.client as mqtt
import json

# MQTT settings
BROKER = "localhost"
TOPIC_HEATER_STATUS = "controller/heater_status"

# Global variables to store the latest messages
temperature_history = {
    'TA': [],
    'TB': [],
    'TC': [],
    'TD': []
}

alert_threshold = 42

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(TOPIC_HEATER_STATUS)

def on_message(client, userdata, msg):
    if msg.topic == TOPIC_HEATER_STATUS:
        message = json.loads(msg.payload.decode())
        temperatures = message.get('current_temperatures', {})
    
        # Process the alert condition
        if temperatures:
            process_alert(client, temperatures)

def process_alert(client, temperatures):
    global temperature_history

    problematic_sensors = []

    # Update temperature history
    for zone, temp in temperatures.items():
        if zone in temperature_history:
            temperature_history[zone].append(temp)
        
            # Maintain a fixed history length
            if len(temperature_history[zone]) > alert_threshold:
                temperature_history[zone].pop(0)

            # Check if the last `alert_threshold` values all indicate a problem
            if len(temperature_history[zone]) >= alert_threshold:
                rising_slowly = temperature_history[zone][-1] < (1.001**alert_threshold)*temperature_history[zone][-alert_threshold]
                if all(t < 19.5 for t in temperature_history[zone][-alert_threshold:]) and rising_slowly:
                    problematic_sensors.append(zone)

    print("problematic sensor values:", problematic_sensors)
    
    if problematic_sensors:
        publish_alert(client, problematic_sensors)

def publish_alert(client, problematic_sensors):
    alert_message = {"alert": True, "problematic_sensors": problematic_sensors}
    client.publish("monitor/alert", json.dumps(alert_message))

# Main function
def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, 1883, 60)
    
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        client.disconnect()

if __name__ == "__main__":
    main()
