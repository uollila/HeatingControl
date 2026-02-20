#!/usr/bin/env python3
'''Module for unit test for Thermostat class.
Run with command in the main directory of the project:
python3 -m unittest discover -s devices/tests -p "testThermostat.py"
'''

import unittest
from unittest.mock import patch, MagicMock
from devices.thermostat import Thermostat # pylint: disable=import-error

class TestThermostat(unittest.TestCase):
    '''Unit tests for Thermostat class.'''

    def setUp(self):
        '''Set up a Thermostat instance for testing.'''
        self.thermostat = Thermostat(configPath="devices/tests/test_config.json")

    @patch('devices.thermostat.Thermostat.printTemps')
    def testPrintStatus(self, mockPrintTemps):
        '''Test the printStatus method of Thermostat.'''
        responseJson = {
            'parameters': {'heatingSetpoint': 22.5},
            'internalTemperature': 21.0,
            'floorTemperature': 24.0
        }

        with patch('builtins.print') as mockPrint:
            self.thermostat.printStatus(responseJson)

            mockPrintTemps.assert_called_once_with(22.5, 21.0)
            mockPrint.assert_any_call('lattia: 24.0 C')

    @patch('httpx.post')
    def testSendTempToDevice(self, mockPost):
        '''Test the sendTempToDevice method of Thermostat.'''
        mockResponse = MagicMock()
        mockPost.return_value = mockResponse

        newTemp = 23.0
        response = self.thermostat.sendTempToDevice(newTemp)

        mockPost.assert_called_once_with(
            f'http://{self.thermostat.getIpAddress()}/api/parameters?' \
            f'heatingSetpoint=23.0&operatingMode=1&sensorMode=2',
            timeout=10
        )
        self.assertEqual(response, mockResponse)

    def testPlotHistory(self):
        '''Test the plotHistory method of Thermostat.'''
        with patch('builtins.print') as mockPrint:
            self.thermostat.plotHistory()
            mockPrint.assert_called_once_with('\n\n')

if __name__ == '__main__':
    unittest.main()
