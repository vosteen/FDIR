import paho.mqtt.client as mqtt
import json
import matplotlib.pyplot as plt
import numpy as np
import config

# MQTT settings
TOPIC_HEATING = "controller/heater_status"
TOPIC_ALERT = "monitor/alert"

# Data storage: Ändern Sie die Schlüssel entsprechend den tatsächlichen Bezeichnern aus der MQTT-Nachricht
heating_status = {
    'Z1': [],
    'Z2': [],
    'Z3': []
}
alerts = {sensor: [] for sensor in ['TA', 'TB', 'TC', 'TD']}
time_history = []

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe([(TOPIC_HEATING, 0), (TOPIC_ALERT, 0)])

def on_message(client, userdata, msg):
    global heating_status, alerts, time_history

    message = json.loads(msg.payload.decode())
    if msg.topic == TOPIC_HEATING:
        heater_status = message.get('heater_status', {})
        for zone in ['Z1', 'Z2', 'Z3']:
            if zone in heater_status:
                heating_status[zone].append(heater_status[zone])
            else:
                print(f"Warnung: Kein Heizungsstatus für {zone} verfügbar.")
    elif msg.topic == TOPIC_ALERT:
        alert_time = len(time_history) * message.get('delta_t', 10)
        for sensor in alerts:
            count = message['problematic_sensors'].count(sensor)
            alerts[sensor].append((alert_time, count))
    
    time_history.append(len(time_history) * message.get('delta_t', 10))

# Plot-Funktion anpassen
def plot_data():
    global heating_status, alerts, time_history

    if not time_history:
        print("Keine Zeitdaten verfügbar.")
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    time_steps = np.array(time_history)

    # Set colors for clarity
    colors_heating = ['blue', 'green', 'purple']
    colors_alerts = ['red', 'orange', 'yellow', 'brown']

    # Plot heating status for each zone if data available
    for idx, zone in enumerate(['Z1', 'Z2', 'Z3']):
        if heating_status[zone]:
            ax.plot(time_steps, np.array(heating_status[zone]) + idx * 1.5, label=f"Heating {zone}", marker='o', color=colors_heating[idx])
        else:
            print(f"Keine Heizungsdaten für {zone} verfügbar.")

    # Plot alerts for each sensor if data available
    for idx, sensor in enumerate(['TA', 'TB', 'TC', 'TD']):
        sensor_alerts = np.array([(alert[0], alert[1]) for alert in alerts[sensor] if alert[1] > 0])
        if sensor_alerts.size > 0:
            ax.scatter(sensor_alerts[:, 0], np.ones(sensor_alerts.shape[0]) * (4.5 + idx * 0.5), label=f"Alert {sensor}", marker='x', color=colors_alerts[idx])

    ax.set_xlabel("Time (seconds)")
    ax.set_yticks([0, 1.5, 3, 4.5, 6, 7.5, 9])
    ax.set_yticklabels(['Heating Z1', 'Heating Z2', 'Heating Z3', 'Alert TA', 'Alert TB', 'Alert TC', 'Alert TD'])
    ax.legend(loc='upper left')
    ax.grid(True)
    ax.set_title("Heating and Alert Status")

    plt.tight_layout()
    plt.show()


# Main function
def main():
    global DELTA_T
    DELTA_T = config.Controller.SIM_DELTA_T

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(config.Mqtt.MQTT_SERVER_USER, config.Mqtt.MQTT_SERVER_PASS)

    client.connect(config.Mqtt.MQTT_SERVER_URL, config.Mqtt.MQTT_SERVER_PORT, 60)

    try:
        client.loop_start()
        input("Press Enter to stop and plot...\n")  # Wait for user to stop the loop
        client.loop_stop()
        client.disconnect()
        plot_data()
    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
