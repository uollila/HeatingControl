#!/usr/bin/env python3
'''Module for Panasonic device class. Can control Panasonic  and Mitsubishi heat pumps
that are connected to the Comfort Cloud app.'''

import os

import httpx

from apis.homeassistant import HomeAssistantClient  # pylint: disable=import-error
from devices.device import Device  # pylint: disable=import-error

class HeatPump(Device):
    '''Class for heat pump device connected to HA.'''
    def __init__(self, configPath: os.PathLike):
        super().__init__(configPath)
        self.client = self._initHomeAssistantClient()

    def printStatus(self, responseJson: dict) -> None:
        '''Print current status of the heat pump.'''
        print(f'Ilmalämpöpumpun tämän hetken asetettu ' \
                f'lämpötila {responseJson["attributes"]["temperature"]} C. ' \
                f'Huoneen lämpötila on ' \
                f'{responseJson["attributes"]["current_temperature"]} C. ')

    def plotHistory(self) -> None:
        '''Plot history of heat pump data.'''
        print('\n\n')

    def _initHomeAssistantClient(self) -> HomeAssistantClient:
        '''Initialize session to Home Assistant.'''
        url = os.getenv('HA_URL', 'default')
        token = os.getenv('HA_TOKEN', 'default')
        if url == 'default' or token == 'default':
            print('HA_URL tai HA_TOKEN ympäristömuuttujaa '\
                  'ei ole asetettu. Lämpöpumppua ei voida ohjata.')
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
            print(f'Ilmalämpöpumppuun asetettiin uusi lämpötila {newTemp} astetta.')
        except (httpx.RequestError, httpx.HTTPStatusError) as err:
            print(f'Lämpötilan asettaminen ilmalämpöpumppuun epäonnistui. '
                  f'Syy: {err}')
            return False
        return True

    def _checkValidResponse(self, response: httpx.Response) -> None:
        '''Check if the response from Home Assistant is valid.'''
        if response.status_code != 200:
            raise httpx.RequestError(f'Home Assistant vastasi koodilla {response.status_code}')
        try:
            gotResponse = response.json()
            _ = self._getCurrentTemperature(gotResponse)
        except KeyError as exc:
            raise httpx.RequestError('Ei validia JSONia') from exc

    def _getStatusResponse(self) -> httpx.Response:
        '''Get response for status query from device.'''
        response = self.client.getStatus(self.ipAddress)
        self._checkValidResponse(response)
        return response

    def _getCurrentTemperature(self, status: dict) -> float:
        '''Get current temperature from status dictionary.'''
        return status['attributes']['temperature']
