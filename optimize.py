#!/usr/bin/env python3
'''Main module for heating optimization'''

import json
import time
from pathlib import Path

import schedule

from devices.device import Device # pylint: disable=import-error
from devices.panel import Panel # pylint: disable=import-error
from devices.thermostat import Thermostat # pylint: disable=import-error
from devices.heatpump import HeatPump # pylint: disable=import-error

def setHeating(target: Device) -> None:
    '''Set heating based on current status and api-spot-hinta.fi data.'''
    #Printataan perustiedot
    name = target.getName()
    timestamp = time.localtime(time.time())
    strTime = time.strftime('%H:%M:%S (%a %d %b)', timestamp)
    print(f'Kello on {strTime}. Asetetaan säädöt kohteeseen: {name}')

    #Käydään hakemassa tämän hetkinen tilanne termarilta
    status = target.getCurrentStatus()
    if not status:
        print('Laitteeseen ei saatu yhteyttä ja säätöä ei jatketa. Yritetään ' \
              'tunnin päästä uudelleen.')
        return

    #Käydään hakemassa API:lta lämmityksen tarve
    heating = target.getHeatingDemand()
    #Asetetaan lämmitys seuraavalle tunnille saatujen tietojen perusteella
    successful = target.adjustTempSetpoint(status, heating)
    if not successful:
        print('Lämpötilan asettaminen laitteeseen epäonnistui.')
    else:
        target.plotHistory()

def getDeviceType(file) -> str:
    '''Get device type from configuration file.'''
    with open(file, 'r', encoding='utf-8') as jsonFile:
        data = jsonFile.read()
    parsedData = json.loads(data)
    return parsedData[0]['type']

def createObject(file: Path) -> Device:
    '''Create device object based on configuration file.'''
    deviceType = getDeviceType(file)
    match deviceType:
        case 'panel':
            device = Panel(file)
        case 'thermostat':
            device = Thermostat(file)
        case 'heatpump':
            device = HeatPump(file)
        case _:
            print(f'Tiedostossa {file} on tuntematon laitetyyppi {deviceType}, objektia ei luoda.')
            return None
    return device

def readConfigs(devices: list) -> list[Device]:
    '''Read configuration files and create device objects.'''
    devices.clear()
    configPath = 'configs/'
    filelist = Path(configPath).rglob('*.json')
    for file in filelist:
        if 'default.json' in str(file):
            continue
        print(f'Löytyi konfiguraatiotiedosto: {file}. Luodaan sille objekti ja ajastetaan säätö.')
        device = createObject(file)
        devices.append(device)
    return devices

def main() -> None:
    '''Main function to run the heating optimization.'''
    devices = []
    # Luodaan objektit jokaiselle ohjattavalle kohteelle. Annetaan nimet ja IP-osoitteet
    devices = readConfigs(devices)
    #Ajastetaan säätöfunktio jokaiselle kohteelle
    baseTime = 10
    for device in devices:
        schedule.every().hour.at(f'01:{baseTime}').do(setHeating, device)
        schedule.every().hour.at(f'16:{baseTime}').do(setHeating, device)
        schedule.every().hour.at(f'31:{baseTime}').do(setHeating, device)
        schedule.every().hour.at(f'46:{baseTime}').do(setHeating, device)
        baseTime += 2
    schedule.run_all()
    while True:
        schedule.run_pending()
        time.sleep(30)




if __name__ == '__main__':
    main()
