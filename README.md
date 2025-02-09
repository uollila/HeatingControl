# HeatingControl
Python script to control underfloor heating with HeatIt Wifi6 thermostat.

# Usage

1. Create configiguration .json-file for each thermostat into the configs-folder. 
Use the format specified in the default.json file. All fields are required.

2. Set IP-address of each thermostat as an environmental variable. The variable name
should be "ip_<config_file_name_without_file_extension>".

3. Run script "python3 optimize.py". It sets thermostat themperatures every hour
according to the configuration.
