#!/usr/bin/env python3
'''Web editor for device configuration files.'''

import json
import os
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, urlparse


EDITOR_HTML = '''<!doctype html>
<html lang="fi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HeatingControl asetukset</title>
  <style>
    body { font-family: sans-serif; margin: 1rem auto; max-width: 1000px; padding: 0 1rem; }
    textarea { box-sizing: border-box; font: 14px monospace; min-height: 70vh; width: 100%; }
    button, select { font-size: 1rem; margin: .4rem .4rem .8rem 0; padding: .4rem; }
    #message { min-height: 1.5em; }
  </style>
</head>
<body>
  <h1>HeatingControl asetukset</h1>
  <label for="file">Tiedosto:</label>
  <select id="file"></select>
  <button id="load">Lataa</button>
  <button id="save">Tallenna</button>
  <p id="message" role="status"></p>
  <textarea id="content" spellcheck="false"></textarea>
  <script>
    const file = document.getElementById('file');
    const content = document.getElementById('content');
    const message = document.getElementById('message');
    async function request(url, options) {
      const response = await fetch(url, options);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Pyyntö epäonnistui');
      return data;
    }
    async function loadFiles() {
      const data = await request('/api/configs');
      file.replaceChildren(...data.files.map(name => new Option(name, name)));
      if (file.value) await loadFile();
    }
    async function loadFile() {
      if (!file.value) return;
      const data = await request('/api/config?file=' + encodeURIComponent(file.value));
      content.value = data.content;
      message.textContent = 'Tiedosto ladattu.';
    }
    async function saveFile() {
      if (!file.value) return;
      const data = await request('/api/config?file=' + encodeURIComponent(file.value), {
        method: 'PUT', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({content: content.value})
      });
      content.value = data.content;
      message.textContent = 'Tiedosto tallennettu.';
    }
    file.addEventListener('change', loadFile);
    document.getElementById('load').addEventListener('click', () => loadFile().catch(showError));
    document.getElementById('save').addEventListener('click', () => saveFile().catch(showError));
    function showError(error) { message.textContent = 'Virhe: ' + error.message; }
    loadFiles().catch(showError);
  </script>
</body>
</html>'''


