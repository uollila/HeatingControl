#!/usr/bin/env python3
'''Module for unit tests for HomeAssistantClient class.
Run with command in the main directory of the project:
python3 -m unittest discover -s apis/tests
'''

import unittest
from unittest.mock import patch, MagicMock

from apis.homeassistant import HomeAssistantClient # pylint: disable=import-error

class TestHomeAssistantClient(unittest.TestCase):
    '''Unit tests for HomeAssistantClient class.'''

    def setUp(self):
        '''Set up a HomeAssistantClient instance for testing.'''
        self.client = HomeAssistantClient('http://ha.test:8123/', 'testtoken')

    def testInit(self):
        '''Test that trailing slash is stripped and headers are set.'''
        self.assertEqual(self.client.baseUrl, 'http://ha.test:8123')
        self.assertEqual(self.client.headers['Authorization'], 'Bearer testtoken')

    @patch('httpx.get')
    def testGetStatus(self, mockGet):
        '''Test the getStatus method.'''
        mockResponse = MagicMock()
        mockGet.return_value = mockResponse

        response = self.client.getStatus('climate.heatpump')

        mockGet.assert_called_once_with(
            'http://ha.test:8123/api/states/climate.heatpump',
            headers=self.client.headers,
            timeout=10
        )
        mockResponse.raise_for_status.assert_called_once()
        self.assertEqual(response, mockResponse)

    @patch('httpx.post')
    def testSetTemperature(self, mockPost):
        '''Test the setTemperature method.'''
        mockResponse = MagicMock()
        mockPost.return_value = mockResponse

        response = self.client.setTemperature('climate.heatpump', 21.5)

        mockPost.assert_called_once_with(
            'http://ha.test:8123/api/services/climate/set_temperature',
            headers=self.client.headers,
            json={'entity_id': 'climate.heatpump', 'temperature': 21.5},
            timeout=10
        )
        mockResponse.raise_for_status.assert_called_once()
        self.assertEqual(response, mockResponse)

    @patch('httpx.post')
    def testTurnOn(self, mockPost):
        '''Test the turnOn method.'''
        self.client.turnOn('climate.heatpump')

        mockPost.assert_called_once_with(
            'http://ha.test:8123/api/services/climate/turn_on',
            headers=self.client.headers,
            json={'entity_id': 'climate.heatpump'},
            timeout=10
        )

    @patch('httpx.post')
    def testTurnOff(self, mockPost):
        '''Test the turnOff method.'''
        self.client.turnOff('climate.heatpump')

        mockPost.assert_called_once_with(
            'http://ha.test:8123/api/services/climate/turn_off',
            headers=self.client.headers,
            json={'entity_id': 'climate.heatpump'},
            timeout=10
        )

if __name__ == '__main__':
    unittest.main()
