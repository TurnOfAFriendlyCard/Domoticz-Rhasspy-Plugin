# Goal
This plugin captures Rhasspy voice requests and processes these requests in Domoticz and speaks feedback via Rhasspy.

# Description
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

# Prerequisites
1. `Rhasspy 2.5 up and running`: See for more information https://rhasspy.readthedocs.io/en/latest/. 
2. `Recent Domoticz`: supporting new API structures.

# Rhasspy
## Intents, Sentences and Slots
Based on an example the structure of sentences in Rhasspy relevant to Domoticz is explained. First the intents are explained and next the sentences within the intents.
### Intents
Every intent that needs to be interpreted by Domoticz needs to start with `dz` succeeded by an API command for Domoticz, for instance `switchlight`. The intent text in the plugin
is not case sensitive (everything will be converted to lowercase by the plugin).

Currently supported API commands of Domoticz (see for details https://wiki.domoticz.com/Domoticz_API/JSON_URL's and the appendix chapter at the end of this readme document):
  1. [dzswitchlight] - So on/off open/close switches.
  2. [dzsetsetpoint] - Update setpoint device like heating thermostat (available as from v3).
  3. [dzgetdevices] - So actual value of a Domoticz device, report the value.
### Sentences
Besides the sentence rules of Rhasspy every sentence consists of next blocks:
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
This will be communicated to Domoticz as `on` or `off`. If language Rhasspy and Domoticz are the same, the translation can be omitted (so `(an | aus){state}` for both German). The field for Domoticz to capture the state of the device is {state}.
- (:){speakresponse:`Das Licht in der Küche ist`
  * The text to be spoken by Rhasspy after processing by Domoticz. The actual status will be captured and added to this text. If status is `on` this will be translated to German as `an`.

### Sample sentence.ini
Next would be a valid setup within Rhasspy of the sentence.ini file:

    [dzSwitchLight]

    mach das Küchenlicht`{device:Licht} (an:on | aus:off){state}(:){speakresponse:Das Licht in der Küche ist}

    [GetTime]

    wie spät is es.

    [dzGetDevices]

    wie ist der Status der Küchenlampe{device:Licht}(:){speakresponse:Die Lampe in der Küche ist}

In this case the intent [GetTime] will not be processed in the plugin (as it lacks the prefix `dz`).

### Partial texts
Status text retrieved from a device status can consists of multiple parts. For instance take a `Temp + Humidity + Baro` device. This extracts next data components:
- `11.1` Temperature
- `49.0` Humidity
- `Comfortable` HumidityStatus
- `1025.0` Barometer
- `Some Clouds` ForecastStr

This results in next string to be spoken in Rhasspy:
`11 point 1 degrees. humidity 49 percent means Comfortable.  air pressure 1025 and Some Clouds`

Suppose you are only interested in the humidity to be spoken. You can configure this via the `speakpartialtext` option in sentence.ini:

    [dzGetDevices]

    what is humidity{device:TempHumBaro}(:){speakresponse:humidity is}(:){speakpartialtext:5,6}

So just count the words (starting with zero as the first word - so `11` from the example Rhasspy spoken text would be the first word).~~

As from vs 3 the `speakpartialtext` functionality is integrated into the `speakresponse` tag (and `speakpartialtext` tag will be deprecated in next version). 
So would be something like `(:){speakresponse:humidity is;3;percent}`.
Retrieved base values from a device type `Temp + Humidity + Baro` are for example: `11 point 1 49 Comfortable 1025 Some Clouds`.
Feedback will be spoken as `humidity is 49 percent`. So fixed texts are `humidity is` and `percent` where the `3` refers to the 3rd value in the reported values counting the first field as zero.
Bear in mind the blocks after the `speakresponse` tag are separated by a semi-colon (so `;`).
In this way you can build you own reporting feedback to be spoken mixing fixed text and values from Domoticz.

Also new functionality is to suppress the feedback of the actual state by a device (as from vs 3 as well). The German example of the kitchenlight reports the actual state.
If you would amend the sentence to `(:){speakresponse:Das Licht in der Küche ist}(:){speakstate:no}` no actual state would be spoken.

### Slots
It is possible to process slots as spoken device names defined in Rhasspy. The sentence.ini file in Rhasspy would like this:

    [dzGetDevices]

    what is [the] $domoticz/temperature{device:Temperature Outside}(:){speakresponse:The temperature outside is}

The slot `domoticz/temperature` would look like this:

    (temperature outside | outside temperature | out temperature)

Also placing the devicename in the slot is possible:

    [dzGetDevices]

    what is [the] $domoticz/temperature(:){speakresponse:The temperature outside is}

The slot `domoticz/temperature` would look like this:

    (temperature outside | outside temperature | out temperature){device:Temperature Outside}
## Typical Setup Rhasspy
My current setup is `Base-Satellite` (Base Rhasspy under Docker on NAS and Satellite Rhasspy under Docker on RPi3).
![Rhasspy](https://github.com/user-attachments/assets/e539f4a2-1ee0-424c-ab21-19f3d169fa83)

![Base Master v2](https://github.com/user-attachments/assets/d9d8001d-7c9a-43eb-acdd-033252446d3c)

# Domoticz
## User variables
The device name to be supplied in the sentence or slot in Rhasspy should be the actual device name. One way to be flexible in Domoticz on device names is to define a user variable representing the device.

User variables in Domoticz are defined in Setup, More options, User variables. Example is:

- Variable name: 	TempOut
- Variable type: 	String
- Variable value: Outside Temperature	

So `Outside Temperature` is the actual device name, but the variable `TempOut` can be used in Rhasspy and Domoticz.
So you could stay independant of changing your device names in Domoticz and also having tp change your Rhasspy sentences and slots.
I'm using user variables for devices (ao) in DzVents as well (so would look like this: `if (domoticz.devices(domoticz.variables('SensorGarageDoor').value).state == 'Open'`).

Bear in mind, this is `optional` functionality. You can still use the actual device name in the sentence.ini. So two options.

# INSTALLATION

Two methods can be implemented: 1) via Local Command script or 2) via MQTT service script (as from vs3).

## Local Command Script

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
8. Install module deepl: `pip3 install deepl-translate`. This is required for translating Domoticz states and values into local language (so for instance `aus` in `off`).

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

## MQTT service Script

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
7. Install module jmespath: `pip3 install jmespath`. This is required for searching in JSON structures.
8. Install module deepl: `pip3 install deepl-translate`. This is required for translating Domoticz states and values into local language (so for instance `aus` in `off`).
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

# Appendix - Device status details
List is conform https://wiki.domoticz.com/Developing_a_Python_plugin#Available_Device_Types

✅ available in current version
💡 to do
❌ not foreseen (yet)

| Type | Subtype | Retrieve | Partial Response | Update |
| :--- | :--- | :---: | :---: |:---: |
| Lighting 2 |  | See Light/Switch | See Light/Switch | See Light/Switch |
| Temp |  | ✅ | ❌ | 💡 |
| Humidity |  | 💡 | 💡 | ❌ |
| Temp+Hum |  | ✅ | ✅ |❌ |
| Temp+Hum+Baro |  | ✅ | ✅ |❌ |
| Rain |  | 💡 |💡 | ❌ |
| Wind |  | 💡 |💡 | ❌ |
| UV |  | 💡 |💡 | ❌ |
| Current |  | 💡 | ❌| ❌ |
| Scale |  | 💡 | 💡 | ❌ |
| Counter |  | 💡 | ❌ |💡 |
| Color Switch  |  | 💡 |💡 | 💡 |
| Setpoint | Setpoint | ✅ |✅ | 💡 |
| General  |  | 💡 |💡 | 💡 |
| General  | Text | ✅ | ✅ | 💡 |
| Light/Switch | Selector Switch | ✅ | 💡| 💡 |
| Light/Switch | Switch | ✅ | ❌ |✅ |
| Lux  |  | 💡 | 💡 | ❌ |
| Temp+Baro  |  | 💡 | 💡 | ❌ |
| Usage  |  | 💡 | 💡 | ❌ |
| Air Quality |  | 💡 | 💡 | ❌ |
| P1 Smart Meter  |  | 💡 | 💡 | ❌ |
| Security  |  | 💡 | 💡 | 💡 |
| Camera  | Snapshot | 💡 | 💡 | ❌ |
| Scenes  |  | 💡 | 💡 | 💡 |

# Plugin remarks
Version 1 of this integration (so published releases `v1.0.141` and `v1.1.6`) had been built via the Domomticz framework. That development was advised to cancel:
`Reply from Domoticz moderator: This plugin does not make an interface with hardware, it interfaces with Domoticz and a voice assitant application.
I am not saying it will not work as a plugin but the better way would be to have it as a separate python script/service installed somewhere on your system and so run it outside Domoticz.`
See https://forum.domoticz.com/viewtopic.php?p=324019#p324019
The `plugin.py` file will be removed from the environment.
