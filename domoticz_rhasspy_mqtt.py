#!/usr/bin/env python
#
# Python Plugin for Rhasspy Domoticz integration
#
# Author:  marathon2010
#
#####################################################################
version_script = "2.1.1 (4Nov25)"
#####################################################################
import daemon
import paho.mqtt.client as mqtt
from domoticz_rhasspy_functions import *
#####################################################################
#
# Local functions
#
#####################################################################
def askConfirmation(mqttClient, session_id, domoticz_device):
    text = translateText ("do you mean") + " " + domoticz_device
    msg  = {"sessionId": session_id, "text": text, "intentFilter": ["confirmyes", "confirmno"]}
    mqttClient.publish(mqttJSON ["continue"], json.dumps(msg))

def on_connect(mqttClient, userdata, flags, rc, properties):
    # Called when connected to MQTT broker.
    mqttClient.subscribe([(mqttJSON ["intent"] + "/#", 1), (mqttJSON ["dialogue"] + "/#", 1)])
    writeLog("Connected MQTT server. Waiting for intent.\n", logDebug)

def on_disconnect(mqttClient, userdata, flags, rc):
    # Called when disconnected from MQTT broker.
    writeLog("Disconnected. Trying to reconnect.", logDebug)
    mqttClient.reconnect()

def on_message(mqttClient, userdata, msg):
    # Called each time a message is received on a subscribed topic.
    global pending_action
    nlu_payload   = json.loads(msg.payload)
    writeLog ("JSON input: " + str(nlu_payload), logDebug)
    capturedTopic = searchJSON("intent.intentName", nlu_payload)
    session_id    = nlu_payload.get("sessionId", "")
    writeLog ("Topic captured <" + capturedTopic + "> for session <" + session_id + ">", logInfo)
    if capturedTopic[:len(intentPrefix)].lower() == intentPrefix:                                       ### so regular request to Domoticz
        response_status, domoticz_device, domoticz_IDX, domoticz_type, domoticz_subtype, domoticz_result, askForConfirmation = validateDomoticz (nlu_payload, scriptTypeMQ)
        writeLog ("Validate response <" + str(response_status) + ">", logDebug)
        if response_status > 4000:
            site_id = nlu_payload["siteId"]
            mqttClient.publish(mqttJSON ["say"], json.dumps({"text": translateText ("error" + str(response_status)), "siteId": site_id}))
            writeLog ("Intent error <" + capturedTopic + "> and waiting new intent.\n", logError)
            return
        if askForConfirmation == "yes":
            pending_action[session_id] = {"device": domoticz_device, "IDX": domoticz_IDX, "type": domoticz_type, "subtype": domoticz_subtype, "result": domoticz_result, "topic": capturedTopic[len(intentPrefix):].lower(), "payload": nlu_payload}
            writeLog("Asking confirmation session = " + session_id, logDebug)
            askConfirmation(mqttClient, session_id, domoticz_device)
        else:
            sentence = performDomoticz (capturedTopic[len(intentPrefix):].lower(), nlu_payload, scriptTypeMQ, domoticz_device, domoticz_IDX, domoticz_type, domoticz_subtype, domoticz_result)
            site_id = nlu_payload["siteId"]
            writeLog ("Sentence to speak on <" + site_id + ">", logDebug)
            mqttClient.publish(mqttJSON ["say"], json.dumps({"text": sentence, "siteId": site_id}))
    elif capturedTopic == "confirmyes" and session_id in pending_action:                                ### confirm request to process into Domoticz
        domoticz_device  = pending_action[session_id]["device"]
        domoticz_IDX     = pending_action[session_id]["IDX"]
        domoticz_type    = pending_action[session_id]["type"]
        domoticz_subtype = pending_action[session_id]["subtype"]
        domoticz_result  = pending_action[session_id]["result"]
        domoticz_topic   = pending_action[session_id]["topic"]
        nlu_payload      = pending_action[session_id]["payload"]
        sentence = performDomoticz (domoticz_topic, nlu_payload, scriptTypeMQ, domoticz_device, domoticz_IDX, domoticz_type, domoticz_subtype, domoticz_result)
        site_id = nlu_payload["siteId"]
        writeLog ("Sentence to speak on <" + site_id + ">", logDebug)
        mqttClient.publish(mqttJSON ["say"], json.dumps({"text": sentence, "siteId": site_id}))
        writeLog ("End dialogue", logDebug)
        mqttClient.publish(mqttJSON ["end"], json.dumps({"sessionId": session_id}))
        writeLog ("Ended dialogue confirm for  <" + session_id + ">", logDebug)
        del pending_action[session_id]
    elif capturedTopic == "confirmno" and session_id in pending_action:                                 ### cancel request to process into Domoticz
###        text = translateText ("request cancelled for") + " " + domoticz_device
###        site_id = nlu_payload["siteId"]
        mqttClient.publish(mqttJSON ["end"], json.dumps({"sessionId": session_id}))
        writeLog ("Ended dialogue cancel for  <" + session_id + ">", logDebug)
        del pending_action[session_id]
    elif capturedTopic == "askInternet":                                                                ### regular search request
        baseQuestion = searchJSON(tagListJSON ["openquestion"] [scriptTypeMQ], payload)
        writeLog ("Generic question <" + baseQuestion + ">", logDebug)
    else:
        writeLog("No Domoticz topic " + capturedTopic, logDebug)
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