class ConfigStore:
    '''Read and safely write JSON configuration files.'''

    def __init__(self, config_dir: str | Path = 'configs') -> None:
        self.config_dir = Path(config_dir).resolve()

    def _getPath(self, filename: str) -> Path:
        '''Return a configuration path and reject path traversal.'''
        path = (self.config_dir / filename).resolve()
        if path.parent != self.config_dir and self.config_dir not in path.parents:
            raise ValueError('Virheellinen tiedostopolku.')
        if path.suffix != '.json':
            raise ValueError('Vain JSON-tiedostoja voi muokata.')
        return path

    def listFiles(self) -> list[str]:
        '''List JSON files relative to the configuration directory.'''
        if not self.config_dir.is_dir():
            return []
        return sorted(path.relative_to(self.config_dir).as_posix()
                      for path in self.config_dir.rglob('*.json')
                      if path.is_file())

    def read(self, filename: str) -> str:
        '''Read a configuration file as formatted JSON.'''
        path = self._getPath(filename)
        if not path.is_file():
            raise FileNotFoundError(filename)
        with path.open('r', encoding='utf-8') as config_file:
            data = json.load(config_file)
        return json.dumps(data, indent=2, ensure_ascii=False) + '\n'

    def write(self, filename: str, content: str) -> str:
        '''Validate and atomically write a configuration file.'''
        path = self._getPath(filename)
        data = json.loads(content)
        if not isinstance(data, list) or len(data) != 2:
            raise ValueError('Konfiguraation pitää olla kahden alkion JSON-taulukko.')
        path.parent.mkdir(parents=True, exist_ok=True)
        formatted = json.dumps(data, indent=2, ensure_ascii=False) + '\n'
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile('w', encoding='utf-8',
                                             dir=path.parent, delete=False) as temp_file:
                temp_file.write(formatted)
                temporary_path = Path(temp_file.name)
            os.replace(temporary_path, path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()
        return formatted


class ConfigRequestHandler(BaseHTTPRequestHandler):
    '''HTTP request handler for the configuration editor.'''

    store: ConfigStore

    def log_message(self, format_string: str, *args) -> None:  # pylint: disable=arguments-differ
        '''Keep the standard HTTP log output in Finnish.'''
        print(f'Web-muokkain: {format_string % args}')

    def _sendJson(self, status: HTTPStatus, data: dict) -> None:
        '''Send a JSON response.'''
        payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _error(self, status: HTTPStatus, message: str) -> None:
        '''Send a JSON error response.'''
        self._sendJson(status, {'error': message})

    def do_GET(self) -> None:  # pylint: disable=invalid-name
        '''Handle the editor page and read-only API endpoints.'''
        parsed = urlparse(self.path)
        try:
            if parsed.path == '/':
                payload = EDITOR_HTML.encode('utf-8')
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            elif parsed.path == '/api/configs':
                self._sendJson(HTTPStatus.OK, {'files': self.store.listFiles()})
            elif parsed.path == '/api/config':
                filename = parse_qs(parsed.query).get('file', [None])[0]
                if filename is None:
                    self._error(HTTPStatus.BAD_REQUEST, 'Tiedostonimi puuttuu.')
                else:
                    self._sendJson(HTTPStatus.OK, {'content': self.store.read(filename)})
            else:
                self._error(HTTPStatus.NOT_FOUND, 'Sivua ei löytynyt.')
        except json.JSONDecodeError as error:
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR,
                        f'Tiedoston lukeminen epäonnistui: {error}')
        except ValueError as error:
            self._error(HTTPStatus.BAD_REQUEST, str(error))
        except FileNotFoundError:
            self._error(HTTPStatus.NOT_FOUND, 'Tiedostoa ei löytynyt.')
        except OSError as error:
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR,
                        f'Tiedoston lukeminen epäonnistui: {error}')

    def do_PUT(self) -> None:  # pylint: disable=invalid-name
        '''Validate and save a configuration file.'''
        parsed = urlparse(self.path)
        if parsed.path != '/api/config':
            self._error(HTTPStatus.NOT_FOUND, 'Sivua ei löytynyt.')
            return
        filename = parse_qs(parsed.query).get('file', [None])[0]
        if filename is None:
            self._error(HTTPStatus.BAD_REQUEST, 'Tiedostonimi puuttuu.')
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            body = json.loads(self.rfile.read(length).decode('utf-8'))
            if not isinstance(body, dict) or not isinstance(body.get('content'), str):
                raise ValueError('Pyynnön sisältö puuttuu.')
            content = self.store.write(filename, body['content'])
            self._sendJson(HTTPStatus.OK, {'content': content})
        except json.JSONDecodeError as error:
            self._error(HTTPStatus.BAD_REQUEST, str(error))
        except ValueError as error:
            self._error(HTTPStatus.BAD_REQUEST, str(error))
        except OSError as error:
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR,
                        f'Tiedoston tallennus epäonnistui: {error}')


def startConfigServer(host: str | None = None, port: int | None = None,
                      config_dir: str | Path = 'configs') -> tuple[ThreadingHTTPServer, Thread]:
    '''Start the configuration editor in a daemon thread.'''
    listen_host = host or os.getenv('CONFIG_WEB_HOST', '0.0.0.0')
    listen_port = port if port is not None else int(os.getenv('CONFIG_WEB_PORT', '8124'))
    store = ConfigStore(config_dir)
    handler = type('ConfiguredConfigRequestHandler', (ConfigRequestHandler,),
                   {'store': store})
    server = ThreadingHTTPServer((listen_host, listen_port), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f'Web-muokkain käynnistetty osoitteessa http://{listen_host}:{server.server_port}')
    return server, thread
