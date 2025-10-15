#!/usr/bin/env python3
'''Module for Panel class.'''

from classes.device import Device

class Panel(Device):
    '''Class for panel device.'''

    def printStatus(self, responseJson: dict) -> None:
        '''Print current status of the panel.'''
        print(f'Patterin tämän hetken asetettu lämpötila ' \
              f'{responseJson['parameters']['heatingSetpoint']} C')
        print(f'Status: {responseJson['state']}, Huoneen lämpötila: ' \
              f'{responseJson['roomTemperature']} C')

    def plotHistory(self):
        '''Plot history of panel data.'''
        print('\n\n')
