#!/usr/bin/env python3
'''Unit tests for the configuration web editor.'''

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from urllib.request import Request, urlopen

from configweb import ConfigStore, startConfigServer  # pylint: disable=import-error


class TestConfigStore(unittest.TestCase):
    '''Unit tests for ConfigStore.'''

    def setUp(self):
        '''Create an isolated temporary configuration directory.'''
        self.tempDir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tempDir, True)
        self.configDir = Path(self.tempDir)
        self.configPath = self.configDir / 'device.json'
        self.configPath.write_text('[{"type": "thermostat"}, {"BackupHours": [1]}]',
                                   encoding='utf-8')
        self.store = ConfigStore(self.configDir)

    def testListAndRead(self):
        '''Test listing and formatted reading of JSON files.'''
        self.assertEqual(self.store.listFiles(), ['device.json'])
        self.assertEqual(json.loads(self.store.read('device.json'))[0]['type'], 'thermostat')

    def testWriteFormatsValidJson(self):
        '''Test that valid configuration is written atomically and formatted.'''
        content = '[{"type":"panel"},{"BackupHours":[]}]'
        result = self.store.write('device.json', content)
        self.assertEqual(json.loads(result)[0]['type'], 'panel')
        saved = json.loads(self.configPath.read_text(encoding='utf-8'))
        self.assertEqual(saved[0]['type'], 'panel')

    def testWriteRejectsInvalidConfiguration(self):
        '''Test that malformed and structurally invalid JSON is rejected.'''
        with self.assertRaises(json.JSONDecodeError):
            self.store.write('device.json', '{')
        with self.assertRaises(ValueError):
            self.store.write('device.json', '{}')

    def testRejectsPathTraversal(self):
        '''Test that paths outside configs cannot be accessed.'''
        with self.assertRaises(ValueError):
            self.store.read('../secret.json')


class TestConfigWebServer(unittest.TestCase):
    '''Unit tests for the HTTP interface.'''

    def setUp(self):
        '''Start an isolated local web server.'''
        self.tempDir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tempDir, True)
        configDir = Path(self.tempDir)
        (configDir / 'device.json').write_text('[{}, {}]', encoding='utf-8')
        self.server, _ = startConfigServer('127.0.0.1', 0, configDir)
        self.addCleanup(self._stopServer)
        self.baseUrl = f'http://127.0.0.1:{self.server.server_port}'

    def _stopServer(self):
        '''Stop and close the test web server.'''
        self.server.shutdown()
        self.server.server_close()

    def testListAndReadEndpoints(self):
        '''Test listing and reading configurations over HTTP.'''
        with urlopen(f'{self.baseUrl}/api/configs') as response:
            self.assertEqual(json.loads(response.read())['files'], ['device.json'])
        with urlopen(f'{self.baseUrl}/api/config?file=device.json') as response:
            self.assertEqual(json.loads(response.read())['content'], '[\n  {},\n  {}\n]\n')

    def testPutEndpoint(self):
        '''Test saving a configuration over HTTP.'''
        body = json.dumps({'content': '[{"type": "panel"}, {}]'}).encode('utf-8')
        request = Request(f'{self.baseUrl}/api/config?file=device.json', data=body,
                          headers={'Content-Type': 'application/json'}, method='PUT')
        with urlopen(request) as response:
            self.assertEqual(json.loads(response.read())['content'],
                             '[\n  {\n    "type": "panel"\n  },\n  {}\n]\n')


if __name__ == '__main__':
    unittest.main()
