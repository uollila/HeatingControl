#!/usr/bin/env python3
'''Module for Panel class.'''

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
            setTemp = responseJson['parameters']['heatingSetpoint']
            currentTemp = responseJson["roomTemperature"]
            self.printTemps(setTemp, currentTemp)
        except KeyError:
            print('Ei saatu kunnon vastausta patterilta.')

    def plotHistory(self):
        '''Plot history of panel data.'''
        print('\n\n')

    def sendTempToDevice(self, newTemp: float) -> httpx.Response:
        '''Send new temperature to panel.'''
        url = f'http://{self.getIpAddress()}/api/parameters?heatingSetpoint' \
              f'={newTemp}&panelMode=1&sensorMode={self.sensorMode}'
        response = httpx.post(url, timeout=10)
        return response
