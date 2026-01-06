#!/usr/bin/env python
#
# Python Plugin for Rhasspy Domoticz integration - generic functions
#
# Author:  marathon2010
#
import json
import sys
import datetime
import requests
import jmespath
from domoticz_rhasspy_vars import *
#####################################################################
version = "3.4.28 (28Nov25)"
#####################################################################
#
# Global functions
#
#####################################################################
def openLog(scriptType, version_script):
    global logfile, pathname, specificTranslation
    if scriptType == scriptTypeLC:
        pathname = pathnameLC
    else:
        pathname = pathnameMQ
    try:
        logfile = open(pathname + logFileName, "a")
    except FileNotFoundError:    
        logfile = open(pathname + logFileName, "w")
    writeLog ("Domoticz Rhasspy initiated: Functions=v" + version + " / Vars=v" + version_vars + " / Script=v" + version_script, logStatus)
    writeLog ("Arguments Path:        " + str(pathname), logInfo)
    arguments.append(pathname)              # 0: pathname of logfile

    try:
        with open(pathname + translationFileName, 'r') as jsonFile:
            specificTranslation = json.load(jsonFile)
            writeLog ("Translations " + str(specificTranslation), logDebug)
    except FileNotFoundError:
        writeLog ("Translations JSON file not found", logError)
        specificTranslation = []
    except json.JSONDecodeError as e:
        writeLog ("Translations JSON decode error: {}".format(e), logError)
        specificTranslation = []

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
        with open(pathname + logFileName, "a") as fileName:
            fileName.write(texttolog)

def processargs ():
    def striparguments (argumentId, argumentPrefix):
        # split arguments in two blocks split by equals sign with single quotes
        splitarguments = sys.argv[argumentId].split("=",1)
        writeLog ("Arguments Split id:    " + str(argumentId) + "= " + str(splitarguments) + " (" + str(argumentPrefix) + ")", logInfo)
        if splitarguments[0] != argumentPrefix:
            argumentStatus = False
        else:
            argumentStatus = True
        return splitarguments[1], argumentStatus

    # Structure of arguments Local Command script type:
    # server=<servername>:<port> credentials=<user>:<passwd> language=<lang> --debug

    # Structure of arguments MQTT script type:
    # server=<servername>:<port> credentials=<user>:<passwd> mqttserver=<server>:<port> --debug

    # --debug option is optional
    
    argumentStatus = True 
    numberarguments = len(sys.argv)
    writeLog ("Arguments Raw (" + str(numberarguments) + "):     " + str(sys.argv), logInfo)

    argumentResult, argumentStatus = striparguments(1, argumentsText[0])
    if not argumentStatus:
        return False
    arguments.append(argumentResult)        # 1: server connection

    argumentResult, argumentStatus = striparguments(2, argumentsText[1])
    if not argumentStatus:
        return False
    credentials = str(argumentResult).split(":",1)
    arguments.append(credentials[0])        # 2: credentials username
    arguments.append(credentials[1])        # 3: credentials password

    argumentResult, argumentStatus = striparguments(3, argumentsText[2])     # 4: language Rhasspy
    if not argumentStatus:
        argumentResult, argumentStatus = striparguments(3, argumentsText[3]) # 4: MQTT server
        if not argumentStatus:
            return False
    arguments.append(argumentResult)        # 4: language Rhasspy or MQTT server

    if numberarguments == 5:
        if sys.argv[4].lower() == argdebug:    
            arguments.append(argdebug)      # 5: debug option
        else:
            arguments.append("--nodebug")   # 5: no debug option
    else:
        arguments.append("--nodebug")       # 5: no debug option

    writeLog ("Arguments Clean:       " + str(arguments), logInfo)
    return argumentStatus

def domoRequest(domoParms):
    domoticz_url = str(arguments[1]) + domoAPIbase + domoParms    
    writeLog ("Domoticz API definition: " + str(domoticz_url), logDebug)
    request_response = requests.get(domoticz_url, headers={'Accept': 'application/json'}, auth=(arguments[2], arguments[3]))
    writeLog ("Domoticz API status <" + str(request_response.status_code) + ">", logDebug)
    writeLog ("Domoticz API JSON " + str(request_response.json()), logDebug)
    return request_response

