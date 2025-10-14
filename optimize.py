#!/usr/bin/env python3

import datetime
import json
import time
import schedule
from pathlib import Path

from device import Device
from panel import Panel
from thermostat import Thermostat

def setHeating(target: Thermostat) -> None:

    #Printataan perustiedot
    name = target.getConfiguration()['name']
    timestamp = time.localtime(time.time())
    useBackup = False
    strTime = time.strftime("%H:%M:%S (%a %d %b)", timestamp)
    print(f"Kello on {strTime}. Asetetaan säädöt kohteeseen: {name}")

    #Käydään hakemassa tämän hetkinen tilanne termarilta
    status = target.getCurrentStatus()
    if (not status):
        print("Termostaattiin ei saatu yhteyttä ja säätöä ei jatketa. Yritetään tunnin päästä uudelleen.")
        return

    #Käydään hakemassa API:lta lämmityksen tarve
    heatingDemand = target.getHeatingDemand()
    if (not heatingDemand):
        print("api-spot-hinta.fi:stä ei saatu tarvittavia tietoja. Käytetään asetettuja backup-tunteja.")
        useBackup = True

    #Asetetaan lämmitys seuraavalle tunnille saatujen tietojen perusteella
    hour = timestamp.tm_hour
    successful = target.adjustTempSetpoint(status, heatingDemand, useBackup, hour)
    if not successful:
        print("Lämpötilan asettaminen termostaattiin epäonnistui.")
    else:
        target.plotHistory()

def getDeviceType(file) -> str:
    with open(file, "r") as json_file:
        data = json_file.read()
    parsed_data = json.loads(data)
    return parsed_data[0]['type']

def createObject(file: Path) -> Device:
    deviceType = getDeviceType(file)
    match deviceType:
        case "panel":
            device = Panel(file)
        case "thermostat":
            device = Thermostat(file)
        case _:
            print(f"Tiedostossa {file} on tuntematon laitetyyppi {deviceType}, objektia ei luoda.")
            return None
    device.setIpAddress()
    return device

def readConfigs(devices: list) -> list[Device]:
    devices.clear()
    configPath = "configs/"
    filelist = Path(configPath).rglob('*.json')
    for file in filelist:
        if "default.json" in str(file):
            continue
        print(f"Löytyi konfiguraatiotiedosto: {file}. Luodaan sille objekti ja ajastetaan säätö")
        device = createObject(file)
        devices.append(device)
    return devices

def main() -> None:
    devices = []
    # Luodaan objektit jokaiselle ohjattavalle kohteelle. Annetaan nimet ja IP-osoitteet
    devices = readConfigs(devices)
    #Ajastetaan säätöfunktio jokaiselle kohteelle
    baseTime = 10
    for device in devices:
        schedule.every().hour.at(f"01:{baseTime}").do(setHeating, device)
        baseTime += 2
    schedule.run_all()
    while True:
        schedule.run_pending()
        time.sleep(30)




if __name__ == "__main__":
    main()
