#!/usr/bin/env python3
'''Module for unit test for Panel class.
Run with command in the main directory of the project:
python3 -m unittest discover -s devices/tests
'''

import unittest
from unittest.mock import patch, MagicMock
from devices.panel import Panel # pylint: disable=import-error

class TestPanel(unittest.TestCase):
    '''Unit tests for Panel class.'''

    def setUp(self):
        '''Set up a Panel instance for testing.'''
        self.panel = Panel(configPath="devices/tests/test_config.json")

    @patch('devices.panel.Panel.printTemps')
    def testPrintStatus(self, mockPrintTemps):
        '''Test the printStatus method of Panel.'''
        responseJson = {
            'parameters': {'heatingSetpoint': 22.5},
            'roomTemperature': 21.0
        }

        self.panel.printStatus(responseJson)
        mockPrintTemps.assert_called_once_with(22.5, 21.0)

    @patch('builtins.print')
    def testPrintStatusInvalidResponse(self, mockPrint):
        '''Test the printStatus method of Panel with invalid response.'''
        self.panel.printStatus({})
        mockPrint.assert_called_once_with('Ei saatu kunnon vastausta patterilta.')

    @patch('httpx.post')
    def testSendTempToDevice(self, mockPost):
        '''Test the sendTempToDevice method of Panel.'''
        mockResponse = MagicMock()
        mockPost.return_value = mockResponse

        newTemp = 23.0
        response = self.panel.sendTempToDevice(newTemp)

        # sensorMode luetaan konfiguraatiotiedostosta, kun IP-osoite haetaan
        mockPost.assert_called_once_with(
            f'http://{self.panel.getIpAddress()}/api/parameters?' \
            f'heatingSetpoint=23.0&panelMode=1&sensorMode=2',
            timeout=10
        )
        self.assertEqual(response, mockResponse)

    def testPlotHistory(self):
        '''Test the plotHistory method of Panel.'''
        with patch('builtins.print') as mockPrint:
            self.panel.plotHistory()
            mockPrint.assert_called_once_with('\n')

if __name__ == '__main__':
    unittest.main()
