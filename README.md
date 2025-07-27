# 1 Goal
This plugin captures Rhasspy voice requests and processes these requests in Domoticz and speaks feedback via Rhasspy.

# 2 Description
**_Put on the light_**, **_what is the state of the washing machine_** or **_put the heating to 18 degrees_**.
These are requests that can be processed with all kind of voice assistants.
This plugin takes care that a voice request is actually processed within Domoticz.
And for **free**. And **no data** being captured by Google or other cloud based providors.

Basic idea is sentences defined in Rhasspy (intents) which are in line with Domoticz API commands and devices.
Once the request is processed in Domoticz, the actual status of the device will be captured and spoken via Rhasspy.
So a dialogue will be something like this (`Hey Jarvis` is the wake word in Rhasspy):

1. `Hey Jarvis put on the kitchen light`
2. `The light in the kitchen is swithed on`

In German this would be:

1. `Hey Jarvis, mach das Küchenlicht an`
2. `Das Licht in der Küche ist an`

# 3 Prerequisites
1. `Rhasspy 2.5 up and running`: See for more information https://rhasspy.readthedocs.io/en/latest/. 
2. `Recent Domoticz`: supporting new API structures.

# 4 Rhasspy
## 4.1 Intents, Sentences and Slots
Based on an example the structure of sentences in Rhasspy relevant to Domoticz is explained. First the intents are explained and next the sentences within the intents.
### 4.1.1 Intents
Every intent that needs to be interpreted by Domoticz needs to start with `dz` succeeded by an API command for Domoticz, for instance `switchlight`. The intent text in the plugin
is not case sensitive (everything will be converted to lowercase by the plugin).

