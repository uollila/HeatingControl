#!/usr/bin/env python3
'''Module for Thermostat class.'''
import time

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
            print(f'Termostaatin tämän hetken asetettu ' \
                f'lämpötila {responseJson['parameters']['heatingSetpoint']} C.')
            print(f'Status: {responseJson['state']}, huone: ' \
                f'{responseJson['internalTemperature']} C, ' \
                f'lattia: {responseJson['floorTemperature']} C')
        except KeyError:
            print("Error: Could not retrieve status information from response.")

    def plotHistory(self) -> None:
        '''Plot history of thermostat data.'''
        print('\n\n')

    def _setTemp(self, newTemp: float, oldTemp: float) -> bool:
        '''Set new temperature to device.'''
        if newTemp == oldTemp:
            print(f'Ei tarvetta muuttaa lämpötilaa! Vanha ja uusi on samat {oldTemp} astetta.')
            return True
        url = f'http://{self._getIpAddress()}/api/parameters?heatingSetpoint' \
              f'={newTemp}&operatingMode=1&sensorMode={self.sensorMode}'
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
