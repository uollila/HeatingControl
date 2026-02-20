# HeatingControl

Lightweight Python service to control HeatIt Wifi6 thermostats, HeatIt Wifi panel heaters and devices with Home Assistant integration using spot-hinta.fi pricing data.

Supported devices

- HeatIt Wifi6 thermostat — <https://documents.heatit.com/54305-04>  
- HeatIt Wifi panel heater — <https://documents.heatit.com/54304-02>
- Device with HA integration. Requires that device has climate entity.
  - Tested with Panasonic heat pump with Panasonic comfort cloud integration.
  - Tested with Mitsubishi heat pump with MELCloud Home integration.

Requirements

- Python 3.9+
- pip packages listed in the requirements.txt
- Devices are in local network with fixed IP address  

## Quickstart

1. Place one JSON configuration file per device in the `configs/` folder. Use the format in `configs/default.json`.
    - All required fields must be present or the script will fail.
    - IP is set correctly in the config file for each device. Use your router to assign static IPs or DHCP reservations so addresses remain stable.
    - With HA devices, the IP must be set to the id of the climate entity of the device.

2. Run script `python optimize.py`.
    - The script creates objects for each config file and schedules heating according to the 
configuration
    - The script updates temperature setpoints every 15 minutes (aligned to :00, :15, :30, :45)
and logs actions to the console.

## Configuration overview

- First object in the JSON: local device settings — name, IP, type, tempLow, tempHigh, sensorMode, etc.
- Second object: API parameters used to request a heating plan from <https://api.spot-hinta.fi/SmartHeating>.

## Behaviour

- The service toggles between low and high setpoints rather than turning heating fully off.
- If device connectivity is lost the script will retry; existing device setpoints remain unchanged.

## Further information

- The spot-hinta.fi API does not have formal public docs; reference implementation:
<https://github.com/Spot-hinta-fi/Shelly/blob/main/Scripts/Shelly-SmartHeating-15.js>

## Contributing

Open issues or pull requests for improvements, bug fixes, or additional device support.
Open for any collaboration.
