#!/usr/bin/env python3
'''Module for unit tests for HeatPump class.
Run with command in the main directory of the project:
python3 -m unittest discover -s devices/tests
'''

import os
import unittest
from unittest.mock import patch, MagicMock

from devices.heatpump import HeatPump # pylint: disable=import-error
from apis.homeassistant import HomeAssistantClient # pylint: disable=import-error

class TestHeatPump(unittest.TestCase):
    '''Unit tests for HeatPump class.'''

    def setUp(self):
        '''Set up a HeatPump instance for testing with mocked environment.'''
        self.envPatch = patch.dict(os.environ,
                                   {'HA_URL': 'http://ha.test:8123',
                                    'HA_TOKEN': 'testtoken'},
                                   clear=True)
        self.envPatch.start()
        self.addCleanup(self.envPatch.stop)
        self.heatpump = HeatPump(configPath="devices/tests/test_config.json")
        self.heatpump.ipAddress = 'climate.heatpump'

    def testInitCreatesClient(self):
        '''Test that Home Assistant client is created when env vars are set.'''
        self.assertIsInstance(self.heatpump.client, HomeAssistantClient)
        self.assertEqual(self.heatpump.client.baseUrl, 'http://ha.test:8123')

    def testInitWithoutEnvVars(self):
        '''Test that client is not created when env vars are missing.'''
        with patch.dict(os.environ, {}, clear=True):
            with patch('builtins.print'):
                heatpump = HeatPump(configPath="devices/tests/test_config.json")
        self.assertIsNone(heatpump.client)

    def testSendTempToDevice(self):
        '''Test the sendTempToDevice method of HeatPump.'''
        self.heatpump.client = MagicMock()

        response = self.heatpump.sendTempToDevice(21.5)

        self.heatpump.client.setTemperature.assert_called_once_with(
            'climate.heatpump', 21.5)
        self.assertEqual(response, self.heatpump.client.setTemperature.return_value)

    @patch('devices.heatpump.HeatPump.printTemps')
    def testPrintStatus(self, mockPrintTemps):
        '''Test the printStatus method of HeatPump.'''
        responseJson = {
            'attributes': {'current_temperature': 20.0, 'temperature': 21.0}
        }

        self.heatpump.printStatus(responseJson)
        mockPrintTemps.assert_called_once_with(21.0, 20.0)

    @patch('builtins.print')
    def testPrintStatusInvalidResponse(self, mockPrint):
        '''Test the printStatus method of HeatPump with invalid response.'''
        self.heatpump.printStatus({'attributes': {}})
        mockPrint.assert_called_once_with(
            'Error: Could not retrieve status information from response.')

    def testGetCurrentStatus(self):
        '''Test that status is fetched through Home Assistant client.'''
        statusJson = {'attributes': {'current_temperature': 20.0,
                                     'temperature': 21.0}}
        mockResponse = MagicMock()
        mockResponse.status_code = 200
        mockResponse.json.return_value = statusJson
        self.heatpump.client = MagicMock()
        self.heatpump.client.getStatus.return_value = mockResponse

        with patch.object(self.heatpump, 'printStatus'):
            status = self.heatpump.getCurrentStatus()

        self.heatpump.client.getStatus.assert_called_once_with('climate.heatpump')
        self.assertEqual(status, statusJson)

    @patch('devices.device.time.sleep')
    def testGetCurrentStatusNon200(self, mockSleep):
        '''Test that connection is retried when Home Assistant responds with error.'''
        mockResponse = MagicMock()
        mockResponse.status_code = 500
        self.heatpump.client = MagicMock()
        self.heatpump.client.getStatus.return_value = mockResponse

        with patch('builtins.print'):
            status = self.heatpump.getCurrentStatus()

        self.assertIsNone(status)
        self.assertEqual(self.heatpump.client.getStatus.call_count, 5)
        self.assertEqual(mockSleep.call_count, 5)

    @patch('devices.device.time.sleep')
    def testGetCurrentStatusInvalidJson(self, mockSleep):
        '''Test that connection is retried when Home Assistant response is invalid.'''
        mockResponse = MagicMock()
        mockResponse.status_code = 200
        mockResponse.json.return_value = {}
        self.heatpump.client = MagicMock()
        self.heatpump.client.getStatus.return_value = mockResponse

        with patch('builtins.print'):
            status = self.heatpump.getCurrentStatus()

        self.assertIsNone(status)
        self.assertEqual(self.heatpump.client.getStatus.call_count, 5)
        self.assertEqual(mockSleep.call_count, 5)

    def testPlotHistory(self):
        '''Test the plotHistory method of HeatPump.'''
        with patch('builtins.print') as mockPrint:
            self.heatpump.plotHistory()
            mockPrint.assert_called_once_with('\n')

if __name__ == '__main__':
    unittest.main()
