#!/usr/bin/env python3
'''Module for Thermostat class.'''

from classes.device import Device

class Thermostat(Device):
    '''Thermostat class inherits from Device class.'''

    def printStatus(self, responseJson: dict) -> None:
        '''Print current status of the thermostat.'''
        print(f'Termostaatin tämän hetken asetettu ' \
              f'lämpötila {responseJson['parameters']['heatingSetpoint']} C')
        print(f'Status: {responseJson['state']}, huoneen lämpötila:' \
              f'{responseJson['internalTemperature']} C, ' \
              f'lattian lämpötila: {responseJson['floorTemperature']} C')

    def plotHistory(self) -> None:
        '''Plot history of thermostat data.'''
        print('\n\n')
