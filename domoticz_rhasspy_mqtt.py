#!/usr/bin/env python
#
# Python Plugin for Rhasspy Domoticz integration
#
# Author:  marathon2010
#
#####################################################################
version_script = "1.0.6 (15Jul25)"
#####################################################################
import daemon
import paho.mqtt.client as mqtt
from domoticz_rhasspy_functions import *
#####################################################################
#
# Local functions
#
#####################################################################
def on_connect(mqttClient, userdata, flags, rc, properties):
    # Called when connected to MQTT broker.
    mqttClient.subscribe("hermes/intent/#", qos=1)
    writeLog("Connected MQTT server. Waiting for intent.\n", logDebug)

def on_disconnect(mqttClient, userdata, flags, rc):
    # Called when disconnected from MQTT broker.
    writeLog("Disconnected. Trying to reconnect.", logDebug)
    mqttClient.reconnect()

def on_message(mqttClient, userdata, msg):
    # Called each time a message is received on a subscribed topic.
    nlu_payload = json.loads(msg.payload)
    writeLog ("JSON input: " + str(nlu_payload), logDebug)
    capturedTopic = searchJSON("intent.intentName", nlu_payload)
    writeLog ("Topic captured <" + capturedTopic + ">", logInfo)
        
    if capturedTopic[:len(intentPrefix)].lower() != intentPrefix:
        writeLog("No Domoticz topic " + capturedTopic, logDebug)
    else:
        sentence = processDomoticz (capturedTopic[len(intentPrefix):].lower(), nlu_payload, scriptTypeMQ)
        site_id = nlu_payload["siteId"]
        writeLog ("Sentence to speak on <" + site_id + ">", logDebug)
        mqttClient.publish("hermes/tts/say", json.dumps({"text": sentence, "siteId": site_id}))
    writeLog ("Intent finished processing <" + capturedTopic + "> and waiting new intent.\n", logInfo)
#####################################################################
#
# Preparation
#
#####################################################################
openLog(scriptTypeMQ, version_script)
#####################################################################
#
# Main processing
#
#####################################################################
if processargs():
    mqttClient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttClient.on_connect = on_connect
    mqttClient.on_disconnect = on_disconnect
    mqttClient.on_message = on_message

    # process argument mqttserver, could be for instance localhost:1883 or http://192.168.1.1:1883

    countSplitter = arguments[4].count(':')      # how many : are in the argument of mqttserver  
    argumentsMQTT = arguments[4].split(":",2)    # split arguments in maximum of 3 blocks
    serverMQTT = argumentsMQTT[0]
    if countSplitter > 1:
        serverMQTT = serverMQTT + ":" + argumentsMQTT[1]
        portMQTT = argumentsMQTT[2]
    else:
        portMQTT = argumentsMQTT[1]
    writeLog ("Connecting MQTT server <" + serverMQTT + " via port " + portMQTT + ">", logDebug)
    mqttClient.connect(serverMQTT, int(portMQTT))
    with daemon.DaemonContext():
        mqttClient.loop_forever(0.1)
#####################################################################
#
# Completion
#
#####################################################################
closeLog()





