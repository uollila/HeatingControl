# HeatingControl

Lightweight Python service to control HeatIt Wifi6 thermostats and HeatIt Wifi panel heaters using spot-hinta.fi pricing data.

Supported devices

- HeatIt Wifi6 thermostat — <https://documents.heatit.com/54305-04>  
- HeatIt Wifi panel heater — <https://documents.heatit.com/54304-02>

Requirements

- Python 3.9+
- pip packages: httpx, schedule
- Devices are in local network with fixed IP address  

## Quickstart

1. Place one JSON configuration file per device in the `configs/` folder. Use the format in `configs/default.json`.
    - All required fields must be present or the script will fail.

2. Provide each device IP using an environment variable named `ip_<config_filename_without_extension>`. Example, for `configs/eteinen.json`:
   `export ip_eteinen=192.168.1.10`
   - Use your router to assign static IPs or DHCP reservations so addresses remain stable.

3. Run script `python3 optimize.py`.
    - The script updates temperature setpoints every 15 minutes (aligned to :00, :15, :30, :45)
and logs actions to the console.

## Configuration overview

- First object in the JSON: local device settings — name, type, tempLow, tempHigh, sensorMode, etc.
- Second object: API parameters used to request a heating plan from <https://api.spot-hinta.fi/SmartHeating>.

## Behaviour

- The service toggles between low and high setpoints rather than turning heating fully off.
- If device connectivity is lost the script will retry; existing device setpoints remain unchanged.

## Further information

- The spot-hinta.fi API does not have formal public docs; reference implementation:
<https://github.com/Spot-hinta-fi/Shelly/blob/main/Scripts/Shelly-SmartHeating-15.js>

## Contributing

Open issues or pull requests for improvements, bug fixes, or additional device support.
