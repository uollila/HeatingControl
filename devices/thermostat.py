#!/usr/bin/env python3
'''Module for Thermostat class.'''

import httpx

from devices.device import Device # pylint: disable=import-error

class Thermostat(Device):
    '''Thermostat class inherits from Device class.'''

    def __init__(self, configPath: str):
        super().__init__(configPath)
        self.sensorMode = 2

    def printStatus(self, responseJson: dict) -> None:
        '''Print current status of the thermostat.'''
        try:
            setTemp = responseJson['parameters']['heatingSetpoint']
            currentTemp = responseJson['internalTemperature']
            self.printTemps(setTemp, currentTemp)
            print(f'lattia: {responseJson['floorTemperature']} C')
        except KeyError:
            print('Ei saatu kunnon vastausta termostaatilta.')

    def plotHistory(self) -> None:
        '''Plot history of thermostat data.'''
        print('\n\n')

    def sendTempToDevice(self, newTemp: float) -> httpx.Response:
        '''Send new temperature to thermostat.'''
        url = f'http://{self.getIpAddress()}/api/parameters?heatingSetpoint' \
              f'={newTemp}&operatingMode=1&sensorMode={self.sensorMode}'
        response = httpx.post(url, timeout=10)
        return response
