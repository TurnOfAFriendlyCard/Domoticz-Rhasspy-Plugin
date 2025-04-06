#!/usr/bin/env python
#
# Python Plugin for Rhasspy Domoticz integration - generic variables and constants
#
# Author:  marathon2010
# Version: 0.1.12 (30 March 2025)
#
#####################################################################
import os
import sys
#####################################################################
arguments     = []            # input arguments to the program
argumentsText = ["server", "credentials", "language", "mqttserver"]       # fixed text in arguments line for validations
argdebug      = "--debug"     # debug argument on local command line rhasspy
intentPrefix  = "dz"          # fixed prefix for intents to process in Domoticz
logDebug      = "DEBUG"       # show logmessage as debug  
logError      = "ERROR"       # show logmessage as error
logInfo       = "INFO"        # show logmessage as info
logStatus     = "STATUS"      # show logmessage as status
logFileName   = "/domoticz_rhasspy.log"
# scriptType is 1) LocalCommand or 2) MQTT defined in calling script.
# LocalCommand implies script called from Intent Handling in Rhasspy, so JSON file communication
# MQTT implies script running and monitoring MQTT puplished messahes from Rhasspy
scriptTypeLC  = "LocalCommand"
scriptTypeMQ  = "MQTT"
pathnameLC    = sys.argv[0][:sys.argv[0].rfind("/")] 
pathnameMQ    = os.getcwd()
tagListJSON = {
  "device" : {
    scriptTypeLC : "slots.device",
    scriptTypeMQ : "slots[0].value.value"
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
resultJSON = {
  "barometer"      : "result[].Barometer",
  "data"           : "result[].Data",
  "forecaststr"    : "result[].ForecastStr",
  "humidity"       : "result[].Humidity",
  "humiditystatus" : "result[].HumidityStatus",
  "subtype"        : "result[].SubType",
  "temp"           : "result[].Temp",
  "type"           : "result[].Type",
}
specificTranslation = {
  "op"      : "aan",
}
domoAPIbase   = "/json.htm?type=command&param="
# what domoticz types and subtypes are validated to be processed (use lower characters).
# all types/subtypes are listed, not yet validated is prefix with an ~.    
domoTypes         = ["lighting 2", "temp", "~humidity", "temp + humidity", "temp + humidity + baro",    # 0..4
                     "~rain", "~wind", "~uv", "~current", "~scale",                                     # 5..9
                     "~counter", "~color switch", "setpoint", "general", "light/switch",                # 10..14
                     "~lux", "~temp+baro", "~usage", "~air quality", "p1 smart meter"                   # 15..19
                    ]
domoSubTypes      = ["", "lacrosse tx3", "wtgr800", "thb1 - bthr918", "bthgn129",                            # 0..4
                     "thb2 - bthr918n", "bthr968", "weather station", "~weight", "setpoint",                 # 5..9
                     "~visibility", "~solar radiation", "~soil moisture", "~leaf wetness", "~percentage",    # 10..14
                     "~fan", "~voltage", "~pressure", "~kwh", "~waterflow",                                  # 15..19
                     "~custom sensor", "~managed counter", "text", "~alert", "~ampere (1 phase)",            # 20..24
                     "~sound le vel", "~barometer", "~distance", "~counter incremental", "selector switch",  # 25..29
                     "switch", "~lux", "~electric", "~energy", "gas",                                        # 30..34
                     "thgn122/123/132, thgr122/228/238/268"                                                  # 35..36
                    ]
#####################################################################