Currently supported API commands of Domoticz (see for details https://wiki.domoticz.com/Domoticz_API/JSON_URL's and the appendix chapter at the end of this readme document):
  1. [dzswitchlight] - So on/off open/close switches.
  2. [dzsetsetpoint] - Update setpoint device like heating thermostat.
  3. [dzgetsecstatus] - Retrieve security status.
  4. [dzgetdevices] - So actual value of a Domoticz device, report the value.
### 4.1.2 Sentences
Besides the sentence rules of Rhasspy every sentence related to the Domoticz integration consists of next blocks:
1. `spoken text`
2. `fields Domoticz`
3. `reponse text`

Let's assume Domoticz is running in English language and review the German kitchenlight example. This would be configured next:

**`mach das Küchenlicht`{device:Licht} (an:on | aus:off){state}(:){speakresponse:`Das Licht in der Küche ist`}**

- `mach das Küchenlicht`
  * This is the text to be spoken by the user.
- {device:Licht}
  * The devicename in Domoticz is `Licht`, this is case sensitive and should match exactly. If not, the plugin is not able to find the corresponding device IDX.
- (an:on | aus:off){state}
  * The state into which the device is to be updated. In this case spoken text by the user can be either `an` or `aus`.
  * So the actual spoken text by the user can be `mach das Küchenlicht an`.
This will be communicated to Domoticz as `on` or `off`. If language Rhasspy and Domoticz are the same, the translation can be omitted (so `(an | aus){state}` for both German). The field for Domoticz to capture the state of the device is {state}.
- (:){speakresponse:`Das Licht in der Küche ist`
  * The text to be spoken by Rhasspy after processing by Domoticz. The actual status will be captured and added to this text. If status is `on` this can be translated to German as `an` (by using the specific translations feature, see below).

### 4.1.3 Sample sentence.ini
Next would be a valid setup within Rhasspy of the sentence.ini file:

    [dzSwitchLight]

    mach das Küchenlicht`{device:Licht} (an:on | aus:off){state}(:){speakresponse:Das Licht in der Küche ist}

    [GetTime]

    wie spät ist es.

    [dzGetDevices]

    wie ist der Status der Küchenlampe{device:Licht}(:){speakresponse:Die Lampe in der Küche ist}

In this case the intent [GetTime] will not be processed in the plugin (as it lacks the prefix `dz`).

### 4.1.4 Response text
Status text retrieved from a device status can consists of multiple parts. For instance take a `Temp + Humidity + Baro` device. This extracts next data components:
- `11.1` Temperature
- `49.0` Humidity
- `Comfortable` HumidityStatus
- `1025.0` Barometer
- `Some Clouds` ForecastStr

This results in next string to be spoken in Rhasspy:
`11 point 1 49 comfortable 1025 some clouds`

Suppose you are only interested in the humidity to be spoken. You can configure this via the `speakresponse` option in sentence.ini:

    [dzGetDevices]

    what is humidity{device:TempHumBaro}(:){speakresponse:humidity is;3;percent}

So just count the words (starting with zero as the first word - so `11` from the example Rhasspy spoken text would be the first word).
Rhasspy will respond with the spoken text `humidity is 49 percent`.

As from vs 3.0 the `speakpartialtext` functionality is integrated into the `speakresponse` tag (and `speakpartialtext` tag will be deprecated in a next version). 
Bear in mind the blocks after the `speakresponse` tag are separated by a semi-colon (so `;`).
In this way you can build you own reporting feedback to be spoken mixing fixed text and values from Domoticz.

It is also possible to suppress the feedback of the actual state by a device. The German example of the kitchenlight reports the actual state.
If you would amend the sentence to `(:){speakresponse:Der Zustand des Küchenlichts hat sich geändert}(:){speakstate:no}` no actual state retrieved from Domoticz would be spoken. 

### 4.1.5 Slots
It is possible to process slots as spoken device names defined in Rhasspy. The `temperature` file in the `slots/domoticz` folder in Rhasspy could be like this:

    [dzGetDevices]

    what is [the] $domoticz/temperature(:){speakresponse:the temperature is;0;degrees}

The slot `domoticz/temperature` would look like this:

    (temperature outside | outside temperature | out temperature){device:Temperature Outside}
    (temperature inside | inside temperature | in temperature){device:Temperature Inside}

So the request `what is inside temperature` will be parsed in Domoticz and spoken text will be `the temperature is 19 degrees`.

## 4.2 Specific translations
The JSON structure `domoticz_rhasspy_translations.json` will be processed once the integration is started. The file contains mapping between results in Domoticz and results to be send back to Rhasspy.
Example of the structure (so English to Dutch translation - for simplicity the {} were omitted):

      "always"        : "altijd",
      "closed"        : "gesloten",
      "cloudy"        : "bewolkt",
      "cloudy/rain"   : "bewolkt en regen",
      "_last_line"    : "_add new lines above this line"


When the state of a device is captured as `closed` the text send to Rhasspy to be spoken will be `gesloten`. The content of the JSON structure may be adjusted for your own needs. 
Bear in mind that after changing the content of the JSON file, the integration is to be stopped and to be restarted in order to take changes into effect.

## 4.3 Typical Setup Rhasspy
My current setup is `Base-Satellite` (Base Rhasspy under Docker on NAS and Satellite Rhasspy under Docker on RPi3).

![Rhasspy](https://github.com/user-attachments/assets/e539f4a2-1ee0-424c-ab21-19f3d169fa83)

![Base Master v3](https://github.com/user-attachments/assets/d96ef095-01c0-4ef4-b863-594b3bb1e839)


# 5 Domoticz
## 5.1 User variables
The device name to be supplied in the sentence or slot in Rhasspy should be the actual device name. One way to be flexible in Domoticz on device names is to define a user variable representing the device.

User variables in Domoticz are defined in Setup, More options, User variables. Example is:

- Variable name: 	TempOut
- Variable type: 	String
- Variable value: Outside Temperature	

So `Outside Temperature` is the actual device name, but the variable `TempOut` can be used in Rhasspy and Domoticz.
So you could stay independant of changing your device names in Domoticz and also having tp change your Rhasspy sentences and slots.
I'm using user variables for devices (ao) in DzVents as well (so would look like this: `if (domoticz.devices(domoticz.variables('SensorGarageDoor').value).state == 'Open'`).
In the sentence.ini next lines have same result:


    what is temperature outside{device:Outside Temperature}(:){speakresponse:the temperature is;0;degrees}
    what is temperature outside{device:TempOut}(:){speakresponse:the temperature is;0;degrees}


Bear in mind, this is `optional` functionality. You can still use the actual device name in the sentence.ini. So two options.

# 6 INSTALLATION

Two methods can be implemented: 1) via Local Command script or 2) via MQTT service script (as from vs3).

## 6.1 Local Command Script

### A. Python program
1. Open a `PuTTY` session.
2. Go to the Rhasspy `profiles` folder. On that level you will see the language folder of Rhasspy, for instance `en` or `nl`.
3. Download the plugin: `git clone https://github.com/TurnOfAFriendlyCard/Domoticz-Rhasspy-Plugin`
4. Alternative is to download and extract the zip file:
   - Go to https://github.com/TurnOfAFriendlyCard/Domoticz-Rhasspy-Plugin.
   - Click on Code and select Download ZIP.
   - Create a folder for the plugin (`mkdir Domoticz-Rhasspy-Plugin`) in the `profiles` folder of Rhasspy.
   - Unzip the ZIP file in the created folder.
5. Go to folder (`cd Domoticz-Rhasspy-Plugin`).
6. Make the domoticz_rhasspy.py file executable (`chmod 755 pdomoticz_rhasspy.py`). Same applies to domoticz_rhasspy_vars.py and domoticz_rhasspy_functions.py.
7. Install module jmespath: `pip3 install jmespath`. This is required for searching in JSON structures.

### B. Rhasspy
1. Open Rhasspy and select `Settings` in the menu.
2. Enable Intent Handling and select Local Command.
3. Restart Rhasspy.
4. Open the Local Command settings within Intent Handling.
5. In field `Program` enter the full path and filename of the program downloaded in step A. For instance `/profiles/domoticz-rhasspy-plugin/domoticz_rhasspy.py`.
6. In field `Arguments` next is to be entered:
- `server=[ip-address:port] credentials=[username[:[password] language=[lang] --debug`
- `Server` is the Domoticz ip address and port.
- `Credentials` is username and password separated by a colon from the Domoticz user who is authorized to access devices.
- Language of Rhasspy used for `text-to-speech` (not captured in JSON structure in Rhasspy).
- Use option `--debug` for showing debug messages in the logfile. Is optional. The logfile is maintained in same folder as the Python program installed in step A.
- Example:    `server=http://192.102.141.1:8080 credentials=user1:pass1234 language=en --debug`

7. In field `Satellite siteIds` enter the Rhasspy satellites involved in `speech-to-text` and `text-to-speech`.

## 6.2 MQTT service Script

### A. Rhasspy
1. Open Rhasspy and select `Settings` in the menu.
2. Disable Intent Handling.
3. Restart Rhasspy.

### B. Python program
1. Open a `PuTTY` session.
2. Go to the Domoticz `scripts` folder. On that level you will see for example the `dzVents` and `lua` folders.
3. Download the plugin: `git clone https://github.com/TurnOfAFriendlyCard/Domoticz-Rhasspy-Plugin`
4. Alternative is to download and extract the zip file:
   - Go to https://github.com/TurnOfAFriendlyCard/Domoticz-Rhasspy-Plugin.
   - Click on Code and select Download ZIP.
   - Create a folder for the plugin (`mkdir Domoticz-Rhasspy-Plugin`) in the `scripts` folder of Domoticz.
   - Unzip the ZIP file in the created folder.
5. Go to folder (`cd Domoticz-Rhasspy-Plugin`).
6. Make the domoticz_rhasspy_mqtt.py file executable (`chmod 755 pdomoticz_rhasspy_mqtt.py`). Same applies to domoticz_rhasspy_vars.py and domoticz_rhasspy_functions.py.
7. Adjust the variable `pathnameMQ` in the` domoticz_rhasspy_vars.py` for the location of the `domoticz_rhasspy.log`.
8. Install module jmespath: `pip3 install jmespath`. This is required for searching in JSON structures.
9. Install module paho mqtt: `pip3 install paho-mqtt`. This is required for communicating with the MQTT server.
10. Install module daemon: `pip3 install python-daemon`. This is required for running Rhasspy Domoticz MQTT script in background.
11. Start the python script, for instance like next:

        /usr/bin/python3.9 /opt/domoticz/userdata/scripts/Domoticz-Rhasspy-Plugin/domoticz_rhasspy_mqtt.py server=http://192.168.141.1:8080 credentials=<user>:<password> mqttserver=localhost:1883 –debug >> /opt/domoticz/userdata/scripts/Domoticz-Rhasspy-Plugin/domoticz_rhasspy_daemon.log 2>&1

12. The command can be broken down as:
- `/usr/bin/python3.9` to start the python script.
- `/opt/domoticz/userdata/scripts/Domoticz-Rhasspy-Plugin/domoticz_rhasspy_mqtt.py` full path to the python script.
- `server=[ip-address:port] credentials=[username[:[password] mqttserver=[ip-address:port] --debug`
- `Server` is the Domoticz ip address and port.
- `Credentials` is username and password separated by a colon from the Domoticz user who is authorized to access devices.
- `MQTTServer` is the MQTT ip address and port.
- Use option `--debug` for showing debug messages in the logfile. Is optional. The logfile is maintained in same folder as the Python program installed in step B5.
12. The python program will start and run in the background.
- Use `ps axuw | grep domoticz_rhasspy_mqtt.py` to verify the process running and to determine the process id.
- Use kill <process id> to stop the python program.
- The `PuTTY` session can be closed.

Enjoy your **Rhasspy Domoticz integration** 😁

## 6.3 Example log file
Next is an example of the `domoticz_rhasspy.log` file with the `--debug` option supplied. Some data is reworked or shortened for obvious reasons or readability.

    26-Jul-25 17:54:19.436291 - STATUS - Domoticz Rhasspy initiated: Functions=v3.3.17 (26Jul25) / Vars=v1.2.16 (26Jul25) / Script=v1.0.6 (15Jul25)
    26-Jul-25 17:54:19.436442 - INFO - Arguments Path:        /.../userdata/scripts/python
    26-Jul-25 17:54:19.436654 - DEBUG - Translations {'always': 'altijd', 'closed': 'gesloten', '_last_line': '_add new lines above this line'}
    26-Jul-25 17:54:19.436755 - INFO - Arguments Raw (5):     ['userdata/scripts/python/domoticz_rhasspy_mqtt.py', 'server=http://xxx.xxx.xxx.xxx:pppp', 'credentials=<user>:<password>', 'mqttserver=localhost:pppp', '--debug']
    26-Jul-25 17:54:19.436841 - INFO - Arguments Split id:    1= ['server', 'http://xxx.xxx.xxx.xxx:pppp'] (server)
    26-Jul-25 17:54:19.436923 - INFO - Arguments Split id:    2= ['credentials', '<user>:<password>'] (credentials)
    26-Jul-25 17:54:19.437006 - INFO - Arguments Split id:    3= ['mqttserver', 'localhost:pppp'] (language)
    26-Jul-25 17:54:19.437095 - INFO - Arguments Split id:    3= ['mqttserver', 'localhost:pppp'] (mqttserver)
    26-Jul-25 17:54:19.437179 - INFO - Arguments Clean:       ['/opt/domoticz/userdata/scripts/python', 'http://xxx.xxx.xxx.xxx:pppp', '<user>', '<password>', 'localhost:pppp', '--debug']
    26-Jul-25 17:54:19.437344 - DEBUG - Connecting MQTT server <localhost via port pppp>
    26-Jul-25 17:54:19.474002 - DEBUG - Connected MQTT server. Waiting for intent.
    
    26-Jul-25 23:13:07.134900 - DEBUG - JSON input: {'input': 'hoe warm is het Temperatuur Buiten het is;0;1;2;graden', 'intent': {'intentName': 'dzGetDevices', 'lang': 'nl'}
    26-Jul-25 23:13:07.135259 - DEBUG - searchJSON <dzGetDevices> found thru <intent.intentName>
    26-Jul-25 23:13:07.135356 - INFO - Topic captured <dzGetDevices>
    26-Jul-25 23:13:07.135440 - DEBUG - Script type MQTT
    26-Jul-25 23:13:07.135552 - DEBUG - searchJSON <Temperatuur Buiten> found thru <slots[0].value.value>
    26-Jul-25 23:13:07.135634 - DEBUG - Domoticz API definition: http://xxx.xxx.xxx.xxx:pppp/json.htm?type=command&param=getuservariables
    26-Jul-25 23:13:07.192356 - DEBUG - Domoticz API status <200>
    26-Jul-25 23:13:07.192894 - DEBUG - Domoticz API JSON {'result': [{'LastUpdate': '2022-08-10 15:01:15' }], 'status': 'OK', 'title': 'GetUserVariables'}
    26-Jul-25 23:13:07.193845 - DEBUG - searchJSON <> found thru <result[?Name=='Temperatuur Buiten'].Value>
    26-Jul-25 23:13:07.194015 - DEBUG - User variable device name <>
    26-Jul-25 23:13:07.194111 - DEBUG - Domoticz API definition: http://xxx.xxx.xxx.xxx:pppp/json.htm?type=command&param=devices_list
    26-Jul-25 23:13:07.198933 - DEBUG - Domoticz API status <200>
    26-Jul-25 23:13:07.199581 - DEBUG - Domoticz API JSON {'result': [{'idx': '423', 'name':  {'idx': '40', 'name': 'Wind', 'name_type': 'Wind (Wind/TFA)'}], 'status': 'OK', 'title': 'GetDevicesList'}
    26-Jul-25 23:13:07.201043 - DEBUG - searchJSON <38> found thru <result[?name=='Temperatuur Buiten'].idx>
    26-Jul-25 23:13:07.201284 - DEBUG - Device IDX <38> (Temperatuur Buiten)
    26-Jul-25 23:13:07.201580 - INFO - Domoticz API command getdevices (Temperatuur Buiten)
    26-Jul-25 23:13:07.201681 - DEBUG - Domoticz API definition: http://xxx.xxx.xxx.xxx:ppppjson.htm?type=command&param=getdevices&rid=38
    26-Jul-25 23:13:07.205737 - DEBUG - Domoticz API status <200>
    26-Jul-25 23:13:07.206101 - DEBUG - Domoticz API JSON {'ActTime': 1753564387, 'AstrTwilightEnd': '00:51', 'trend': 3}], 'status': 'OK', 'title': 'Devices'}
    26-Jul-25 23:13:07.206313 - DEBUG - searchJSON <Temp> found thru <result[].Type>
    26-Jul-25 23:13:07.206471 - DEBUG - searchJSON <LaCrosse TX3> found thru <result[].SubType>
    26-Jul-25 23:13:07.206561 - DEBUG - Domoticz type/subtype validated
    26-Jul-25 23:13:07.206642 - DEBUG - Domoticz update validated
    26-Jul-25 23:13:07.206785 - DEBUG - searchJSON <het is;0;1;2;graden> found thru <slots[?entity=='speakresponse'].value.value>
    26-Jul-25 23:13:07.206907 - DEBUG - searchJSON <> found thru <slots[?entity=='speakstate'].value.value>
    26-Jul-25 23:13:07.207058 - DEBUG - searchJSON <18.9 C> found thru <result[].Data>
    26-Jul-25 23:13:07.207231 - DEBUG - Domoticz current API result <{'ActTime': 1753564387, 'AstrTwilightEnd': '00:51', 'trend': 3}], 'status': 'OK', 'title': 'Devices'}>
    26-Jul-25 23:13:07.207463 - DEBUG - searchJSON <18.9> found thru <result[].Temp>
    26-Jul-25 23:13:07.207555 - DEBUG - Domoticz raw value <18 punt 9>
    26-Jul-25 23:13:07.207675 - DEBUG - searchJSON <> found thru <slots[?entity=='speakpartialtext'].value.value>
    26-Jul-25 23:13:07.207767 - DEBUG - Speak response / Domoticz value / count ['het is', '0', '1', '2', 'graden'] | ['18', 'punt', '9'] | 3
    26-Jul-25 23:13:07.208153 - DEBUG - Word text <het is>
    26-Jul-25 23:13:07.208276 - DEBUG - Lower case text to translate <18>
    26-Jul-25 23:13:07.208358 - DEBUG - No specific translation found for <18>
    26-Jul-25 23:13:07.208438 - DEBUG - Word id   <18>
    26-Jul-25 23:13:07.208520 - DEBUG - Lower case text to translate <punt>
    26-Jul-25 23:13:07.208616 - DEBUG - No specific translation found for <punt>
    26-Jul-25 23:13:07.208698 - DEBUG - Word id   <punt>
    26-Jul-25 23:13:07.208779 - DEBUG - Lower case text to translate <9>
    26-Jul-25 23:13:07.208857 - DEBUG - No specific translation found for <9>
    26-Jul-25 23:13:07.208940 - DEBUG - Word id   <9>
    26-Jul-25 23:13:07.209017 - DEBUG - Word text <graden>
    26-Jul-25 23:13:07.209188 - DEBUG - Domoticz sentence for device <Temperatuur Buiten (idx=38) > is ' het is 18 punt 9 graden'
    26-Jul-25 23:13:07.209506 - DEBUG - Sentence to speak on <sat1>
    26-Jul-25 23:13:07.209727 - INFO - Intent finished processing <dzGetDevices> and waiting new intent.

# Appendix - Device status details
List is based on https://wiki.domoticz.com/Developing_a_Python_plugin#Available_Device_Types

✅ available in current version
💡 to do
❌ not foreseen (yet)

| Type | Subtype | Retrieve | Update |
| :--- | :--- | :---: | :---: |
| Air Quality |  | 💡 |  ❌ |
| Camera  | Snapshot | 💡 |  ❌ |
| Color Switch  |  | 💡 | 💡 |
| Counter |  | 💡 |💡 |
| Current |  | ✅ |  ❌ |
| General  |  | ✅ | 💡 |
| Humidity |  | 💡 |  ❌ |
| Light/Switch | Selector Switch | ✅ |  💡 |
| Light/Switch | Switch | ✅ | ✅ |
| Lighting 2 |  | See Light/Switch |  See Light/Switch |
| Lux  |  | 💡 |  ❌ |
| P1 Smart Meter  |  | ✅ |  ❌ |
| Rain |  | 💡 | ❌ |
| RFX Meter  |  | ✅ |  ❌ |
| Scale |  | 💡 |  ❌ |
| Scenes  |  | 💡 |  💡 |
| Security  |  | ✅ |  💡 |
| Setpoint | Setpoint | ✅ | ✅ |
| Temp |  | ✅ |  💡 |
| Temp+Baro  |  | 💡 |  ❌ |
| Temp+Hum |  | ✅ | ❌ |
| Temp+Hum+Baro |  | ✅ | ❌ |
| Usage  |  | ✅ |  ❌ |
| UV |  | 💡 | ❌ |
| Wind |  | ✅ | ❌ |

# Plugin remarks
Version 1 of this integration (so published releases `v1.0.141` and `v1.1.6`) had been built via the Domomticz framework. That development was advised to cancel:
`Reply from Domoticz moderator: This plugin does not make an interface with hardware, it interfaces with Domoticz and a voice assitant application.
I am not saying it will not work as a plugin but the better way would be to have it as a separate python script/service installed somewhere on your system and so run it outside Domoticz.`
See https://forum.domoticz.com/viewtopic.php?p=324019#p324019
The `plugin.py` file is removed from the environment.
