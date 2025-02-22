# Python Plugin for Rhasspy
#
# Author: marathon2010
# Date:   22 February 2025
#
# Inspired:
# Python Plugin MQTT Examples  Author: Dnpwwo
# Python Plugin neOCampus      Author: Dr Thiebolt F.
#
"""
<plugin key="Rhasspy" name="Rhasspy Voice Assistant" author="marathon2010" version="1.0.141">
    <description>
        <h2>Rhasspy Voice Assistant - v1.0.141</h2>
        This plugin integrates Rhasspy intents with Domoticz devices via MQTT and Domoticz API.<br/>
    </description>
    <params>
        <param field="Address"  label="MQTT IP Address"     width="150px" required="true" default="192.168.1.1"/>
        <param field="Port"     label="MQTT Port"           width="50px"  required="true" default="1883"/>
        <param field="Mode1"    label="Domoticz IP Address" width="150px" required="true" default="192.168.1.1"/>
        <param field="Mode2"    label="Domoticz Port"       width="50px"  required="true" default="8080"/>
        <param field="Mode3"    label="Rhasspy site(s)"     width="150px" required="true" default="sat1,sat2"/>
        <param field="Mode6"    label="Debug"               width="150px" required="true">
            <options>
                <option label="None"              value="0" default="true"/>
                <option label="Python Only"       value="2"/>
                <option label="Basic Debugging"   value="62"/>
                <option label="Basic+Messages"    value="126"/>
                <option label="Queue"             value="128"/>
                <option label="Connections Only"  value="16"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All"               value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""
import DomoticzEx as Domoticz
import json
import requests
import jmespath
import deepl

class BasePlugin:
    enabled           = False

    # constants used in the process
    connClientId      = "rhdzfeb25"                        # MQTT connection client id
    connName          = "RhasspyDomoticz"                  # MQTT connection name
    connPacketId      = "620430"                           # MQTT connection package id, just random id
    connProtocol      = "MQTT"                             # MQTT connection to be setup
    connPublish       = "hermes/tts/say"                   # MQTT topic for Rhasspy to publish to
    connSubscription  = "hermes/intent/#"                  # MQTT topic for Rhasspy to listen to
    
    intentPrefix      = "/dz"                              # fixed prefix for messages to process in Domoticz
    
    domoAPIbase       = "/json.htm?type=command&param="    # API domoticz basis

#   what domoticz types and subtypes are validated to be processed.    
    domoTypesOK       = ["lighting 2", "temp", "setpoint", "general", "light/switch"]   # use lower characters
    domoSubTypesOK    = ["", "lacrosse tx3", "setpoint", "text", "switch"]              # use lower characters
    
    def __init__(self):
        # variables used in the process
        self.connSessionId = ""                    # session id received from Rhasspy
        self.heartBeatCnt  = 0                     # For sending PING command to MQTT every several beats
        self.mqttConn      = None                  # MQTT connection processing

        return

    def onStart(self):
        Domoticz.Log("onStart called")
        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))
        DumpConfigToLog()
        self.mqttConn = Domoticz.Connection(
            Name=self.connName, Transport="TCP/IP", Protocol=self.connProtocol,
            Address=Parameters["Address"], Port=Parameters["Port"]
        )
        self.mqttConn.Connect()

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")
        if (Status == 0):
            Domoticz.Debug("MQTT trying to connect.")
            self.mqttConn.Send({ 'Verb' : 'CONNECT', 'ID' : self.connClientId })
            Domoticz.Log("MQTT connected successfully.")
        else:
            Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+":"+Parameters["Port"]+" with error: "+Description)

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called with: "+Data["Verb"])
        DumpDictionaryToLog(Data)
        
        if Data.get('Verb','').lower() == "pingresp":
            Domoticz.Debug("Ping response received.")
            return

        if Data.get('Verb','').lower() == "connack":
            if Data.get('Status',42) == 0:
                Domoticz.Debug("Connection ACK received.")
                self._connack = True
                Domoticz.Debug("Start subscription to " + self.connSubscription)
                self.mqttConn.Send({'Verb' : 'SUBSCRIBE', 'PacketIdentifier': self.connPacketId, 'Topics': [{'Topic':self.connSubscription, 'QoS': 0}]})
                return
            else:
                Domoticz.Debug("Connection ACK with error code: " + str(Data.get('Status',42)))
                return

        if Data.get('Verb','').lower() == "suback":
            if (Data['Topics'][0])['Status'] == 0:
                Domoticz.Debug("Subscription ACK received.")
                return
            else:
                Domoticz.Debug("Subscribe ACK with errors: " + str(Data))
                return

        if Data.get('Verb','').lower() == "publish":
            Domoticz.Debug("Message received.")
            self.processMQTTmessage( topic=Data['Topic'], payload=json.loads(Data.get('Payload').decode('utf-8')) )
            return

    def onCommand(self, DeviceID, Unit, Command, Level, Color):
        Domoticz.Log("onCommand called for Device " + str(DeviceID) + " Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Log("onHeartbeat called " +str(self.heartBeatCnt))
        if self.mqttConn.Connected() and self.heartBeatCnt % 6 == 0:
            self.mqttConn.Send({'Verb': 'PING'})
        self.heartBeatCnt = (self.heartBeatCnt + 1) % 100000

    def processMQTTmessage( self, topic=None, payload=None ):

        def domoRequest(domoParms):
            domoticz_url = "http://" + str(Parameters["Mode1"]) + ":" + Parameters["Mode2"] + self.domoAPIbase + domoParms    
            Domoticz.Debug("Domoticz API definition: " + str(domoticz_url))
            request_response = requests.get(domoticz_url, headers={'Accept': 'application/json'})
            Domoticz.Debug("Domoticz API status <" + str(request_response.status_code) + ">")
            Domoticz.Debug("Domoticz API JSON " + str(request_response.json()))
            return request_response

        def domoGetIDX(domoticz_device):
            domoticz_result = domoRequest("devices_list")
            domoticz_idx = 0
            if domoticz_result.ok:    
                domoticz_idx = searchJSON("result[?name=='" + domoticz_device + "'].idx", domoticz_result.json())
                Domoticz.Debug("Device IDX <" + str(domoticz_idx) + "> (" + str(domoticz_device) + ")")
            return domoticz_idx

        def searchJSON(jmessearch, payload):
            foundJSONstring = str(jmespath.search(jmessearch, payload)).strip("[']")
            Domoticz.Debug("searchJSON <" + foundJSONstring + "> found thru <" + jmessearch + ">")
            return foundJSONstring

        def translateText (toLanguage, textToTranslate):
            if Settings["Language"] == toLanguage:
                textTranslated = textToTranslate.lower()
            else:
                textTranslated = deepl.translate(source_language=Settings["Language"], target_language=toLanguage, text=textToTranslate.lower())
            return textTranslated

        def processDomoticz (apiCommand, payload):
            Domoticz.Status("Domoticz API command " + apiCommand)
#           capture the device delivered from Rhasspy and validate it exists in Domoticz by retrieving the IDX.
            domoticz_device = searchJSON("slots[?entity=='device'].value.value", payload)
            domoticz_IDX = domoGetIDX(domoticz_device)
            if domoticz_IDX == "":
                Domoticz.Error("Device " + domoticz_device + " not found")
                return

#           validate type and subtype can already be processed by the plugin.
            domoticz_result = domoRequest("getdevices&rid=" + domoticz_IDX)
            if not domoticz_result.ok:
                Domoticz.Error("Device details " + domoticz_device + " not found")
                return
               
            domoticz_type = searchJSON("result[].Type", domoticz_result.json()).lower()
            domoticz_subtype = searchJSON("result[].SubType", domoticz_result.json()).lower()
            if not (domoticz_type in self.domoTypesOK and domoticz_subtype in self.domoSubTypesOK):
                Domoticz.Error("Device type / subtype (" + domoticz_type + " / " + domoticz_subtype + ") for device <" + domoticz_device + "> not validated yet")
                return

            Domoticz.Debug("Domoticz type/subtype validated")
            if apiCommand == "switchlight":
                domoticz_state = searchJSON("slots[?entity=='state'].value.value", payload).capitalize()
                domoticz_result = domoRequest(apiCommand + "&idx=" + domoticz_IDX + "&switchcmd=" + domoticz_state)
                if not domoticz_result.ok:
                    Domoticz.Error("Device update " + domoticz_device + " failed")
                    return
                
#           perform always a getdevices to confirm the actual status of the device and speak out
#           and would be that all intents will result in a getdevices request whatever intent is defined.
            domoticz_result = domoRequest("getdevices&rid=" + domoticz_IDX)
            if not domoticz_result.ok:
                Domoticz.Error("Device actual details " + domoticz_device + " not found")
                return

            toLanguage = searchJSON("lang", payload)
            domoticz_value = searchJSON("result[].Data", domoticz_result.json())
#           adjust the captured data so it can be spoken properly
            if (domoticz_type == "temp" or domoticz_type == "setpoint"):
                domoticz_value = domoticz_value.strip("C").replace(".", " point ") + " degrees"
            if (domoticz_type == "light/switch" and domoticz_subtype == "selector switch"):
                toLanguage = ""
            if (domoticz_type == "General" and domoticz_subtype == "Text"):
                toLanguage = ""
                domoticz_value = " " + domoticz_value
            Domoticz.Debug("Domoticz value " + domoticz_value)

            baseSentence = searchJSON("slots[?entity=='speakresponse'].value.value", payload)
            self.connSessionId = searchJSON("sessionId", payload)
            if not baseSentence.strip():
                Domoticz.Debug("No speech feedback defined or omitted")
                return

            if toLanguage == "":                  # is translation required?
                sentence = baseSentence + domoticz_value
            else:
                Domoticz.Debug("Language from <" + Settings["Language"] + "> to <" + toLanguage + ">")
                domoticz_valueLocal =  translateText (toLanguage, domoticz_value)
                sentence = baseSentence + " " + domoticz_valueLocal
                Domoticz.Debug("Translated <" + domoticz_value + "> into <" + domoticz_valueLocal + ">")
            payloadSpeak = json.dumps({"text": sentence, "siteId": Parameters["Mode3"]})
            Domoticz.Debug("Speech payload " + payloadSpeak)
            self.mqttConn.Send({'Verb' : 'PUBLISH', 'QoS': 1, 'PacketIdentifier': self.connPacketId, 'Topic': self.connPublish, 'Payload': payloadSpeak})

        Domoticz.Log("processMQTTmessage called")
        capturedTopic = topic[topic.rfind("/"):].lower()
        Domoticz.Debug("Topic captured <" + capturedTopic + ">")
        
        if capturedTopic[:len(self.intentPrefix)].lower() != self.intentPrefix:
            Domoticz.Log("No Domoticz topic " + capturedTopic)
        else:
            processDomoticz (capturedTopic[len(self.intentPrefix):].lower(), payload)

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(DeviceID, Unit, Command, Level, Color):
    global _plugin
    _plugin.onCommand(DeviceID, Unit, Command, Level, Color)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for DeviceName in Devices:
        Device = Devices[DeviceName]
        Domoticz.Debug("Device ID:       '" + str(Device.DeviceID) + "'")
        Domoticz.Debug("--->Unit Count:      '" + str(len(Device.Units)) + "'")
        for UnitNo in Device.Units:
            Unit = Device.Units[UnitNo]
            Domoticz.Debug("--->Unit:           " + str(UnitNo))
            Domoticz.Debug("--->Unit Name:     '" + Unit.Name + "'")
            Domoticz.Debug("--->Unit nValue:    " + str(Unit.nValue))
            Domoticz.Debug("--->Unit sValue:   '" + Unit.sValue + "'")
            Domoticz.Debug("--->Unit LastLevel: " + str(Unit.LastLevel))
    return

def DumpDictionaryToLog(theDict, Depth=""):
    if isinstance(theDict, dict):
        for x in theDict:
            if isinstance(theDict[x], dict):
                Domoticz.Debug(Depth+"> Dict '"+x+"' ("+str(len(theDict[x]))+"):")
                DumpDictionaryToLog(theDict[x], Depth+"---")
            elif isinstance(theDict[x], list):
                Domoticz.Debug(Depth+"> List '"+x+"' ("+str(len(theDict[x]))+"):")
                DumpListToLog(theDict[x], Depth+"---")
            elif isinstance(theDict[x], str):
                Domoticz.Debug(Depth+">'" + x + "':'" + str(theDict[x]) + "'")
            else:
                Domoticz.Debug(Depth+">'" + x + "': " + str(theDict[x]))

def DumpListToLog(theList, Depth):
    if isinstance(theList, list):
        for x in theList:
            if isinstance(x, dict):
                Domoticz.Debug(Depth+"> Dict ("+str(len(x))+"):")
                DumpDictionaryToLog(x, Depth+"---")
            elif isinstance(x, list):
                Domoticz.Debug(Depth+"> List ("+str(len(theList))+"):")
                DumpListToLog(x, Depth+"---")
            elif isinstance(x, str):
                Domoticz.Debug(Depth+">'" + x + "':'" + str(theList[x]) + "'")
            else:
                Domoticz.Debug(Depth+">'" + x + "': " + str(theList[x]))