def domoGetIDX(domoticz_device):
    # check for friendly name device supplied, so xxxx;yyyy where xxxx is regular name and yyyy is friendly name
    # try to translate the supplied device name to the value of a user variable
    # so user variables names are logical device names and will containt the actual device names
    domoticz_idx      = 0
    friendly_name     = False
    if str(domoticz_device).count(";") > 0:
        friendly_name = True
    writeLog ("Friendly name supplied <" + str(friendly_name) + ">", logDebug)
    devicelist        = domoticz_device.split(";",1)
    domoticz_device   = devicelist [0]

    domoticz_result = domoRequest("getuservariables")
    if domoticz_result.ok:
        domoticz_usrvar = searchJSON("result[?Name=='" + domoticz_device + "'].Value", domoticz_result.json())
        writeLog ("User variable device name <" + str(domoticz_usrvar) + ">", logDebug)
        if domoticz_usrvar.lower() not in ("none", ""):
            writeLog ("User variable processed <" + str(domoticz_device) + ">", logDebug)
            domoticz_device = domoticz_usrvar       
    # determine the IDX of the devicename        
    domoticz_result = domoRequest("devices_list")
    if domoticz_result.ok:    
        domoticz_idx = searchJSON("result[?name=='" + domoticz_device + "'].idx", domoticz_result.json())
        writeLog ("Device IDX <" + str(domoticz_idx) + "> (" + str(domoticz_device) + ")", logDebug)

    # friendly device name supplied?
    if friendly_name:
        domoticz_device = devicelist [1]
    return domoticz_idx, domoticz_device

def searchJSON(jmessearch, payload):
    foundJSONstring = str(jmespath.search(jmessearch, payload)).strip("[']")
    writeLog("searchJSON <" + foundJSONstring + "> found thru <" + jmessearch + ">", logDebug)
    return foundJSONstring

def translateText (textToTranslate):
    textToTranslate = textToTranslate.lower()
    writeLog("Lower case text to translate <" + textToTranslate + ">", logDebug)
    if textToTranslate in specificTranslation.keys():
        writeLog("Found specific translation for <" + textToTranslate + "> : <" + specificTranslation [textToTranslate] + ">", logDebug)
        textTranslated = specificTranslation [textToTranslate]
    else:
        writeLog("No specific translation found for <" + textToTranslate + ">", logDebug)
        textTranslated = textToTranslate
    return textTranslated

def extractTexts(blocksSpeakResponse, blocksDomoticzValues, payload, scriptType):
    # check "peakpartialtext" is supplied for backward compatibility
    blocksPartialTexts = searchJSON(tagListJSON ["speakpartialtext"] [scriptType], payload)
    if blocksPartialTexts != "":
        writeLog("Deprecated partial texts " + str(blocksPartialTexts), logError)
        blocksSpeakResponse = blocksSpeakResponse.split(";") + blocksPartialTexts.split(",")
        # example ["0"; "1"; "2"] So pick 0th, 1st and 2nd values
    else:
        blocksSpeakResponse = blocksSpeakResponse.split(";")
        # example ["The temparature is"; "0"; "1"; "2"; "degrees"] So pick 0th, 1st and 2nd values

    if len(blocksSpeakResponse) == 1:
        if blocksSpeakResponse[0] == "none":
            return ""

    blocksDomoticzValues = blocksDomoticzValues.split()
    # example ["4" "point" "7" "90" "Wet"] So in above example: "4", "point" and "7"

    speakFullValue = True
    countBlocksDomoticzValues = len(blocksDomoticzValues)
    writeLog("Speak response / Domoticz value / count = " + str(blocksSpeakResponse) + " | " +  str(blocksDomoticzValues) + " | " + str(countBlocksDomoticzValues), logDebug)
    sentenceToSpeak = ""
    for indexOrText in blocksSpeakResponse:
        if indexOrText.isdigit():
            if int(indexOrText) in range(0, countBlocksDomoticzValues):
###                sentenceToSpeak = sentenceToSpeak + " " + translateText (''.join(filter(str.isalnum, blocksDomoticzValues[int(indexOrText)])))
                sentenceToSpeak = sentenceToSpeak + " " + translateText (blocksDomoticzValues[int(indexOrText)])
###                writeLog("Word id   <" + str(''.join(filter(str.isalnum, blocksDomoticzValues[int(indexOrText)]))) +">", logDebug)
                writeLog("Word id   <" + str(blocksDomoticzValues[int(indexOrText)]) +">", logDebug)
                speakFullValue = False
            else:
                writeLog("Value id <"+ str(indexOrText) + "> outside Words list range <0-"+ str(countBlocksDomoticzValues) +">", logDebug)
        else:
            sentenceToSpeak = sentenceToSpeak + " " + indexOrText
            writeLog("Word text <" + str(indexOrText) +">", logDebug)
    if speakFullValue: # all values captured from Domoticz to be spoken
        for textBlock in blocksDomoticzValues:
            sentenceToSpeak = sentenceToSpeak + " " + translateText (textBlock)
            writeLog("Word block <" + str(textBlock) +">", logDebug)
    return sentenceToSpeak

