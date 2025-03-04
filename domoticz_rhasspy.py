#!/usr/bin/env python
#
# Python Plugin for Rhasspy Domoticz integration
#
# Author:  marathon2010
#
import sys
import json
import datetime
import requests
import jmespath
import deepl
#####################################################################
version = "2.1.17 (4 March 2025)"
#####################################################################
#
# Constant values
#
#####################################################################
arguments    = []            # input arguments to the program
argdebug     = "--debug"     # debug argument on local command line rhasspy
emptySearch  = ["none", ""]  # result of jmespath search is empty
logDebug     = "DEBUG"       # show logmessage as debug  
logError     = "ERROR"       # show logmessage as error
logInfo      = "INFO"        # show logmessage as info
logStatus    = "STATUS"      # show logmessage as status
intentPrefix = "dz"          # fixed prefix for intents to process in Domoticz
domoAPIbase  = "/json.htm?type=command&param="
# what domoticz types and subtypes are validated to be processed (use lower characters).
# all types/subtypes are listed, not yet validated is prefix with an ~.    
domoTypes         = ["lighting 2", "temp", "~humidity", "temp + humidity", "temp + humidity + baro",
                     "~rain", "~wind", "~uv", "~current", "~scale",
                     "~counter", "~color switch", "setpoint", "general", "light/switch",
                     "~lux", "~temp+baro", "~usage", "~air quality", "~p1 smart meter"
                    ]
domoSubTypes      = ["", "lacrosse tx3", "wtgr800", "thb1 - bthr918", "bthgn129",
                     "thb2 - bthr918n", "bthr968", "weather station", "~weight", "setpoint", 
                     "~visibility", "~solar radiation", "~soil moisture", "~leaf wetness", "~percentage",
                     "~fan", "~voltage", "~pressure", "~kwh", "~waterflow",
                     "~custom sensor", "~managed counter", "text", "~alert", "~ampere (1 phase)",
                     "~sound level", "~barometer", "~distance", "~counter incremental", "selector switch",
                     "switch", "~lux", "~electric", "~energy", "~gas",
                     "thgn122/123/132, thgr122/228/238/268"
                    ]
#####################################################################
#
# Local functions
#
#####################################################################
def openLog():
    global logfile
    # argument 0 will be something like "/profiles/domoticz/domoticz_rhasspy.py"
    # capture all before last backslash to be pathname for the logfile.
    pathname = sys.argv[0][:sys.argv[0].rfind("/")]
    logfile = open(pathname + "/domoticz_rhasspy.log", "a")
    writeLog ("Domoticz Rhasspy initiated: " + version, logStatus)
    writeLog ("Arguments Path:        " + str(pathname), logInfo)
    arguments.append(pathname)              # 0: pathname of logfile

def closeLog():
    writeLog ("Domoticz Rhasspy completed\n==================", logStatus)
    logfile.close() 

def writeLog (texttolog, logtype):
    # write to local Rhasspy log
    showLogLine = False
    if len(arguments) != 6:  # implies arguments have been not processed yet
        showLogLine = True
    else:
        if arguments[5].lower() == argdebug:     # argument --debug, so show all
            showLogLine = True
        else:
            if logtype != logDebug:              # so only non debug messages to show
                showLogLine = True

    if showLogLine == True:
        curtime = datetime.datetime.now()
        texttolog = str(curtime.strftime("%d"))+"-"+str(curtime.strftime("%b"))+"-"+\
                    str(curtime.strftime("%y"))+" "+str(curtime.strftime("%H"))+":"+\
                    str(curtime.strftime("%M"))+":"+str(curtime.strftime("%S"))+"."+\
                    str(curtime.strftime("%f"))+" - "+str(logtype)+" - "+str(texttolog)+ "\n"
        logfile.write(texttolog)

