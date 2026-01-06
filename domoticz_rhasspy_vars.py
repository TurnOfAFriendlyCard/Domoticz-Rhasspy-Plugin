#!/usr/bin/env python
#
# Python Plugin for Rhasspy Domoticz integration - generic variables and constants
#
# Author:  marathon2010
#
#####################################################################
version_vars = "1.3.0 (4Nov25)"
#####################################################################
import os
import sys
#####################################################################
# Values may be adjusted by the user
#####################################################################
intentPrefix        = "dz"                                           # fixed prefix for intents to process in Domoticz, should be used in the sentences in Rhasspy like [dzGetDevices]
logFileName         = "/domoticz_rhasspy.log"                        # log where progress can be in capturing and processing intents within Domoticz
translationFileName = "/domoticz_rhasspy_translations.json"          # native texts for Domoticz output (if language Domoticz differs from Rhasspy)
pathnameMQ          = "/opt/domoticz/userdata/scripts/python"        # path to python scripts when running MQTT version.
#####################################################################
# Values are not to be adjusted by the user
#####################################################################
arguments           = []            # input arguments to the program
argumentsText       = ["server", "credentials", "language", "mqttserver"]       # fixed text in arguments line for validations
argdebug            = "--debug"     # debug argument on local command line rhasspy
domoAPIbase         = "/json.htm?type=command&param="
logDebug            = "DEBUG"       # show logmessage as debug  
logError            = "ERROR"       # show logmessage as error
logInfo             = "INFO"        # show logmessage as info
logStatus           = "STATUS"      # show logmessage as status
pending_action      = {}            # used for dialogue processing

# scriptType is 1) LocalCommand or 2) MQTT defined in calling script.
# LocalCommand implies script called from Intent Handling in Rhasspy, so JSON file communication
# MQTT implies script running and monitoring MQTT puplished messahes from Rhasspy
scriptTypeLC        = "LocalCommand"
scriptTypeMQ        = "MQTT"
pathnameLC          = sys.argv[0][:sys.argv[0].rfind("/")] 
###pathnameMQ          = os.getcwd()

tagListJSON = {  # variables that can be used in the sentences, how to retrieve from the slot.
  "askconfirmation" : {
    scriptTypeLC : "slots.askconfirmation",
    scriptTypeMQ : "slots[?entity=='askconfirmation'].value.value"
  },
  "device" : {
    scriptTypeLC : "slots.device",
    scriptTypeMQ : "slots[0].value.value"
  },
  "number" : {
    scriptTypeLC : "slots.rhasspy/number",
    scriptTypeMQ : "slots[?entity=='rhasspy/number'].value.value"
  },
  "openquestion" : {
    scriptTypeLC : "slots.openquestion",
    scriptTypeMQ : "slots[?entity=='openquestion'].value.value"
  },
  "setdomoticzvalue" : {
    scriptTypeLC : "slots.setdomoticzvalue",
    scriptTypeMQ : "slots[?entity=='setdomoticzvalue'].value.value"
  },
  "setpoint" : {
    scriptTypeLC : "slots.setpoint",
    scriptTypeMQ : "slots[?entity=='rhasspy/number'].value.value"
  },
  "speakpartialtext" : {
    scriptTypeLC : "slots.speakpartialtext",
    scriptTypeMQ : "slots[?entity=='speakpartialtext'].value.value"
  },
  "speakresponse" : {
    scriptTypeLC : "slots.speakresponse",
    scriptTypeMQ : "slots[?entity=='speakresponse'].value.value"
  },
  "speakstate" : {
    scriptTypeLC : "slots.speakstate",
    scriptTypeMQ : "slots[?entity=='speakstate'].value.value"
  },
  "state" : {
    scriptTypeLC : "slots.state",
    scriptTypeMQ : "slots[?entity=='state'].value.value"
  },
}

mqttJSON = {       # define the MQTT commands.
  "continue"       : "hermes/dialogueManager/continueSession",
  "dialogue"       : "hermes/dialogueManager",
  "end"            : "hermes/dialogueManager/endSession",
  "intent"         : "hermes/intent",
  "say"            : "hermes/tts/say",
}

resultJSON = {     # define in which part of the Domoticz API JSON structure the value is defined.
  "barometer"      : "result[].Barometer",
  "chill"          : "result[].Chill",
  "data"           : "result[].Data",
  "direction"      : "result[].Direction",
  "directionstr"   : "result[].DirectionStr",
  "forecaststr"    : "result[].ForecastStr",
  "humidity"       : "result[].Humidity",
  "humiditystatus" : "result[].HumidityStatus",
  "secstatus"      : "secstatus",
  "speed"          : "result[].Speed",
  "subtype"        : "result[].SubType",
  "temp"           : "result[].Temp",
  "type"           : "result[].Type",
}
# what domoticz types and subtypes are validated to be processed (use lower characters).
# all known types/subtypes are listed, not yet validated has state False.    

domoTypesJSON = {
  "air quality"            : False,
  "color switch"           : False,
  "counter"                : False,
  "current"                : True,
  "general"                : True,
  "humidity"               : False,
  "light/switch"           : True,
  "lighting 2"             : True,
  "lux"                    : False,
  "p1 smart meter"         : True,
  "rain"                   : False,
  "rfxmeter"               : False,
  "scale"                  : False,
  "security"               : True,
  "setpoint"               : True,
  "temp + humidity + baro" : True,
  "temp + humidity"        : True,
  "temp"                   : True,
  "temp+baro"              : False,
  "usage"                  : True,
  "uv"                     : False,
  "wind"                   : True,
}

domoSubTypesJSON = {
""                                     : True,
"ac"                                   : True,
"alert"                                : False,
"ampere (1 phase)"                     : False,
"barometer"                            : False,
"bthgn129"                             : True,
"bthr968"                              : True,
"cm113, electrisave"                   : True,
"counter incremental"                  : False,
"custom sensor"                        : True,
"distance"                             : False,
"electric"                             : True,
"energy"                               : True,
"fan"                                  : False,
"gas"                                  : True,
"kwh"                                  : True,
"lacrosse tx3"                         : True,
"leaf wetness"                         : False,
"lux"                                  : False,
"managed counter"                      : False,
"percentage"                           : True,
"pressure"                             : True,
"rfxmeter counter"                     : False,
"security panel"                       : True,
"selector switch"                      : True,
"setpoint"                             : True,
"soil moisture"                        : False,
"solar radiation"                      : False,
"sound le vel"                         : False,
"switch"                               : True,
"text"                                 : True,
"thb1 - bthr918"                       : True,
"thb2 - bthr918n"                      : True,
"thgn122/123/132, thgr122/228/238/268" : True,
"tfa"                                  : True,
"visibility"                           : True,
"voltage"                              : True,
"waterflow"                            : True,
"weather station"                      : True,
"weight"                               : False,
"wtgr800"                              : True,
}

#####################################################################