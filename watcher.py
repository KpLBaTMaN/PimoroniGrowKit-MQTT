import time
import json
import yaml
import ltr559
import sys, os, pathlib
from grow.moisture import Moisture
import paho.mqtt.client as mqtt
import logging




def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    print(client.subscribe(broker().get('topic')))


def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))


def load_config():

    pathlib.Path(__file__).parent.absolute()
    with open(os.path.join(pathlib.Path(__file__).parent.absolute(), 'config.yaml')) as f:
        return yaml.load(f)


def broker_method():
    return load_config().get('broker')


def auth_method():
    return load_config().get('auth')

def log_method():
    return load_config().get('logging')

config = load_config()
broker = broker_method()
auth = auth_method()
log = log_method()


logging.basicConfig(
    filename=log.get('filepath'), 
    level=logging.DEBUG,
    format='%(asctime)s - %(message)s', 
    datefmt='%d-%b-%y %H:%M:%S'
)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(auth.get('username'), auth.get('password'))
client.connect(broker.get('host', 'homeassistant.local'), broker.get('port', 1883), 60)

print("Start submitting sensor data on MQTT topic {}".format(broker.get('topic')))

sensors = [Moisture(1), Moisture(2), Moisture(3)]
light = ltr559.LTR559()

while True:
    try:
        payload = {"light": light.get_lux()}
        for i in range(len(sensors)):
            payload["sensor_{}".format(i)] = {
                "moisture": sensors[i].moisture,
                "saturation": sensors[i].saturation
            }

        client.publish(broker.get('topic'), json.dumps(payload))
        print(json.dumps(payload))

    except Exception as e:
        logging.error(f"Error in sensor data collection or MQTT publishing: {e}", exc_info=True)

    time.sleep(30)

client.loop_forever()