def readJSON():
    global rhasspyjson
    # get json from stdin and load into python dict
    rhasspyjson = json.loads(sys.stdin.read())
    writeLog ("JSON input: " + str(rhasspyjson), logDebug)

def writeJSON():
    global rhasspyjson
    # convert dict to json and print to stdout, so includig the text to be spoken.
    print(json.dumps(rhasspyjson))
    writeLog ("JSON output: " + str(rhasspyjson), logDebug)

def speech(text):
    global rhasspyjson
    # add text to be spoken by rhasspy to the JSON structure.
    writeLog ("Speech " + str(text), logDebug)
    rhasspyjson["speech"] = {"text": text}

def processargs ():
    def striparguments (argumentid):
        # split arguments in two blocks split by equals sign with single quotes
        splitarguments = sys.argv[argumentid].split("=",1)
        writeLog ("Arguments Split id:    " + str(argumentid) + "= " + str(splitarguments), logInfo)
        return splitarguments[1]

    numberarguments = len(sys.argv)
    writeLog ("Arguments Raw (" + str(numberarguments) + "):     " + str(sys.argv), logInfo)

    arguments.append(striparguments(1))     # 1: server connection
    credentials = str(striparguments(2)).split(":",1)
    writeLog ("Arguments Credentials: " + str(credentials), logInfo)
    arguments.append(credentials[0])        # 2: credentials username
    arguments.append(credentials[1])        # 3: credentials password
    arguments.append(striparguments(3))     # 4: language Rhasspy
    if numberarguments == 5:
        if sys.argv[4].lower() == argdebug:    
            arguments.append(argdebug)      # 5: debug option
        else:
            arguments.append("--nodebug")   # 5: no debug option
    else:
        arguments.append("--nodebug")       # 5: no debug option

    writeLog ("Arguments Clean:       " + str(arguments), logInfo)

def domoRequest(domoParms):
    domoticz_url = str(arguments[1]) + domoAPIbase + domoParms    
    writeLog ("Domoticz API definition: " + str(domoticz_url), logInfo)
    request_response = requests.get(domoticz_url, headers={'Accept': 'application/json'}, auth=(arguments[2], arguments[3]))
    writeLog ("Domoticz API status <" + str(request_response.status_code) + ">", logInfo)
    writeLog ("Domoticz API JSON " + str(request_response.json()), logDebug)
    return request_response

def domoGetIDX(domoticz_device):
    domoticz_idx = 0
    # first try to translate the supplied device name to the value of a user variable
    # so user variables names are logical device names and will containt the actual device names
    domoticz_result = domoRequest("getuservariables")
    if domoticz_result.ok:
        domoticz_usrvar = searchJSON("result[?Name=='" + domoticz_device + "'].Value", domoticz_result.json())
        writeLog ("UsrVar <" + str(domoticz_usrvar) + ">", logDebug)
        if domoticz_usrvar.lower() not in ("none", ""):
            writeLog ("UsrVar Device <" + str(domoticz_device) + ">", logDebug)
            domoticz_device = domoticz_usrvar       
        # determine the IDX of the devicename        
    domoticz_result = domoRequest("devices_list")
    if domoticz_result.ok:    
        domoticz_idx = searchJSON("result[?name=='" + domoticz_device + "'].idx", domoticz_result.json())
        writeLog ("Device IDX <" + str(domoticz_idx) + "> (" + str(domoticz_device) + ")", logDebug)
    return domoticz_idx

def searchJSON(jmessearch, payload):
    foundJSONstring = str(jmespath.search(jmessearch, payload)).strip("[']")
    writeLog("searchJSON <" + foundJSONstring + "> found thru <" + jmessearch + ">", logDebug)
    return foundJSONstring

def translateText (domoLanguage, toLanguage, textToTranslate):
    if domoLanguage == toLanguage:
        textTranslated = textToTranslate.lower()
    else:
        textTranslated = deepl.translate(source_language=domoLanguage, target_language=toLanguage, text=textToTranslate.lower(), formality_tone="informal")
    return textTranslated

