#!/usr/bin/env python3
'''Module for Panel class.'''
import time

import httpx

from devices.device import Device # pylint: disable=import-error

class Panel(Device):
    '''Class for panel device.'''

    def __init__(self, configPath: str):
        super().__init__(configPath)
        self.sensorMode = False

    def printStatus(self, responseJson: dict) -> None:
        '''Print current status of the panel.'''
        try:
            print(f'Patterin tämän hetken asetettu lämpötila ' \
                f'{responseJson['parameters']['heatingSetpoint']} C')
            print(f'Status: {responseJson['state']}, Huone: ' \
                f'{responseJson['roomTemperature']} C')
        except KeyError:
            print("Error: Could not retrieve status information from response.")

    def plotHistory(self):
        '''Plot history of panel data.'''
        print('\n\n')

    def _setTemp(self, newTemp: float, oldTemp: float) -> bool:
        '''Set new temperature to device.'''
        if newTemp == oldTemp:
            print(f'Ei tarvetta muuttaa lämpötilaa! Vanha ja uusi on samat {oldTemp} astetta.')
            return True
        url = f'http://{self._getIpAddress()}/api/parameters?heatingSetpoint' \
              f'={newTemp}&panelMode=1&sensorMode={self.sensorMode}'
        attempts = 5
        for attempt in range(attempts):
            try:
                response = httpx.post(url, timeout=10)
                if response.status_code == 200:
                    responseJson = response.json()
                    print(f'Patteriin asetettiin uusi lämpötila ' \
                          f'{responseJson['heatingSetpoint']} astetta.')
                else:
                    print(f'Patteri vastasi koodilla {response.status_code}')
            except httpx.RequestError:
                print(f'Patteriin ei saatu yhteyttä. Yritetään 5 sekunnin ' \
                      f'päästä uudelleen. Yritys {attempt + 1} / {attempts}')
                time.sleep(5)
            else:
                return True
        return False
