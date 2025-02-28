# Plugin remarks
`Reply from Domoticz moderator: This plugin does not make an interface with hardware, it interfaces with Domoticz and a voice assitant application.
I am not saying it will not work as a plugin but the better way would be to have it as a separate python script/service installed somewhere on your system and so run it outside Domoticz.`
See https://forum.domoticz.com/viewtopic.php?p=324019#p324019

I've started to rework and will publish new approach on short notice.

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
2. `MQTT up and running`: for communication between Rhasspy and this plugin (vice versa).
3. `Recent Domoticz`: supporting new API structures and extended plugin framework.

# Rhasspy
## Intents, Sentences and Slots
Based on an example the structure of sentences in Rhasspy relevant to Domoticz is explained. First the intents are explained and next the sentences within the intents.
### Intents
Every intent that needs to be interpreted by Domoticz needs to start with `dz` succeeded by an API command for Domoticz, for instance `switchlight`. The intent text in the plugin
is not case sensitive (everything will be converted to lowercase by the plugin).

Currently supported API commands of Domoticz (see for details https://wiki.domoticz.com/Domoticz_API/JSON_URL's and the appendix chapter at the end of this readme document):
  1. [dzswitchlight] - So Domoticz type `Light/Switch`, update the state.
  2. [dzgetdevices] - So actual value of a Domoticz device, report the value.
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

    mach das Küchenlicht`{device:Licht} (an:on | aus:off){state}(:){speakresponse:`Das Licht in der Küche ist`}

    [GetTime]

    wie spät is es.

    [dzGetDevices]

    wie ist der Status der Küchenlampe{device:Licht}(:){speakresponse:`Die Lampe in der Küche ist`}

In this case the intent [GetTime] will not be processed in the plugin (as it lacks the prefix `dz`).
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

![Base Master](https://github.com/user-attachments/assets/2269182f-0bbe-4f2e-aee6-e449b482d761)

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
## A. Plugin
1. Open a `PuTTY` session.
2. In the session go to the `Plugin` folder of Domoticz.
3. Download the plugin: `git clone https://github.com/TurnOfAFriendlyCard/Domoticz-Rhasspy-Plugin`
4. Alternative is to download and extract the zip file:
   - Go to https://github.com/TurnOfAFriendlyCard/Domoticz-Rhasspy-Plugin.
   - Click on Code and select Download ZIP.
   - Create a folder for the plugin (`mkdir Domoticz-Rhasspy`) in the `Plugin` folder of Domoticz.
5. Go to folder (`cd Domoticz-Rhasspy`).
6. Make the plugin.py file executable (`chmod 755 plugin.py`).
7. Install module jmespath: `pip3 install jmespath`. This is required for searching in JSON structures.
8. Install module deepl: `pip3 install deepl-translate`. This is required for translating Domoticz states and values into local language (so for instance `aus` in `off`).
9. Restart Domoticz.

## B. Domoticz
1. In the hardware tab a new `type` will be available: `Rhasspy Voice Assistant`.
2. Create the new hardware:
   - Enter a logical `name` (for instance `Rhasspy`).
   - Select the hardware `type` `Rhasspy Voice Assistant`.
   - Enter the IP address of the MQTT server (for instance `192.168.200.1`). Required for Rhasppy integration.
   - Enter the port of the MQTT server (for instance `1883`)
   - Enter the IP address of the Domoticz server (for instance `192.168.100.1`). Required for API integration.
   - Enter the port of the Domoticz server (for instance `8080`). Will be HTTP connection.
   - Enter Rhassy site(s) for audio. Needs to be same as setup in Rhasspy itself. Example: `master`.
   - When required debug message can be shown in the Domoticz log (set required debuglevel from dropdown).
   - Press Add to complete the installation.

## C. Rhasspy
1. The language used by Rhasspy needs to be communicated to the plugin. In Rhasspy go the Advanced menu, so the profile.json will be presented.
2. Add to the intent section the text `"lang": "nl"` (replace the actual language used).
3. The profile.json will look like next:
    },
    "intent": {
        "satellite_site_ids": "sat1",
        "system": "fsticuffs",
        "lang": "nl"
    },
    "mqtt": {
        "enabled": "true",
4. Save the profile and restart Rhasspy.
  
Enjoy your **Rhasspy Domoticz integration** 😁

# Appendix - Device status details
List is conform https://wiki.domoticz.com/Developing_a_Python_plugin#Available_Device_Types

✅ available in current version
💡 to do
❌ not foreseen (yet)

| Type | Subtype | Retrieve | Update |
| :--- | :--- | :--- | :--- |
| Lighting 2 |  | See Light/Switch | See Light/Switch |
| Temp |  | ✅ | 💡 |
| Humidity |  | 💡 | ❌ |
| Temp+Hum |  | 💡 | ❌ |
| Temp+Hum+Baro |  | 💡 | ❌ |
| Rain |  | 💡 | ❌ |
| Wind |  | 💡 | ❌ |
| UV |  | 💡 | ❌ |
| Current |  | 💡 | ❌ |
| Scale |  | 💡 | ❌ |
| Counter |  | 💡 | 💡 |
| Color Switch  |  | 💡 | 💡 |
| Thermostat  |  | ✅ | 💡 |
| General  |  | 💡 | 💡 |
| General  | Text | ✅ | 💡 |
| Light/Switch | Selector Switch | ✅ | 💡 |
| Light/Switch | Switch | ✅ | ✅ |
| Lux  |  | 💡 | ❌ |
| Temp+Baro  |  | 💡 | ❌ |
| Usage  |  | 💡 | ❌ |
| Air Quality |  | 💡 | ❌ |
| P1 Smart Meter  |  | 💡 | ❌ |
| Security  |  | 💡 | 💡 |
| Camera  | Snapshot | 💡 | ❌ |
| Scenes  |  | 💡 | 💡 |
