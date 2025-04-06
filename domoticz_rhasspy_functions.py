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
import deepl
from domoticz_rhasspy_vars import *
#####################################################################
version = "3.0.90 (6 April 2025)"
#####################################################################
#
# Global functions
#
#####################################################################
def openLog(scriptType):
    global logfile, pathname
    if scriptType == scriptTypeLC:
        pathname = pathnameLC
    else:
        pathname = pathnameMQ
    try:
        logfile = open(pathname + logFileName, "a")
    except FileNotFoundError:    
        logfile = open(pathname + logFileName, "w")
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
    domoticz_idx = 0
    # first try to translate the supplied device name to the value of a user variable
    # so user variables names are logical device names and will containt the actual device names
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
    return domoticz_idx

def searchJSON(jmessearch, payload):
    foundJSONstring = str(jmespath.search(jmessearch, payload)).strip("[']")
    writeLog("searchJSON <" + foundJSONstring + "> found thru <" + jmessearch + ">", logDebug)
    return foundJSONstring

def translateText (domoLanguage, toLanguage, textToTranslate):
    writeLog("Language from <" + domoLanguage + "> to <" + toLanguage + ">", logDebug)
    if domoLanguage == toLanguage:
        textTranslated = textToTranslate.lower()
    else:
        textTranslated = deepl.translate(source_language=domoLanguage, target_language=toLanguage, text=textToTranslate.lower(), formality_tone="informal")
        try:
            if specificTranslation [textTranslated] != "None":                 # so specific translation to apply
                writeLog("Found specific translation for <" + textTranslated + "> : <" + specificTranslation [textTranslated] + ">", logDebug)
                textTranslated = specificTranslation [textTranslated]
            else:
                writeLog("Specific translation found None", logDebug)
        except:
            writeLog("No specific translation found for <" + textTranslated + ">", logDebug)
    writeLog("Translated <" + textToTranslate + "> into <" + textTranslated + ">", logDebug)
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
    writeLog("Speak response / Domoticz value / count " + str(blocksSpeakResponse) + " | " +  str(blocksDomoticzValues) + " | " + str(countBlocksDomoticzValues), logDebug)
    sentenceToSpeak = ""
    for indexOrText in blocksSpeakResponse:
        if indexOrText.isdigit():
            if int(indexOrText) in range(0, countBlocksDomoticzValues):
                sentenceToSpeak = sentenceToSpeak + " " + ''.join(filter(str.isalnum, blocksDomoticzValues[int(indexOrText)]))
                writeLog("Word id   <" + str(''.join(filter(str.isalnum, blocksDomoticzValues[int(indexOrText)]))) +">", logDebug)
                speakFullValue = False
            else:
                writeLog("Value id <"+ str(indexOrText) + "> outside Words list range <0-"+ str(countBlocksDomoticzValues) +">", logDebug)
        else:
            sentenceToSpeak = sentenceToSpeak + " " + indexOrText
            writeLog("Word text <" + str(indexOrText) +">", logDebug)
    if speakFullValue: # all values captured from Domoticz to be spoken
        for textBlock in blocksDomoticzValues:
            sentenceToSpeak = sentenceToSpeak + " " + textBlock
            writeLog("Word block <" + str(textBlock) +">", logDebug)
    return sentenceToSpeak

def setValueNoDecimal(valueWithDecimal):
    valueWithoutDecimal = valueWithDecimal.split(".", 1)[0]
    return valueWithoutDecimal

def getValueDecimalPoint (critJSON, payload):
    return searchJSON(critJSON, payload).replace(".", " point ")

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

