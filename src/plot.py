import paho.mqtt.client as mqtt
import json
import matplotlib.pyplot as plt
import numpy as np

# MQTT settings
BROKER = "localhost"
TOPIC_TEMPERATURES = "controller/heater_status"
TOPIC_ALERT = "monitor/alert"
TOPIC_SIMULATION_ERROR = "controller/heater_status"

# Data storage
temperature_history = {
    'Temperature Sensor A': [],
    'Temperature Sensor B': [],
    'Temperature Sensor C': [],
    'Temperature Sensor D': [],
    'Zone 1': [],
    'Zone 2': [],
    'Zone 3': [],
    'RMSE': [],
    'Simulated Temperature Sensor A': [],
    'Simulated Temperature Sensor B': [],
    'Simulated Temperature Sensor C': [],
    'Simulated Temperature Sensor D': [],
    'Environment': []
}
time_history = []
alerts = []
delta_t = 10

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe([(TOPIC_TEMPERATURES, 0), (TOPIC_ALERT, 0), (TOPIC_SIMULATION_ERROR, 0)])
def on_message(client, userdata, msg):
    global temperature_history, environment_temperature, time_history, alerts

    # Nachricht dekodieren
    message = json.loads(msg.payload.decode())
    
    # Überprüfung des Nachrichtenthemas
    if msg.topic == TOPIC_TEMPERATURES:
        # Umgebungstemperatur extrahieren

        temperature_history['Environment'].append(message.get('environment', np.nan))
        
        # Temperaturhistorie der vier Sensoren aktualisieren
        temperature_history['Temperature Sensor A'].append(message.get('current_temperatures', {}).get('TA', np.nan))
        temperature_history['Temperature Sensor B'].append(message.get('current_temperatures', {}).get('TB', np.nan))
        temperature_history['Temperature Sensor C'].append(message.get('current_temperatures', {}).get('TC', np.nan))
        temperature_history['Temperature Sensor D'].append(message.get('current_temperatures', {}).get('TD', np.nan))

        # Temperaturhistorie der Zonen aktualisieren
        temperature_history['Zone 1'].append(message.get('current_temperatures', {}).get('Z1', np.nan))
        temperature_history['Zone 2'].append(message.get('current_temperatures', {}).get('Z2', np.nan))
        temperature_history['Zone 3'].append(message.get('current_temperatures', {}).get('Z3', np.nan))

        # Zeitschrittgröße aktualisieren
        delta_t = message.get('delta_t')
        time_history.append(len(time_history) * delta_t)

        # RMSE-Wert drucken und speichern
        print(message.get('RMSE', np.nan))
        temperature_history['RMSE'].append(message.get('RMSE', np.nan))

        # Simulierte Temperaturen speichern
        temperature_history['Simulated Temperature Sensor A'].append(message.get('Simulated Temperature Sensor A', np.nan))
        temperature_history['Simulated Temperature Sensor B'].append(message.get('Simulated Temperature Sensor B', np.nan))
        temperature_history['Simulated Temperature Sensor C'].append(message.get('Simulated Temperature Sensor C', np.nan))
        temperature_history['Simulated Temperature Sensor D'].append(message.get('Simulated Temperature Sensor D', np.nan))

    elif msg.topic == TOPIC_ALERT:
        alert_time = len(time_history) * DELTA_T
        problematic_zones = message.get("problematic_sensors", [])
        alerts.append((alert_time, problematic_zones))

def plot_data():
    global temperature_history, time_history, alerts

    fig, ax1 = plt.subplots(figsize=(12, 8))

    # Generate time history based on the length of the temperature history and delta_t
    time_steps = np.array(time_history)

    # Plot temperature data
    ax1.plot(time_steps, temperature_history['Environment'], label="Environment", linestyle=':')
    ax1.set_xlabel("Time (seconds)")
    ax1.set_ylabel("Temperature (°C)")
    #ax1.plot(time_steps, temperature_history['Zone 1'], label='Zone 1')
    #ax1.plot(time_steps, temperature_history['Zone 2'], label='Zone 2')
    #ax1.plot(time_steps, temperature_history['Zone 3'], label='Zone 3')
    
    # Define a professional color palette
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

    # Plot simulated temperatures as dots only and keep the colour the same as the real sensors 
    ax1.plot(time_steps, temperature_history['Simulated Temperature Sensor A'], label='Simulated Temperature Sensor A', marker='o', linestyle='None', color=colors[0])
    ax1.plot(time_steps, temperature_history['Simulated Temperature Sensor B'], label='Simulated Temperature Sensor B', marker='o', linestyle='None', color=colors[1])
    ax1.plot(time_steps, temperature_history['Simulated Temperature Sensor C'], label='Simulated Temperature Sensor C', marker='o', linestyle='None', color=colors[2])
    ax1.plot(time_steps, temperature_history['Simulated Temperature Sensor D'], label='Simulated Temperature Sensor D', marker='o', linestyle='None', color=colors[3])

    ax1.plot(time_steps, temperature_history['Temperature Sensor A'], label='Temperature Sensor A', color=colors[0])
    ax1.plot(time_steps, temperature_history['Temperature Sensor B'], label='Temperature Sensor B', color=colors[1])
    ax1.plot(time_steps, temperature_history['Temperature Sensor C'], label='Temperature Sensor C', color=colors[2])
    ax1.plot(time_steps, temperature_history['Temperature Sensor D'], label='Temperature Sensor D', color=colors[3])

    # Plot RMSE with separate y-axis 
    ax2 = ax1.twinx()
    ax2.plot(time_steps, temperature_history['RMSE'], label='Root Mean Square Error', color='black')
    ax2.set_ylabel("Simulation Error")
    # add a line for the RMSE threshold of 0.45
    ax2.axhline(y=0.45, color='black', linestyle='--', label='RMSE Threshold')

    # add a combined legend for both ax1 and ax2
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='lower right')


    # Plot alerts as background colors
    #for alert_time, zones in alerts:
    #    for zone in zones:
    #        ax1.axvspan(alert_time - DELTA_T, alert_time, color='red', alpha=0.05)

    #ax1.legend(loc='upper left')
    ax1.grid(True)
    ax1.set_title("Temperature Evolution")# with Alerts")
    ax1.set_xlim(left=0)

    plt.tight_layout()
    plt.show()

# Main function
def main():
    global DELTA_T
    DELTA_T = 10  # Set delta_t to match your simulation

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, 1883, 60)

    try:
        client.loop_start()
        while True:
            pass  # Keep the script running to listen for messages
    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()
        plot_data()

if __name__ == "__main__":
    main()