def setValueNoDecimal(valueWithDecimal):
    valueWithoutDecimal = valueWithDecimal.split(".", 1)[0]
    return valueWithoutDecimal

def getValueDecimalPoint (critJSON, payload):
    return searchJSON(critJSON, payload).replace(".", " " + specificTranslation ["point"] + " ")

def getValueNoDecimal (critJSON, payload):
    return setValueNoDecimal(searchJSON(critJSON, payload))

def getValue (critJSON, payload):
    return searchJSON(critJSON, payload)

def getLanguage (scriptType, payload):
    # get language of Domoticz
    domoLanguage = "en"   # set domoticz language per default
    domoticz_result = domoRequest("getsettings")
    if domoticz_result.ok:
        domoLanguage = searchJSON("Language", domoticz_result.json())
        writeLog("Domoticz language <" + domoLanguage + "> found", logDebug)
    # get language of Rhasspy
    toLanguage = ""
    if scriptType == scriptTypeLC:
        toLanguage = arguments[4]
    if scriptType == scriptTypeMQ:
        toLanguage = searchJSON("lang", payload)        
    writeLog("Rhasspy language <" + toLanguage + ">", logDebug)
    return domoLanguage, toLanguage

def validateDomoticz (payload, scriptType):
    writeLog ("Script type " + scriptType, logDebug)
    response_status = 200

    ### capture the device delivered from Rhasspy and validate it exists in Domoticz by retrieving the IDX.
    domoticz_device = searchJSON(tagListJSON ["device"] [scriptType], payload)
    domoticz_IDX, domoticz_device = domoGetIDX(domoticz_device)
    if domoticz_IDX == "":
        writeLog ("Device " + domoticz_device + " not found / not active", logError)
        response_status = 4001
        return response_status, "", "", "", "", "", ""

    ### validate type and subtype can already be processed by the plugin.
    domoticz_result = domoRequest("getdevices&rid=" + domoticz_IDX)
    if not domoticz_result.ok:
        writeLog ("Device details " + domoticz_device + " not found", logError)
        response_status = 4002
        return response_status, "", "", "", "", "", ""

    domoticz_type    = searchJSON(resultJSON ["type"], domoticz_result.json()).lower()
    domoticz_subtype = searchJSON(resultJSON ["subtype"], domoticz_result.json()).lower()
    if not domoticz_type in domoTypesJSON.keys():
        writeLog ("Domoticz type " + domoticz_type + " not setup (to add to domoTypesJSON)", logError)
        response_status = 4003
        return response_status, "", "", "", "", "", ""
    if domoTypesJSON [domoticz_type] == False:
        writeLog ("Domoticz type " + domoticz_type + " not configured (domoTypesJSON false)", logError)
        response_status = 4004
        return response_status, "", "", "", "", "", ""
    if not domoticz_subtype in domoSubTypesJSON.keys():
        writeLog ("Domoticz subtype " + domoticz_subtype + " not setup (to add to domoSubTypesJSON)", logError)
        response_status = 4005
        return response_status, "", "", "", "", "", ""
    if domoSubTypesJSON [domoticz_subtype] == False:
        writeLog ("Domoticz subtype " + domoticz_subtype + " not configured (domoSubTypesJSON false)", logError)
        response_status = 4006
        return response_status, "", "", "", "", "", ""
    writeLog("Domoticz type/subtype validated", logDebug)

    askForConfirmation = searchJSON(tagListJSON ["askconfirmation"] [scriptType], payload)
    writeLog("Request confirmation before processing [" + askForConfirmation + "]", logDebug)

    return response_status, domoticz_device, domoticz_IDX, domoticz_type, domoticz_subtype, domoticz_result, askForConfirmation

