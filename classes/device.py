#!/usr/bin/env python3
'''Module for Device base class.'''

import json
import os
import time
from collections import namedtuple
from pathlib import Path

import httpx

class Device:
    '''This provides the base class for the configuration that is used in API-call to
       https://api.spot-hinta.fi/'''

    def __init__(self, configPath: Path):
        self.configPath = configPath
        self.name ='' # This will be set in getConfiguration
        self.ipAddress = '0.0.0.0'

    def getName(self) -> str:
        '''Get name of the device from configuration.'''
        if not self.name:
            self.getConfiguration()
        return self.name

    def getTemps(self) -> tuple[float, float]:
        '''Get low and high temperature settings from configuration.'''
        Temp = namedtuple('Temp', 'low high')
        data = self.getConfiguration()
        return Temp(data['tempLow'], data['tempHigh'])

    def setIpAddress(self) -> None:
        '''Set IP address from environment variable.'''
        defaultIp = '0.0.0.0'
        name = self.configPath.stem
        variable = 'ip_' + name
        ipAddress = os.getenv(variable, defaultIp)
        if ipAddress == defaultIp:
            print('Varoitus! IP:tä ei löytynyt ympäristömuuttujana. ' \
                  'Muista asettaa jokaiselle konfigurointitiedostolle ' \
                  'sopiva IP ympäristömuuttujaksi')
        self.ipAddress = ipAddress
        print(f'Asetettiin ip {self.ipAddress} kohteelle {self.getName()}.')

    def getIpAddress(self) -> str:
        '''Get IP address.'''
        return self.ipAddress


    def getConfiguration(self) -> dict:
        '''Read first part of configuration from file.'''
        with open(self.configPath, 'r', encoding='utf-8') as jsonFile:
            data = jsonFile.read()
        parsedData = json.loads(data)
        self.name = parsedData[0]['name']
        return parsedData[0]

    def getApiConfiguration(self) -> dict:
        '''Read second part of configuration from file.'''
        with open(self.configPath, 'r', encoding='utf-8') as jsonFile:
            data = jsonFile.read()
        parsedData = json.loads(data)
        return parsedData[1]

    def getHeatingDemand(self) -> dict:
        '''Get heating demand from api-spot-hinta.fi.'''
        url = 'https://api.spot-hinta.fi/SmartHeating'
        data = self.getApiConfiguration()
        attempts = 3
        responseJson = None
        for attempt in range(attempts):
            try:
                response = httpx.post(url, json=data)
                if response.status_code in [200, 400]:
                    responseJson = response.json()
                    print(f'api-spot-hinta.fi vastasi koodilla {response.status_code}\n' \
                          f'Peruste: {responseJson['StatusCodeReason']} Rank ' \
                          f'{responseJson['RankNow']}/{responseJson['CalculatedRank']}, ' \
                          f'hinta: {responseJson['PriceWithTaxInCentsModified']} senttiä.')
                else:
                    print(f'Saatiin koodi {response.status_code}. Päättele siitä.')
            except httpx.RequestError:
                print(f'api-spot-hinta.fi ei vastannut. Yritetään 10 sekunnin ' \
                      f'päästä uudelleen. Yritys {attempt + 1} / {attempts}')
                time.sleep(10)
            else:
                return responseJson
        return responseJson

    def setBackupHours(self, temps: tuple[float], currentTemp: float, hour: int) -> None:
        '''Set temperature based on backup hours if needed.'''
        backupHours = self.getApiConfiguration()['BackupHours']
        if hour in backupHours:
            return self.setTemp(temps.high, currentTemp)
        return self.setTemp(temps.low, currentTemp)


    def setTemp(self, newTemp: float, oldTemp: float) -> None:
        '''Set new temperature to device.'''
        if newTemp == oldTemp:
            print(f'Ei tarvetta muuttaa lämpötilaa! Vanha ja uusi on samat {oldTemp} astetta.')
            return True
        url = f'http://{self.getIpAddress()}/api/parameters?heatingSetpoint' \
              f'={newTemp}&operatingMode=1'
        attempts = 5
        for attempt in range(attempts):
            try:
                response = httpx.post(url)
                if response.status_code == 200:
                    responseJson = response.json()
                    print(f'Termostaatiin asetettiin uusi lämpötila ' \
                          f'{responseJson['heatingSetpoint']} astetta.')
                else:
                    print(f'Termostaatti vastasi koodilla {response.status_code}')
            except httpx.RequestError:
                print(f'Termostaattiin ei saatu yhteyttä. Yritetään 5 sekunnin ' \
                      f'päästä uudelleen. Yritys {attempt + 1} / {attempts}')
                time.sleep(5)
            else:
                return True
        return False

    def adjustTempSetpoint(self, status: dict, heatingDemand: dict, useBackup: bool,
                           hour: int) -> None:
        '''Adjust temperature setpoint based on current status and heating demand.'''
        temps = self.getTemps()
        currentTemp = status['parameters']['heatingSetpoint']
        if useBackup:
            return self.setBackupHours(temps, currentTemp, hour)
        responseCode = heatingDemand['HttpStatusCode']
        if responseCode == 200: #heating on
            return self.setTemp(temps.high, currentTemp)
        if responseCode == 400: #no heating
            return self.setTemp(temps.low, currentTemp)
        print('Tuntematon virhe. Käytetään backup-tunteja.')
        return self.setBackupHours(temps, currentTemp, hour)

    def getCurrentStatus(self) -> dict:
        '''Get current status from device.'''
        url = 'http://' + self.getIpAddress() + '/api/status'
        attempts = 5
        responseJson = None
        for attempt in range(attempts):
            try:
                response = httpx.get(url)
                if response.status_code == 200:
                    responseJson = response.json()
                    self.printStatus(responseJson)
                else:
                    print(f'Termostaatti vastasi koodilla {response.status_code}')
            except httpx.RequestError:
                print(f'Termostaattiin ei saatu yhteyttä. Yritetään 5 sekunnin ' \
                      f'päästä uudelleen. Yritys {attempt + 1} / {attempts}')
                time.sleep(5)
            else:
                return responseJson
        return responseJson

    def plotHistory(self) -> None:
        '''Plot history of temperature changes.'''
        # This should be implemented in subclasses
        raise NotImplementedError

    def printStatus(self, responseJson: dict) -> None:
        '''Print current status.'''
        # This should be implemented in subclasses
        raise NotImplementedError
