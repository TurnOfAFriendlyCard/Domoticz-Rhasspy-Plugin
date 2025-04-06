#!/usr/bin/env python
#
# Python Plugin for Rhasspy Domoticz integration
#
# Author:  marathon2010
# Version 2.2.10 (25 March 2025)
#
from domoticz_rhasspy_functions import *
#####################################################################
#
# Local functions
#
#####################################################################
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

def addSpeechJSON(text):
    global rhasspyjson
    # add text to be spoken by rhasspy to the JSON structure.
    writeLog ("Speech " + str(text), logDebug)
    rhasspyjson["speech"] = {"text": text}
#####################################################################
#
# Preparation
#
#####################################################################
openLog(scriptTypeLC)
#####################################################################
#
# Main processing
#
#####################################################################
if processargs():
    readJSON()
    capturedTopic = searchJSON("intent.name", rhasspyjson)
    writeLog ("Topic captured <" + capturedTopic + ">", logInfo)
    if capturedTopic[:len(intentPrefix)].lower() != intentPrefix:
        writeLog("No Domoticz topic " + capturedTopic, logDebug)
    else:
        sentence = processDomoticz (capturedTopic[len(intentPrefix):].lower(), rhasspyjson, scriptTypeLC)
        addSpeechJSON (sentence)
    writeLog ("Intent finished processing <" + capturedTopic + ">", logInfo)
    writeJSON()
#####################################################################
#
# Completion
#
#####################################################################
closeLog()