def performDomoticz (apiCommand, payload, scriptType, domoticz_device, domoticz_IDX, domoticz_type, domoticz_subtype, domoticz_result):
    writeLog ("Domoticz API command " + apiCommand + " (" + domoticz_device + ")", logInfo)
    ### update to do? if so also retrieve updated value.
    # perform update for switchlight types
    if apiCommand == "switchlight":
        # update can be on/off: 'entity': 'state', 'value': {'kind': 'Unknown', 'value': 'Off'}
        # but also can be a number: {'entity': 'rhasspy/number', 'value': {'kind': 'Number', 'value': 5}
        # or a mix: {'entity': 'state', 'value': {'kind': 'Unknown', 'value': '0'}
        domoticz_state = searchJSON(tagListJSON ["state"] [scriptType], payload)
        if domoticz_state == "":
            domoticz_state = searchJSON(tagListJSON ["number"] [scriptType], payload)
            if domoticz_state != "":
                domoticz_state = "Set%20Level&level=" + domoticz_state 
                writeLog("Device number [" + domoticz_state + "]", logInfo)
        else:
            # validate state is digit, so is set level command
            if domoticz_state.isdigit():
                domoticz_state = "Set%20Level&level=" + domoticz_state 
            writeLog("Device state [" + domoticz_state + "]", logInfo)
        if domoticz_state != "":
            domoticz_result = domoRequest(apiCommand + "&idx=" + domoticz_IDX + "&switchcmd=" + domoticz_state)
            if not domoticz_result.ok:
                writeLog("Device update " + domoticz_device + "(" + domoticz_state + ") failed", logError)
                return ""
        else:
            writeLog("Device update " + domoticz_device + " no update value retrieved", logError)
            return ""
    # perform update for setpoint types
    if apiCommand == "setsetpoint":
        domoticz_temp  = searchJSON(tagListJSON ["setpoint"] [scriptType], payload).replace(" ", "")
        domoticz_result = domoRequest(apiCommand + "&idx=" + domoticz_IDX + "&setpoint=" + domoticz_temp)
        if not domoticz_result.ok:
            writeLog("Setpoint update " + domoticz_device + " failed", logError)
            return ""
    # perform update for text types
    if apiCommand == "udevice":
        writeLog("Before compile", logDebug)
        entity_expr = jmespath.compile("slots[?entity=='setdomoticzvalue'].value.value | [0]")
        slot_expr = jmespath.compile("slots[?slotName=='setdomoticzvalue'].value.value | [0]")
        writeLog("Before entity result", logDebug)
        result = entity_expr.search(payload)
        writeLog("After entity result", logDebug)
        domoticz_text = "niet gevonden"
        writeLog("Check entity result", logDebug)
        if result:
            domoticz_text = result
        else:
            writeLog("Before slot result", logDebug)
            result = slot_expr.search(payload)
            writeLog("Check slot result", logDebug)
            if result:
                domoticz_text = result
        writeLog("Result [" + domoticz_text + "]", logDebug)



#####        expression = jmespath.compile(
#####                        "slots[?entity=='setdomoticzvalue'].value.value[0] || "
#####                        "slots[?slotName=='setdomoticzvalue'].value.value[0] || "
#####                        "'no setdomoticzvalue found'"
#####                        )
#####        writeLog("After compile", logDebug)
#####        domoticz_text = expression.search(payload)
#####        writeLog("After expression [" + str(domoticz_text) + "]", logDebug)


### contains(join('; ',slots[*].slotName),'setdomoticzvalue') TRUE dan komt dit voor (jmespath query)

### slots[*].slotName geeft de lijst van slots, bv:

### [
###   "device",
###   "setdomoticzvalue;domoticz/grocery",
###   "speakresponse",
###   "askconfirmation"
### ]

### slots[*].entity geeft de lijst van entities, bv:

### [
###   "device",
###   "domoticz/grocery",
###   "speakresponse",
###   "askconfirmation"
### ]


### lees regel voor regel slotName array.
### als slotNane = setdomoticzvalue dan bepaal slot id (in voorbeeld de tweede regel, dus waarde 1).
### als id een waarde heeft, dan bepaal entity value.value van de regel (id). in voorbeeld domoticz/grocery
### 

### haal dan domoticz/grocery.value.value op: slots[?entity=='domoticz/grocery'].value.value

### resultaat is Albert Heijn Pure Hagelslag

