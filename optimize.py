#!/usr/bin/env python3

import datetime
import time
import schedule
from pathlib import Path

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
        print('Lämpötilan asettaminen termostaattiin epäonnistui.')
    else:
        target.plotHistory()

def readConfigs(thermostats: list):
    thermostats.clear()
    configPath = "configs/"
    filelist = Path(configPath).rglob('*.json')
    for file in filelist:
        if "default.json" in str(file):
            continue
        print(f"Löytyi konfiguraatiotiedosto: {file}. Luodaan sille objekti ja ajastetaan säätö")
        thermostat = Thermostat(file)
        thermostat.setIpAddress()
        thermostats.append(thermostat)
    return thermostats

def main():
    thermostats = []
    # Luodaan objektit jokaiselle ohjattavalle kohteelle. Annetaan nimet ja IP-osoitteet
    thermostats = readConfigs(thermostats)
    #Ajastetaan säätöfunktio jokaiselle kohteelle
    baseTime = 30
    for thermostat in thermostats:
        schedule.every().hour.at(f"01:{baseTime}").do(setHeating, thermostat)
        baseTime += 10
    schedule.run_all()
    while True:
        schedule.run_pending()
        time.sleep(1)




if __name__ == '__main__':
    main()