def processDomoticz (apiCommand, payload, scriptType):
    writeLog ("Script type " + scriptType, logDebug)

    # capture the device delivered from Rhasspy and validate it exists in Domoticz by retrieving the IDX.
    domoticz_device = searchJSON(tagListJSON ["device"] [scriptType], payload)
    domoticz_IDX = domoGetIDX(domoticz_device)
    if domoticz_IDX == "":
        writeLog ("Device " + domoticz_device + " not found / not active", logError)
        return ""
    writeLog ("Domoticz API command " + apiCommand + " (" + domoticz_device + ")", logInfo)

    # get language of Domoticz and Rhasspy
    domoLanguage, toLanguage = getLanguage(scriptType, payload)

    # validate type and subtype can already be processed by the plugin.
    domoticz_result = domoRequest("getdevices&rid=" + domoticz_IDX)
    if not domoticz_result.ok:
        writeLog ("Device details " + domoticz_device + " not found", logError)
        return ""
    domoticz_type = searchJSON(resultJSON ["type"], domoticz_result.json()).lower()
    domoticz_subtype = searchJSON(resultJSON ["subtype"], domoticz_result.json()).lower()
    if not (domoticz_type in domoTypes and domoticz_subtype in domoSubTypes):
        writeLog ("Device type / subtype (" + domoticz_type + " / " + domoticz_subtype + ") for device <" + domoticz_device + "> not validated yet", logError)
        return ""
    writeLog("Domoticz type/subtype validated", logDebug)

    # perform update for switchlight types
    if apiCommand == "switchlight":
        domoticz_state = searchJSON(tagListJSON ["state"] [scriptType], payload)
        domoticz_result = domoRequest(apiCommand + "&idx=" + domoticz_IDX + "&switchcmd=" + domoticz_state)
        if not domoticz_result.ok:
            writeLog("Device update " + domoticz_device + " failed", logError)
            return ""

    # perform update for setpoint types
    if apiCommand == "setsetpoint":
        domoticz_temp  = searchJSON(tagListJSON ["setpoint"] [scriptType], payload)
        domoticz_result = domoRequest(apiCommand + "&idx=" + domoticz_IDX + "&setpoint=" + domoticz_temp)
        if not domoticz_result.ok:
            writeLog("Setpoint update " + domoticz_device + " failed", logError)
            return ""

    baseSpeakResponse = searchJSON(tagListJSON ["speakresponse"] [scriptType], payload)
    if baseSpeakResponse.strip().lower() == "none":
        writeLog("No speech feedback requested", logDebug)
        return ""

    # check feedback needs to be spoken
    if searchJSON(tagListJSON ["speakstate"] [scriptType], payload) == "no":
        writeLog("No actual state feedback requested", logDebug)
        return baseSpeakResponse
                
    # perform a getdevices to confirm the actual status of the device after an update request
    # and would be that all intents will result in a getdevices request whatever intent is defined.
    if apiCommand != "getdevices":
        domoticz_result = domoRequest("getdevices&rid=" + domoticz_IDX)
        if not domoticz_result.ok:
            writeLog("Device actual details " + domoticz_device + " not found", logError)
            return ""
        
    # always determine base value via Data field.
    domoticz_value = searchJSON(resultJSON ["data"], domoticz_result.json())
    # translate raw data to local language if this is an update - so not a getdevices
    if apiCommand != "getdevices":
        domoticz_value = translateText (domoLanguage, toLanguage, domoticz_value)
        
    # adjust the captured data so it can be spoken properly
    # Temp
    if (domoticz_type == domoTypes[1]):
        domoticz_value = translateText (domoLanguage, toLanguage, getValueDecimalPoint (resultJSON ["temp"], domoticz_result.json()))
    # temp + humidity
    if (domoticz_type == domoTypes[3]):
        domoticz_value = translateText (domoLanguage, toLanguage, getValueDecimalPoint (resultJSON ["temp"], domoticz_result.json())) + " " +\
                         getValueNoDecimal (resultJSON ["humidity"], domoticz_result.json()) + " " +\
                         translateText (domoLanguage, toLanguage, getValue (resultJSON ["humiditystatus"], domoticz_result.json()))
    # temp + humidity + baro
    if (domoticz_type == domoTypes[4]):
        domoticz_value = translateText (domoLanguage, toLanguage, getValueDecimalPoint (resultJSON ["temp"], domoticz_result.json())) + " " +\
                         getValueNoDecimal (resultJSON ["humidity"], domoticz_result.json()) + " " +\
                         translateText (domoLanguage, toLanguage, getValue (resultJSON ["humiditystatus"], domoticz_result.json())) + " " +\
                         getValueNoDecimal (resultJSON ["barometer"], domoticz_result.json()) + " " +\
                         translateText (domoLanguage, toLanguage, getValue (resultJSON ["forecaststr"], domoticz_result.json()))
    # setpoint
    if (domoticz_type == domoTypes[12]):
        domoticz_value = translateText (domoLanguage, toLanguage, getValueDecimalPoint (resultJSON ["data"], domoticz_result.json()))
    # general and text
###    if (domoticz_type == domoTypes[13] and domoticz_subtype == domoSubTypes[22]):
    # p1 smart meter and gas
###    if (domoticz_type == domoTypes[19] and domoticz_subtype == domoSubTypes[35]):

    sentence = extractTexts(baseSpeakResponse, domoticz_value, payload, scriptType)
    writeLog("Domoticz sentence <" + sentence +">", logDebug)
    return sentence