###        domoticz_text  = searchJSON(tagListJSON ["setdomoticzvalue"] [scriptType], payload)
        domoticz_result = domoRequest(apiCommand + "&idx=" + domoticz_IDX + "&nvalue=0&svalue=" + domoticz_text)
        if not domoticz_result.ok:
            writeLog("Device update " + domoticz_device + " failed", logError)
            return ""
    # perform a getdevices to confirm the actual status of the device after an update request
    # and would be that all intents will result in a getdevices request whatever intent is defined.
    if apiCommand != "getdevices":
        domoticz_result = domoRequest("getdevices&rid=" + domoticz_IDX)
        if not domoticz_result.ok:
            writeLog("Device actual details " + domoticz_device + " not found", logError)
            return ""
    writeLog("Domoticz update validated", logDebug)

    # perform retrieve security status
    if apiCommand == "getsecstatus":
        domoticz_result = domoRequest(apiCommand)
        if not domoticz_result.ok:
            writeLog("Security status retrieve failed", logError)
            return ""

    baseSpeakResponse = searchJSON(tagListJSON ["speakresponse"] [scriptType], payload)
    if baseSpeakResponse.strip().lower() == "none":
        writeLog("No speech feedback requested", logDebug)
        return ""

    # check feedback needs to be spoken
    if searchJSON(tagListJSON ["speakstate"] [scriptType], payload) == "no":
        writeLog("No actual state feedback requested", logDebug)
        return baseSpeakResponse
        
    # always determine base value via Data field.
    domoticz_value = searchJSON(resultJSON ["data"], domoticz_result.json())
    # translate raw data to local language if this is an update - so not a getdevices
    if apiCommand != "getdevices":
        domoticz_value = translateText (domoticz_value)
    writeLog("Domoticz current API result <" + str(domoticz_result.json()) + ">", logDebug)

    # adjust the captured data so it can be spoken properly
    # only validated types and subtypes are passed (so value is True in domoTypesJSON / domoSubTypesJSON)
    # take care to extend the resultJSON variable.

    if domoticz_type == "current" or domoticz_subtype == "visibility" or domoticz_subtype == "pressure" or domoticz_subtype == "kwh":
        domoticz_value = getValueDecimalPoint (resultJSON ["data"], domoticz_result.json())
    if domoticz_subtype == "energy":
        energysplitted = getValue (resultJSON ["data"], domoticz_result.json()).split(";")
        domoticz_value = energysplitted[0] + " " +\
                         energysplitted[1] + " " +\
                         energysplitted[2] + " " +\
                         energysplitted[3] + " " +\
                         energysplitted[4] + " " +\
                         energysplitted[5]
    if domoticz_type == "security":
        domoticz_value = "security" + getValue (resultJSON ["secstatus"], domoticz_result.json())
    if domoticz_type == "setpoint":
        domoticz_value = translateText (getValueDecimalPoint (resultJSON ["data"], domoticz_result.json()))
    if domoticz_type == "temp":
        domoticz_value = getValueDecimalPoint (resultJSON ["temp"], domoticz_result.json())
    if domoticz_type == "temp + humidity":
        domoticz_value = getValueDecimalPoint (resultJSON ["temp"], domoticz_result.json()) + " " +\
                         getValueNoDecimal (resultJSON ["humidity"], domoticz_result.json()) + " " +\
                         translateText (getValue (resultJSON ["humiditystatus"], domoticz_result.json()))
    if domoticz_type == "temp + humidity + baro":
        domoticz_value = getValueDecimalPoint (resultJSON ["temp"], domoticz_result.json()) + " " +\
                         getValueNoDecimal (resultJSON ["humidity"], domoticz_result.json()) + " " +\
                         translateText (getValue (resultJSON ["humiditystatus"], domoticz_result.json())) + " " +\
                         getValueNoDecimal (resultJSON ["barometer"], domoticz_result.json()) + " " +\
                         translateText (getValue (resultJSON ["forecaststr"], domoticz_result.json()))
    if domoticz_type == "wind":
        domoticz_value = getValueNoDecimal (resultJSON ["direction"], domoticz_result.json()) + " " +\
                         getValue (resultJSON ["directionstr"], domoticz_result.json()) + " " +\
                         getValueDecimalPoint (resultJSON ["speed"], domoticz_result.json()) + " " +\
                         getValueDecimalPoint (resultJSON ["chill"], domoticz_result.json()) + " " +\
                         getValueDecimalPoint (resultJSON ["temp"], domoticz_result.json())
    writeLog("Domoticz raw value <" + domoticz_value + ">", logDebug)

    sentence = extractTexts(baseSpeakResponse, domoticz_value, payload, scriptType)
    writeLog("Domoticz sentence for device <" + domoticz_device + " (idx="+ domoticz_IDX +") > is '" + sentence +"'", logDebug)
    return sentence