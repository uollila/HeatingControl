#!/usr/bin/env python3
'''Module for Panasonic device class. Can control Panasonic heat pumps
that are connected to the Comfort Cloud app.'''

import os
from urllib.error import HTTPError

from apis.homeassistant import HomeAssistantClient  # pylint: disable=import-error
from devices.device import Device  # pylint: disable=import-error

class Panasonic(Device):
    '''Class for Panasonic heat pump device.'''

    def printStatus(self, responseJson: dict) -> None:
        '''Print current status of the Panasonic heat pump.'''
        print(f'Panasonic lämpöpumpun tämän hetken asetettu ' \
              f'lämpötila {responseJson['attributes']['temperature']} C. ' \
              f'Huoneen lämpötila on ' \
              f'{responseJson['attributes']['current_temperature']} C. ')

    def plotHistory(self) -> None:
        '''Plot history of panel data.'''
        print('\n\n')

    def initHomeAssistantClient(self) -> HomeAssistantClient:
        '''Initialize session to Home Assistant.'''
        url = os.getenv('HA_URL', 'default')
        token = os.getenv('HA_TOKEN', 'default')
        if url == 'default' or token == 'default':
            print('HA_URL tai HA_TOKEN ympäristömuuttujaa '\
                  'ei ole asetettu. Panasonic laitetta ei voida ohjata.')
            return None
        client = HomeAssistantClient(url, token)
        return client

    def setTemp(self, newTemp: float, oldTemp: float) -> bool:
        '''Set new temperature to device.'''
        if newTemp == oldTemp:
            print(f'Ei tarvetta muuttaa lämpötilaa! Vanha ja uusi on samat {oldTemp} astetta.')
            return True
        try:
            client = self.initHomeAssistantClient()
            if not client:
                print('Home Assistant clientia ei saatu alustettua.')
                return False
            client.setTemperature(self.ipAddress, newTemp)
            print(f'Panasonic lämpöpumppuun asetettiin uusi lämpötila {newTemp} astetta.')
        except HTTPError as err:
            print(f'Lämpötilan asettaminen Panasonic lämpöpumppuun epäonnistui. '
                  f'Syy: {err}')
            return False
        return True

    def getCurrentStatus(self) -> dict:
        '''Get current status from device.'''
        client = self.initHomeAssistantClient()
        if not client:
            print('Home Assistant clientia ei saatu alustettua.')
            return None
        state = client.getState(self.ipAddress)
        if not state:
            print('Laitteeseen ei saatu yhteyttä Home Assistantin kautta.')
            return None
        self.printStatus(state)
        return state

    def adjustTempSetpoint(self, status: dict, heating: bool) -> None:
        '''Adjust temperature setpoint based on current status and heating demand.'''
        temps = self.getTemps()
        currentTemp = status['attributes']['temperature']
        if heating: #heating on
            return self.setTemp(temps.high, currentTemp)
        return self.setTemp(temps.low, currentTemp)
