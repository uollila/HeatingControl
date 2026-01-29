#!/usr/bin/env python3
'''Module for Device base class.'''

import json
import time
from collections import namedtuple
from pathlib import Path

import httpx

class Device:
    '''This provides the base class for the heating devices.'''

    def __init__(self, configPath: Path):
        self.configPath = configPath
        self.name = '' # This will be set in getConfiguration
        self.ipAddress = '' # This will be set in getConfiguration
        self.futurePlan = []
        self.planExpiration = 0
        self.sensorMode = None

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

    def getIpAddress(self) -> str:
        '''Get IP address.'''
        if not self.ipAddress:
            self.getConfiguration()
        return self.ipAddress


    def getConfiguration(self) -> dict:
        '''Read first part of configuration from file.'''
        with open(self.configPath, 'r', encoding='utf-8') as jsonFile:
            data = jsonFile.read()
        parsedData = json.loads(data)
        self.name = parsedData[0]['name']
        self.sensorMode = parsedData[0]['sensorMode']
        self.ipAddress = parsedData[0]['ip']
        return parsedData[0]

    def getApiConfiguration(self) -> dict:
        '''Read second part of configuration from file.'''
        with open(self.configPath, 'r', encoding='utf-8') as jsonFile:
            data = jsonFile.read()
        parsedData = json.loads(data)
        return parsedData[1]

    def getLocalTimeFromEpoch(self, epoch: int) -> str:
        '''Convert epoch milliseconds to local time string.'''
        epochToLocal = time.localtime(epoch // 1000)
        strTimeLocal = time.strftime('%H:%M:%S (%a %d %b)', epochToLocal)
        return strTimeLocal

    def getHeatingValuesFromFuturePlan(self, epoch: int) -> bool:
        '''Get heating values from future plan.'''
        returnValue = False
        setDone = False
        expirationLocalTime = self.getLocalTimeFromEpoch(self.planExpiration)
        print(f'Tuleva suunnitelma, joka vanhenee {expirationLocalTime}:')
        for item in self.futurePlan:
            planTimeLocal = self.getLocalTimeFromEpoch(item['epochMs'])
            if epoch > item['epochMs']and not setDone:
                print(f'Aika: {planTimeLocal}, Lämmitystarve: {item['result']} (VOIMASSA NYT)')
                returnValue = item['result']
                setDone = True
            else:
                print(f'Aika: {planTimeLocal}, Lämmitystarve: {item['result']}.')
        if not setDone:
            print('Ei löytynyt sopivaa aikaväliä tulevasta suunnitelmasta, ' \
                  'käytetään backup-tunteja.')
            hour = time.localtime(epoch // 1000).tm_hour
            backupHours = self.getApiConfiguration()['BackupHours']
            if hour in backupHours:
                returnValue = True
        return returnValue

    def getHeatingDemand(self) -> bool:
        '''Get heating demand from future plan or fetch new plan if needed.'''
        timestamp = time.time()
        timeMillis = int(timestamp * 1000)
        if timeMillis > self.planExpiration or not self.futurePlan:
            gotNewPlan = self.getNewPlan()
            if not gotNewPlan:
                print('api-spot-hinta.fi:stä ei saatu tarvittavia tietoja. ' \
                      'Käytetään asetettuja backup-tunteja.')
                hour = time.localtime(timestamp).tm_hour
                backupHours = self.getApiConfiguration()['BackupHours']
                if hour in backupHours:
                    return True
                return False
        return self.getHeatingValuesFromFuturePlan(timeMillis)

    def getNewPlan(self) -> bool:
        '''Get new heating plan from api-spot-hinta.fi.'''
        url = 'https://api.spot-hinta.fi/SmartHeating'
        data = self.getApiConfiguration()
        attempts = 3
        gotResponse = False
        for attempt in range(attempts):
            try:
                response = httpx.post(url, json=data)
                if response.status_code == 200:
                    gotResponse = True
                    responseJson = response.json()
                    self.futurePlan = responseJson['PlanAhead']
                    self.planExpiration = responseJson['EpochMsExpiration']
                    print(f'Saatiin uusi suunnitelma, voimasssa '
                          f'{self.getLocalTimeFromEpoch(self.planExpiration)} asti.\n' \
                          f'Vuorokauden keskilämpötila {responseJson['AverageTemperature']} C.')
                else:
                    print(f'Saatiin koodi {response.status_code}. Päättele siitä.')
            except httpx.RequestError:
                print(f'api-spot-hinta.fi ei vastannut. Yritetään 10 sekunnin ' \
                      f'päästä uudelleen. Yritys {attempt + 1} / {attempts}')
                time.sleep(10)
            else:
                return gotResponse
        return gotResponse

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

    def adjustTempSetpoint(self, status: dict, heating: bool) -> None:
        '''Adjust temperature setpoint based on current status and heating demand.'''
        temps = self.getTemps()
        currentTemp = status['parameters']['heatingSetpoint']
        if heating: #heating on
            return self.setTemp(temps.high, currentTemp)
        return self.setTemp(temps.low, currentTemp)

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
                    print(f'Laite vastasi koodilla {response.status_code}')
            except httpx.RequestError:
                print(f'Laitteeseen ei saatu yhteyttä. Yritetään 5 sekunnin ' \
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
