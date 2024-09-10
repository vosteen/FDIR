import paho.mqtt.client as mqtt

# MQTT Broker Adresse
broker_address = "localhost"  # Ersetze dies mit der Adresse deines MQTT Brokers
port = 1883  # Der Standardport für MQTT

# Diese Funktion wird aufgerufen, wenn die Verbindung zum Broker hergestellt wird
def on_connect(client, userdata, flags, rc):
    print("Verbunden mit Code: " + str(rc))
    # Abonnieren der gewünschten Topics
    client.subscribe("controller/heater_status")
    client.subscribe("controller/heater_simulation")

# Diese Funktion wird aufgerufen, wenn eine Nachricht auf einem abonnierten Topic empfangen wird
def on_message(client, userdata, msg):
    print(f"Nachricht empfangen auf Topic {msg.topic}: {msg.payload.decode()}")

# MQTT Client erstellen
client = mqtt.Client("HeaterStatusSubscriber")
client.on_connect = on_connect
client.on_message = on_message

# Verbindung zum Broker herstellen
client.connect(broker_address, port=port)

# Endlosschleife, um auf Nachrichten zu warten und den Client am Laufen zu halten
client.loop_forever()
