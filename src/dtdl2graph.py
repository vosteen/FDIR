import json
import paho.mqtt.client as mqtt
import config

def extract_mqtt_connections(contents):
    publisher_map = {}
    subscriber_map = {}

    def find_publishers(data):
        def traverse_objects(item, current_name=None):
            if isinstance(item, dict):
                # Update current name if this item is an InstanceComponent
                if item.get('@type') == 'InstanceComponent':
                    current_name = item.get('name', current_name)

                # Check for multiple realizations and store topics for each MQTTPublisher
                realizations = item.get('realization', [])
                if not isinstance(realizations, list):
                    realizations = [realizations]

                for realization in realizations:
                    if realization.get('@type') == 'TelemetryRealizationMQTTPublisher':
                        topic = realization.get('topic')
                        if current_name:
                            if current_name not in publisher_map:
                                publisher_map[current_name] = set()
                            publisher_map[current_name].add(topic)

                # Recursively search within this dictionary
                for value in item.values():
                    traverse_objects(value, current_name)

            elif isinstance(item, list):
                for element in item:
                    traverse_objects(element, current_name)

        # Start traversal from the root
        traverse_objects(data)
        return publisher_map

    def find_subscribers(data):
        def traverse_objects(item, current_name=None):
            if isinstance(item, dict):
                # Update current name if this item is an InstanceComponent
                if item.get('@type') == 'InstanceComponent':
                    current_name = item.get('name', current_name)

                # Check for multiple realizations and store topics for each MQTTSubscriber
                realizations = item.get('realization', [])
                if not isinstance(realizations, list):
                    realizations = [realizations]

                for realization in realizations:
                    if realization.get('@type') == 'TelemetryRealizationMQTTSubscriber':
                        topic = realization.get('topic')
                        if current_name:
                            if current_name not in subscriber_map:
                                subscriber_map[current_name] = set()
                            subscriber_map[current_name].add(topic)

                # Recursively search within this dictionary
                for value in item.values():
                    traverse_objects(value, current_name)

            elif isinstance(item, list):
                for element in item:
                    traverse_objects(element, current_name)

        # Start traversal from the root
        traverse_objects(data)
        return subscriber_map

    def match_publishers_and_subscribers():
        connections = {}
        for subscriber, topics in subscriber_map.items():
            for topic in topics:
                for publisher, publisher_topics in publisher_map.items():
                    if topic in publisher_topics:
                        if subscriber not in connections:
                            connections[subscriber] = []
                        connections[subscriber].append(publisher)
        return connections

    # Execute the find operations
    publisher_map = find_publishers(contents)
    subscriber_map = find_subscribers(contents)
    
    # Match publishers and subscribers based on topics and return the connections
    return match_publishers_and_subscribers()

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        connections = extract_mqtt_connections(data['contents'])
        response = json.dumps(connections)
        client.publish("dtdl2graph/reply", response)
    except Exception as e:
        print(f"Error processing message: {e}")

def main():
    client = mqtt.Client()
    client.on_message = on_message
    client.username_pw_set(config.Mqtt.MQTT_SERVER_USER, config.Mqtt.MQTT_SERVER_PASS)

    client.connect(config.Mqtt.MQTT_SERVER_URL, config.Mqtt.MQTT_SERVER_PORT, 60)
    client.subscribe("dtdl2graph/request")

    client.loop_forever()

if __name__ == "__main__":
    main()
