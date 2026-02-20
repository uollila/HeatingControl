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
        try:
            currentTemp = responseJson["attributes"]["current_temperature"]
            setTemp = responseJson["attributes"]["temperature"]
            self.printTemps(setTemp, currentTemp)
        except KeyError:
            print("Error: Could not retrieve status information from response.")

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

    def sendTempToDevice(self, newTemp: float) -> httpx.Response:
        '''Send new temperature to heat pump.'''
        return self.client.setTemperature(self.ipAddress, newTemp)

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
