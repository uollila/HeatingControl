# HeatingControl

Lightweight Python service to control HeatIt Wifi6 thermostats, HeatIt Wifi panel heaters and devices with Home Assistant integration using spot-hinta.fi pricing data.

Supported devices

- HeatIt Wifi6 thermostat — <https://documents.heatit.com/54305-04>  
- HeatIt Wifi panel heater — <https://documents.heatit.com/54304-02>
- Device with HA integration. Requires that device has climate entity.
  - Tested with Panasonic heat pump with Panasonic comfort cloud integration.
  - Tested with Mitsubishi heat pump with MELCloud Home integration.

Requirements

- Python 3.12 or newer (the code uses newer f-string syntax and `match`)
- pip packages listed in the requirements.txt
- HeatIt devices in local network with fixed IP addresses
- For `heatpump` type devices: Home Assistant reachable through its REST API,
  with `HA_URL` and `HA_TOKEN` environment variables set

## Setup and running

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Only needed for heatpump type devices:
export HA_URL="http://your-home-assistant:8123"
export HA_TOKEN="<long-lived access token>"

python optimize.py
```

The configuration editor is available at `http://127.0.0.1:8080/` while the
service is running. The listener is local-only by default. Set
`CONFIG_WEB_HOST` and `CONFIG_WEB_PORT` before starting the service to change
the listening address or port. Do not expose the editor outside a trusted
network; it has no authentication.

The service runs in the foreground; run it under systemd, tmux/screen or
`nohup python optimize.py &` to keep it alive.

## Quickstart

1. Place one JSON configuration file per device in the `configs/` folder. Use the format in `configs/default.json`.
    - All required fields must be present or the script will fail.
    - IP is set correctly in the config file for each device. Use your router to assign static IPs or DHCP reservations so addresses remain stable.
    - With HA devices, the IP must be set to the id of the climate entity of the device.

2. Run script `python optimize.py`.
    - The script creates objects for each config file and schedules heating according to the configuration.
    - On startup every device is adjusted once immediately, and after that every 15 minutes
      (at :01, :16, :31 and :46 past the hour; each additional device is offset by 2 seconds
      so devices are not polled at the same moment). Actions are logged to the console.

## Configuration overview

- First object in the JSON: local device settings — name, IP, type, tempLow, tempHigh, sensorMode, etc.
- Second object: API parameters used to request a heating plan from <https://api.spot-hinta.fi/SmartHeating>.
- `configs/default.json` is only a template and is never controlled. Every other `*.json`
  found under `configs/` is loaded and scheduled.
- Changes to an existing configuration are read on the next device adjustment. Adding,
  removing or changing a device's `type` requires restarting the service.

## Behaviour

- The service toggles between low and high setpoints rather than turning heating fully off.
- If device connectivity is lost the script will retry; existing device setpoints remain unchanged.
- If the spot-hinta.fi API is unreachable or the plan has no matching time slot, heating is
  switched on only during the `BackupHours` defined in the configuration.

## Tests

Tests use the standard library `unittest` and need no network access (all HTTP
calls are mocked). Run from the project root:

```bash
python3 -m unittest discover
```

This scans all test packages: `configweb/tests/`, `tests/` (optimize module),
`devices/tests/` and `apis/tests/`. A single package can be run with e.g.
`python3 -m unittest discover -s devices/tests`.

## Linting

The code is linted with pylint (included in requirements.txt). Run from the project root:

```bash
pylint optimize.py configweb devices apis tests
```

There is no pylint configuration file in the repository, and methods intentionally use
camelCase instead of the Python snake_case convention. To silence the resulting
`invalid-name` warnings, add `--disable=C0103`.

## Further information

- The spot-hinta.fi API does not have formal public docs; reference implementation:
<https://github.com/Spot-hinta-fi/Shelly/blob/main/Scripts/Shelly-SmartHeating-15.js>

## Contributing

Open issues or pull requests for improvements, bug fixes, or additional device support.
Open for any collaboration.