def convertDegrees(domoticz_value):
    domoticz_value = domoticz_value.replace(".", " point ") + " degrees"
    return domoticz_value

def convertPercentage(domoticz_value):
    domoticz_value = domoticz_value.split(".", 1)[0] + " percent"
    return domoticz_value

def convertPressure(domoticz_value):
    domoticz_value = domoticz_value.split(".", 1)[0]
    return domoticz_value

def extractTexts(domoticz_value, payload):
    idsPartialText = searchJSON("slots.speakpartialtext", payload).lower()
    idsPartialText = idsPartialText.split(",")
    # example ["6", "7"] bit can also be ["none"] if not supplied

    if len(idsPartialText) == 1:
        if idsPartialText[0] == "none":
           return domoticz_value

#        if idsPartialText not in emptySearch:

    wordsPartialText = domoticz_value.split()
    # example ["4" "point" "7" "degrees." "humidity" "90" "percent" "means" "Wet"]
    
    writeLog("Partial word id's " + str(idsPartialText), logDebug)
    try:
        if (len(wordsPartialText) - 1) >= int(max(idsPartialText)):     # 8 vs 7
            domoticz_value = ""
            for ids in idsPartialText:
                try:
                    domoticz_value = domoticz_value + " " + wordsPartialText[int(ids)]
                except:
                    writeLog("Partial word id incorrect " + str(ids), logError)
    except:
        writeLog("Partial words ids incorrect (no partial processing)", logError)
    return domoticz_value

def processDomoticz (apiCommand, payload):
    # capture the device delivered from Rhasspy and validate it exists in Domoticz by retrieving the IDX.
### JSON via MQTT (future use)    domoticz_device = searchJSON("slots[0].value.value", payload)
    domoticz_device = searchJSON("slots.device", payload)
    domoticz_IDX = domoGetIDX(domoticz_device)
    if domoticz_IDX == "":
        writeLog ("Device " + domoticz_device + " not found", logError)
        return
    writeLog ("Domoticz API command " + apiCommand + " (" + domoticz_device + ")", logInfo)

    # get language of domoticz
    domoLanguage = "en"   # set domoticz language per default
    domoticz_result = domoRequest("getsettings")
    if domoticz_result.ok:
        domoLanguage = searchJSON("Language", domoticz_result.json())
        writeLog("Domoticz language <" + domoLanguage + "> found", logDebug)

    # validate type and subtype can already be processed by the plugin.
    domoticz_result = domoRequest("getdevices&rid=" + domoticz_IDX)
    if not domoticz_result.ok:
        writeLog ("Device details " + domoticz_device + " not found", logError)
        return
    domoticz_type = searchJSON("result[].Type", domoticz_result.json()).lower()
    domoticz_subtype = searchJSON("result[].SubType", domoticz_result.json()).lower()
    if not (domoticz_type in domoTypes and domoticz_subtype in domoSubTypes):
        writeLog ("Device type / subtype (" + domoticz_type + " / " + domoticz_subtype + ") for device <" + domoticz_device + "> not validated yet", logError)
        return
    writeLog("Domoticz type/subtype validated", logDebug)

    # perform update for switchlight types
    if apiCommand == "switchlight":
### JSON via MQTT (future use)                    domoticz_state = searchJSON("slots[?entity=='state'].value.value", payload)
        domoticz_state = searchJSON("slots.state", payload)
        domoticz_result = domoRequest(apiCommand + "&idx=" + domoticz_IDX + "&switchcmd=" + domoticz_state)
        if not domoticz_result.ok:
            writeLog("Device update " + domoticz_device + " failed", logError)
            return
                
    # perform a getdevices to confirm the actual status of the device after an update request
    # and would be that all intents will result in a getdevices request whatever intent is defined.
    if apiCommand != "getdevices":
        domoticz_result = domoRequest("getdevices&rid=" + domoticz_IDX)
        if not domoticz_result.ok:
            writeLog("Device actual details " + domoticz_device + " not found", logError)
            return

