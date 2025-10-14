#!/usr/bin/env python3
'''Module for Device base class.'''

import httpx
import json
import os
import time
from collections import namedtuple
from pathlib import Path

class Device:
    '''Base class for all devices.'''

    def __init__(self, configPath: Path):
        self.configPath = configPath
        self.ipAddress = '0.0.0.0'

    def getTemps(self) -> tuple[float, float]:
        Temp = namedtuple('Temp', 'low high')
        data = self.getConfiguration()
        return Temp(data['tempLow'], data['tempHigh'])

    def setIpAddress(self) -> None:
        defaultIp = '0.0.0.0'
        name = self.configPath.stem
        variable = "ip_" + name
        ipAddress = os.getenv(variable, defaultIp)
        if ipAddress == defaultIp:
            print('Varoitus! IP:tä ei löytynyt ympäristömuuttujana. '
                  'Muista asettaa jokaiselle konfigurointitiedostolle '
                  'sopiva IP ympäristömuuttujaksi')
        self.ipAddress = ipAddress
        print(f"Asetettiin ip {self.ipAddress}.")

    def getIpAddress(self) -> str:
        return self.ipAddress

    def getConfiguration(self) -> dict:
        with open(self.configPath, "r", encoding="utf-8") as jsonFile:
            data = jsonFile.read()
        parsedData = json.loads(data)
        return parsedData[0]

    def getApiConfiguration(self) -> dict:
        with open(self.configPath, "r", encoding="utf-8") as jsonFile:
            data = jsonFile.read()
        parsedData = json.loads(data)
        return parsedData[1]

    def getHeatingDemand(self) -> dict:
        url = "https://api.spot-hinta.fi/SmartHeating"
        data = self.getApiConfiguration()
        attempts = 3
        responseJson = None
        for attempt in range(attempts):
            try:
                response = httpx.post(url, json=data)
                if response.status_code == 200 or response.status_code == 400:
                    responseJson = response.json()
                    print(f'''api-spot-hinta.fi vastasi koodilla {response.status_code}\n'''
                          f'''Peruste: {responseJson['StatusCodeReason']} Rank '''
                          f'''{responseJson['RankNow']}/{responseJson['CalculatedRank']}, '''
                          f'''hinta : {responseJson['PriceWithTaxInCentsModified']} senttiä.''')
                else:
                    print(f'Saatiin koodi {response.status_code}. Päättele siitä.')
            except httpx.RequestError as exc:
                print(f"api-spot-hinta.fi ei vastannut. Yritetään 10 sekunnin päästä uudelleen.")
                time.sleep(10)
            else:
                return responseJson
        return responseJson

    def setBackupHours(self, temps: tuple[float], currentTemp: float, hour: int) -> None:
        backupHours = self.getApiConfiguration()["BackupHours"]
        if hour in backupHours:
            return self.setTemp(temps.high, currentTemp)
        else:
            return self.setTemp(temps.low, currentTemp)

    def setTemp(self, newTemp: float, oldTemp: float) -> None:
        if newTemp == oldTemp:
            print(f'Ei tarvetta muuttaa lämpötilaa! Vanha ja uusi on samat {oldTemp} astetta.')
            return True
        url = f'''http://{self.getIpAddress()}/api/parameters?heatingSetpoint=
              {newTemp}&operatingMode=1'''
        attempts = 5
        for attempt in range(attempts):
            try:
                response = httpx.post(url)
                if response.status_code == 200:
                    responseJson = response.json()
                    print(f'''Termostaatiin asetettiin uusi lämpötila
                          {responseJson['heatingSetpoint']} astetta.''')
                else:
                    print(f'Termostaatti vastasi koodilla {response.status_code}')
            except httpx.RequestError as exc:
                print(f"Termostaattiin ei saatu yhteyttä. Yritetään 5 sekunnin päästä uudelleen.")
                time.sleep(5)
            else:
                return True
        return False

    def adjustTempSetpoint(self, status: dict, heatingDemand: dict, useBackup: bool,
                           hour: int) -> None:
        temps = self.getTemps()
        currentTemp = status['parameters']['heatingSetpoint']
        if useBackup:
            return self.setBackupHours(temps, currentTemp, hour)
        else:
            responseCode = heatingDemand["HttpStatusCode"]
            if responseCode == 200: #heating on
                return self.setTemp(temps.high, currentTemp)
            if responseCode == 400: #no heating
                return self.setTemp(temps.low, currentTemp)
            else:
                print(f"Tuntematon virhe. Käytetään backup-tunteja.")
                return self.setBackupHours(temps, currentTemp, hour)

    def getCurrentStatus(self) -> dict:
        # This should be implemented in subclasses
        raise NotImplementedError

    def plotHistory(self):
        # This should be implemented in subclasses
        raise NotImplementedError
