#!/usr/bin/env python3
'''Module for unit tests for Device base class.
Run with command in the main directory of the project:
python3 -m unittest discover -s devices/tests
'''

import time
import unittest
from unittest.mock import patch, MagicMock

import httpx

from devices.device import Device # pylint: disable=import-error

class TestDevice(unittest.TestCase):
    '''Unit tests for Device class.'''

    def setUp(self):
        '''Set up a Device instance for testing.'''
        self.device = Device(configPath="devices/tests/test_config.json")

    def testGetName(self):
        '''Test that name is read from configuration.'''
        self.assertEqual(self.device.getName(), 'default')

    def testGetIpAddress(self):
        '''Test that ip address is read from configuration.'''
        self.assertEqual(self.device.getIpAddress(), '0.0.0.0')

    def testIsEnabledDefaultsToTrue(self):
        '''Test that configurations without enabled remain active.'''
        self.assertTrue(self.device.isEnabled())

    def testIsEnabledReadsFalse(self):
        '''Test that disabled configuration is recognized.'''
        with patch.object(Device, '_getConfiguration', return_value={'enabled': False}):
            self.assertFalse(self.device.isEnabled())

    @patch('builtins.print')
    @patch.object(Device, 'sendTempToDevice')
    def testAdjustTempSetpointHeatingOn(self, mockSend, mockPrint):
        '''Test that high setpoint is used when heating is demanded.'''
        mockSend.return_value = MagicMock(status_code=200)

        status = {'parameters': {'heatingSetpoint': 18.0}}
        result = self.device.adjustTempSetpoint(status, True)

        self.assertTrue(result)
        mockSend.assert_called_once_with(22.0)
        mockPrint.assert_any_call('Laitteeseen asetettiin uusi lämpötila 22.0 astetta.')

    @patch('builtins.print')
    @patch.object(Device, 'sendTempToDevice')
    def testAdjustTempSetpointHeatingOff(self, mockSend, mockPrint):
        '''Test that low setpoint is used when heating is not demanded.'''
        mockSend.return_value = MagicMock(status_code=200)

        status = {'parameters': {'heatingSetpoint': 22.0}}
        result = self.device.adjustTempSetpoint(status, False)

        self.assertTrue(result)
        mockSend.assert_called_once_with(18.0)
        mockPrint.assert_any_call('Laitteeseen asetettiin uusi lämpötila 18.0 astetta.')

    @patch('builtins.print')
    @patch.object(Device, 'sendTempToDevice')
    def testAdjustTempSetpointNoChange(self, mockSend, mockPrint):
        '''Test that nothing is sent when setpoint is already correct.'''
        status = {'parameters': {'heatingSetpoint': 18.0}}
        result = self.device.adjustTempSetpoint(status, False)

        self.assertTrue(result)
        mockSend.assert_not_called()
        mockPrint.assert_any_call('Ei tarvetta muuttaa lämpötilaa! Vanha ja uusi on samat ' \
                                  '18.0 astetta.')

    def testGetHeatingDemandFromFuturePlan(self):
        '''Test heating demand lookup from a valid future plan.'''
        nowMillis = int(time.time() * 1000)
        self.device.futurePlan = [
            {'epochMs': nowMillis - 60000, 'result': True},
            {'epochMs': nowMillis + 3600000, 'result': False}
        ]
        self.device.planExpiration = nowMillis + 7200000

        with patch('builtins.print'):
            self.assertTrue(self.device.getHeatingDemand())

        self.device.futurePlan = [
            {'epochMs': nowMillis - 60000, 'result': False}
        ]
        with patch('builtins.print'):
            self.assertFalse(self.device.getHeatingDemand())

    @patch('devices.device.time.sleep')
    @patch('httpx.post')
    def testGetHeatingDemandFetchesNewPlan(self, mockPost, mockSleep):
        '''Test that a new plan is fetched from api.spot-hinta.fi when expired.'''
        nowMillis = int(time.time() * 1000)
        plan = [{'epochMs': nowMillis - 60000, 'result': True}]
        mockResponse = MagicMock()
        mockResponse.status_code = 200
        mockResponse.json.return_value = {
            'PlanAhead': plan,
            'EpochMsExpiration': nowMillis + 7200000,
            'AverageTemperature': 5
        }
        mockPost.return_value = mockResponse

        with patch('builtins.print'):
            self.assertTrue(self.device.getHeatingDemand())

        mockPost.assert_called_once()
        self.assertEqual(self.device.futurePlan, plan)
        mockSleep.assert_not_called()

    @patch('devices.device.time.sleep')
    @patch('httpx.post')
    def testGetHeatingDemandBackupHoursOn(self, mockPost, mockSleep):
        '''Test that backup hours heat when the api.spot-hinta.fi is unreachable.'''
        mockPost.side_effect = httpx.RequestError('mock error')
        currentHour = time.localtime().tm_hour

        with patch.object(Device, '_getApiConfiguration',
                          return_value={'BackupHours': [currentHour]}):
            with patch('builtins.print'):
                self.assertTrue(self.device.getHeatingDemand())

        self.assertEqual(mockSleep.call_count, 3)

    @patch('devices.device.time.sleep')
    @patch('httpx.post')
    def testGetHeatingDemandBackupHoursOff(self, mockPost, mockSleep):
        '''Test that backup hours do not heat outside the configured hours.'''
        mockPost.side_effect = httpx.RequestError('mock error')
        currentHour = time.localtime().tm_hour

        with patch.object(Device, '_getApiConfiguration',
                          return_value={'BackupHours': [(currentHour + 12) % 24]}):
            with patch('builtins.print'):
                self.assertFalse(self.device.getHeatingDemand())

        self.assertEqual(mockSleep.call_count, 3)

    @patch('httpx.get')
    def testGetCurrentStatus(self, mockGet):
        '''Test that current status is returned from device.'''
        statusJson = {'parameters': {'heatingSetpoint': 20.0}}
        mockResponse = MagicMock()
        mockResponse.status_code = 200
        mockResponse.json.return_value = statusJson
        mockGet.return_value = mockResponse

        with patch.object(self.device, 'printStatus'):
            status = self.device.getCurrentStatus()

        self.assertEqual(status, statusJson)

    @patch('devices.device.time.sleep')
    @patch('httpx.get')
    def testGetCurrentStatusNoConnection(self, mockGet, mockSleep):
        '''Test that None is returned when device cannot be reached.'''
        mockGet.side_effect = httpx.RequestError('mock error')

        with patch('builtins.print'):
            status = self.device.getCurrentStatus()

        self.assertIsNone(status)
        self.assertEqual(mockGet.call_count, 5)
        self.assertEqual(mockSleep.call_count, 5)

    def testNotImplementedMethods(self):
        '''Test that abstract methods raise NotImplementedError.'''
        with self.assertRaises(NotImplementedError):
            self.device.plotHistory()
        with self.assertRaises(NotImplementedError):
            self.device.printStatus({})
        with self.assertRaises(NotImplementedError):
            self.device.sendTempToDevice(20.0)

if __name__ == '__main__':
    unittest.main()