### JSON via MQTT (future use)            toLanguage = searchJSON("lang", payload)
    toLanguage = arguments[4]
    domoticz_value = searchJSON("result[].Data", domoticz_result.json())
    domoticzValueToTranslate = False
    if toLanguage != domoLanguage:          # so state On to translate to local language
        domoticzValueToTranslate = True
    # adjust the captured data so it can be spoken properly
    # temp OR setpoint
    if (domoticz_type == domoTypes[1] or domoticz_type == domoTypes[12]):
        domoticz_value = convertDegrees(searchJSON("result[].Temp", domoticz_result.json()))
        domoticzValueToTranslate = True
    # temp + humidity
    if (domoticz_type == domoTypes[3]):
        temp = convertDegrees(searchJSON("result[].Temp", domoticz_result.json()))
        hum = "humidity " + convertPercentage(searchJSON("result[].Humidity", domoticz_result.json()))
        humstat = searchJSON("result[].HumidityStatus", domoticz_result.json())
        domoticz_value = temp + ". " + hum + " means " + humstat
        domoticz_value = extractTexts(domoticz_value, payload)
        domoticzValueToTranslate = True
    # temp + humidity + baro
    if (domoticz_type == domoTypes[4]):
        temp = convertDegrees(searchJSON("result[].Temp", domoticz_result.json()))
        hum = "humidity " + convertPercentage(searchJSON("result[].Humidity", domoticz_result.json()))
        humstat = searchJSON("result[].HumidityStatus", domoticz_result.json())
        baro = "air pressure " + convertPressure(searchJSON("result[].Barometer", domoticz_result.json()))
        forecast = searchJSON("result[].ForecastStr", domoticz_result.json())
        domoticz_value = temp + ". " + hum + " means " + humstat + ".  " + baro + " and " + forecast
        domoticz_value = extractTexts(domoticz_value, payload)
        domoticzValueToTranslate = True
    # general
    if (domoticz_type == domoTypes[13] and domoticz_subtype == domoSubTypes[22]):
        domoticz_value = extractTexts(domoticz_value, payload)
        domoticzValueToTranslate = False
    writeLog("Domoticz value " + domoticz_value, logDebug)

### JSON via MQTT (future use)        baseSentence = searchJSON("slots[?entity=='speakresponse'].value.value", payload)
    baseSentence = searchJSON("slots.speakresponse", payload)
    if not baseSentence.strip():
        writeLog("No speech feedback defined or omitted", logDebug)
        return

    if not domoticzValueToTranslate:       # is translation required?
        sentence = baseSentence + " " + domoticz_value
    else:
        writeLog("Language from <" + domoLanguage + "> to <" + toLanguage + ">", logDebug)
        domoticz_valueLocal =  translateText (domoLanguage, toLanguage, domoticz_value)
        sentence = baseSentence + " " + domoticz_valueLocal
        writeLog("Translated <" + domoticz_value + "> into <" + domoticz_valueLocal + ">", logDebug)

    speech(sentence)

#####################################################################
#
# Preparation
#
#####################################################################

openLog()
processargs()
readJSON()

#####################################################################
#
# Main processing
#
#####################################################################

capturedTopic = searchJSON("intent.name", rhasspyjson)
writeLog ("Topic captured <" + capturedTopic + ">", logInfo)
        
if capturedTopic[:len(intentPrefix)].lower() != intentPrefix:
    writeLog("No Domoticz topic " + capturedTopic, logDebug)
else:
    processDomoticz (capturedTopic[len(intentPrefix):].lower(), rhasspyjson)

writeLog ("Intent finished processing <" + capturedTopic + ">", logInfo)

#####################################################################
#
# Completion
#
#####################################################################

writeJSON()
closeLog()