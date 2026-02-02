#!/usr/bin/env python3
'''Module for Panasonic device class. Can control Panasonic heat pumps
that are connected to the Comfort Cloud app.'''

import os

import httpx

from apis.homeassistant import HomeAssistantClient  # pylint: disable=import-error
from devices.device import Device  # pylint: disable=import-error

class Panasonic(Device):
    '''Class for Panasonic heat pump device.'''
    def __init__(self, configPath: os.PathLike):
        super().__init__(configPath)
        self.client = self._initHomeAssistantClient()

    def printStatus(self, responseJson: dict) -> None:
        '''Print current status of the Panasonic heat pump.'''
        print(f'Panasonic lämpöpumpun tämän hetken asetettu ' \
              f'lämpötila {responseJson['attributes']['temperature']} C. ' \
              f'Huoneen lämpötila on ' \
              f'{responseJson['attributes']['current_temperature']} C. ')

    def plotHistory(self) -> None:
        '''Plot history of panel data.'''
        print('\n\n')

    def _initHomeAssistantClient(self) -> HomeAssistantClient:
        '''Initialize session to Home Assistant.'''
        url = os.getenv('HA_URL', 'default')
        token = os.getenv('HA_TOKEN', 'default')
        if url == 'default' or token == 'default':
            print('HA_URL tai HA_TOKEN ympäristömuuttujaa '\
                  'ei ole asetettu. Panasonic laitetta ei voida ohjata.')
            return None
        client = HomeAssistantClient(url, token)
        return client

    def _setTemp(self, newTemp: float, oldTemp: float) -> bool:
        '''Set new temperature to device.'''
        if newTemp == oldTemp:
            print(f'Ei tarvetta muuttaa lämpötilaa! Vanha ja uusi on samat {oldTemp} astetta.')
            return True
        try:
            self.client.setTemperature(self.ipAddress, newTemp)
            print(f'Panasonic lämpöpumppuun asetettiin uusi lämpötila {newTemp} astetta.')
        except httpx.RequestError as err:
            print(f'Lämpötilan asettaminen Panasonic lämpöpumppuun epäonnistui. '
                  f'Syy: {err}')
            return False
        return True

    def _getStatusResponse(self) -> httpx.Response:
        '''Get response for status query from device.'''
        return self.client.getState(self.ipAddress)

    def _getCurrentTemperature(self, status: dict) -> float:
        '''Get current temperature from status dictionary.'''
        return status['attributes']['temperature']
