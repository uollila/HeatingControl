#!/usr/bin/env python3
'''Module for unit tests for optimize module.
Run with command in the main directory of the project:
python3 -m unittest discover -s tests
'''

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from optimize import getDeviceType, createObject, setHeating # pylint: disable=import-error
from devices.device import Device # pylint: disable=import-error
from devices.panel import Panel # pylint: disable=import-error
from devices.thermostat import Thermostat # pylint: disable=import-error
from devices.heatpump import HeatPump # pylint: disable=import-error

class TestOptimize(unittest.TestCase):
    '''Unit tests for optimize module.'''

    def setUp(self):
        '''Set up a temporary directory for test configuration files.'''
        self.tempDir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tempDir, True)

    def _writeConfig(self, deviceType: str) -> str:
        '''Write a minimal configuration file and return its path.'''
        configPath = os.path.join(self.tempDir, f'{deviceType}.json')
        with open(configPath, 'w', encoding='utf-8') as configFile:
            json.dump([{'type': deviceType}], configFile)
        return configPath

    def testGetDeviceType(self):
        '''Test that device type is read from configuration file.'''
        deviceType = getDeviceType('devices/tests/test_config.json')
        self.assertEqual(deviceType, 'thermostat')

    def testCreateObjectThermostat(self):
        '''Test that thermostat object is created for thermostat type.'''
        device = createObject('devices/tests/test_config.json')
        self.assertIsInstance(device, Thermostat)

    def testCreateObjectPanel(self):
        '''Test that panel object is created for panel type.'''
        device = createObject(self._writeConfig('panel'))
        self.assertIsInstance(device, Panel)

    def testCreateObjectHeatpump(self):
        '''Test that heatpump object is created for heatpump type.'''
        with patch('builtins.print'):
            device = createObject(self._writeConfig('heatpump'))
        self.assertIsInstance(device, HeatPump)

    def testCreateObjectUnknownType(self):
        '''Test that None is returned for unknown device type.'''
        with patch('builtins.print'):
            device = createObject(self._writeConfig('unknown'))
        self.assertIsNone(device)

    @patch('builtins.print')
    def testSetHeatingNoConnection(self, mockPrint):
        '''Test that heating is not adjusted when device is unreachable.'''
        target = MagicMock(spec=Device)
        target.getName.return_value = 'testdevice'
        target.getCurrentStatus.return_value = None

        setHeating(target)

        target.adjustTempSetpoint.assert_not_called()
        mockPrint.assert_any_call('Laitteeseen ei saatu yhteyttä ja säätöä ei jatketa. ' \
                                  'Yritetään tunnin päästä uudelleen.')

    @patch('builtins.print')
    def testSetHeatingDisabledDevice(self, mockPrint):
        '''Test that disabled devices are not queried or adjusted.'''
        target = MagicMock(spec=Device)
        target.getName.return_value = 'testdevice'
        target.isEnabled.return_value = False

        setHeating(target)

        target.getCurrentStatus.assert_not_called()
        target.getHeatingDemand.assert_not_called()
        target.adjustTempSetpoint.assert_not_called()
        target.plotHistory.assert_not_called()
        mockPrint.assert_any_call('Kohteen testdevice säätö ei ole aktiivinen, säätöä ei tehdä.\n')

    @patch('builtins.print')
    def testSetHeatingAdjustsDevice(self, mockPrint):
        '''Test that heating is adjusted based on status and heating demand.'''
        target = MagicMock(spec=Device)
        target.getName.return_value = 'testdevice'
        status = {'parameters': {'heatingSetpoint': 18.0}}
        target.getCurrentStatus.return_value = status
        target.getHeatingDemand.return_value = True
        target.adjustTempSetpoint.return_value = True

        setHeating(target)

        target.adjustTempSetpoint.assert_called_once_with(status, True)
        target.plotHistory.assert_called_once()
        self.assertTrue(mockPrint.called)

    @patch('builtins.print')
    def testSetHeatingAdjustmentFails(self, mockPrint):
        '''Test that failed adjustment is reported and history is not plotted.'''
        target = MagicMock(spec=Device)
        target.getName.return_value = 'testdevice'
        target.getCurrentStatus.return_value = {'parameters': {}}
        target.getHeatingDemand.return_value = False
        target.adjustTempSetpoint.return_value = False

        setHeating(target)

        target.plotHistory.assert_not_called()
        mockPrint.assert_any_call('Lämpötilan asettaminen laitteeseen epäonnistui.')

if __name__ == '__main__':
    unittest.main()
