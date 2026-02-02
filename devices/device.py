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
            self._getConfiguration()
        return self.name

    def _getTemps(self) -> tuple[float, float]:
        '''Get low and high temperature settings from configuration.'''
        Temp = namedtuple('Temp', 'low high')
        data = self._getConfiguration()
        return Temp(data['tempLow'], data['tempHigh'])

    def _getIpAddress(self) -> str:
        '''Get IP address.'''
        if not self.ipAddress:
            self._getConfiguration()
        return self.ipAddress


    def _getConfiguration(self) -> dict:
        '''Read first part of configuration from file.'''
        with open(self.configPath, 'r', encoding='utf-8') as jsonFile:
            data = jsonFile.read()
        parsedData = json.loads(data)
        self.name = parsedData[0]['name']
        self.sensorMode = parsedData[0]['sensorMode']
        self.ipAddress = parsedData[0]['ip']
        return parsedData[0]

    def _getApiConfiguration(self) -> dict:
        '''Read second part of configuration from file.'''
        with open(self.configPath, 'r', encoding='utf-8') as jsonFile:
            data = jsonFile.read()
        parsedData = json.loads(data)
        return parsedData[1]

    def _getLocalTimeFromEpoch(self, epoch: int) -> str:
        '''Convert epoch milliseconds to local time string.'''
        epochToLocal = time.localtime(epoch // 1000)
        strTimeLocal = time.strftime('%H:%M:%S (%a %d %b)', epochToLocal)
        return strTimeLocal

    def _getHeatingValuesFromFuturePlan(self, epoch: int) -> bool:
        '''Get heating values from future plan.'''
        returnValue = False
        setDone = False
        expirationLocalTime = self._getLocalTimeFromEpoch(self.planExpiration)
        print(f'Tuleva suunnitelma, joka vanhenee {expirationLocalTime}:')
        for item in self.futurePlan:
            planTimeLocal = self._getLocalTimeFromEpoch(item['epochMs'])
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
            backupHours = self._getApiConfiguration()['BackupHours']
            if hour in backupHours:
                returnValue = True
        return returnValue

    def getHeatingDemand(self) -> bool:
        '''Get heating demand from future plan or fetch new plan if needed.'''
        timestamp = time.time()
        timeMillis = int(timestamp * 1000)
        if timeMillis > self.planExpiration or not self.futurePlan:
            gotNewPlan = self._getNewPlan()
            if not gotNewPlan:
                print('api-spot-hinta.fi:stä ei saatu tarvittavia tietoja. ' \
                      'Käytetään asetettuja backup-tunteja.')
                hour = time.localtime(timestamp).tm_hour
                backupHours = self._getApiConfiguration()['BackupHours']
                if hour in backupHours:
                    return True
                return False
        return self._getHeatingValuesFromFuturePlan(timeMillis)

    def _getNewPlan(self) -> bool:
        '''Get new heating plan from api-spot-hinta.fi.'''
        url = 'https://api.spot-hinta.fi/SmartHeating'
        data = self._getApiConfiguration()
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
                          f'{self._getLocalTimeFromEpoch(self.planExpiration)} asti.\n' \
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

    def _getCurrentTemperature(self, status: dict) -> float:
        '''Get current temperature from status dictionary.'''
        return status['parameters']['heatingSetpoint']

    def adjustTempSetpoint(self, status: dict, heating: bool) -> None:
        '''Adjust temperature setpoint based on current status and heating demand.'''
        temps = self._getTemps()
        currentTemp = self._getCurrentTemperature(status)
        if heating: #heating on
            return self._setTemp(temps.high, currentTemp)
        return self._setTemp(temps.low, currentTemp)

    def _getStatusResponse(self) -> httpx.Response:
        '''Get response for status query from device.'''
        url = 'http://' + self._getIpAddress() + '/api/status'
        response = httpx.get(url)
        return response

    def getCurrentStatus(self) -> dict:
        '''Get current status from device.'''
        attempts = 5
        responseJson = None
        for attempt in range(attempts):
            try:
                response = self._getStatusResponse()
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

    def _setTemp(self, newTemp: float, oldTemp: float) -> bool:
        '''Set new temperature to device.'''
        # This should be implemented in subclasses
        raise NotImplementedError

    def plotHistory(self) -> None:
        '''Plot history of temperature changes.'''
        # This should be implemented in subclasses
        raise NotImplementedError

    def printStatus(self, responseJson: dict) -> None:
        '''Print current status.'''
        # This should be implemented in subclasses
        raise NotImplementedError
