#!/usr/bin/env python3

import httpx
import time

from device import Device

# This provides the base class for the configuration that is used in API-call to
# https://api.spot-hinta.fi/
class Panel(Device):

    def getCurrentStatus(self) -> dict:
        url = "http://" + self.getIpAddress() + "/api/status"
        attempts = 5
        responseJson = None
        for attempt in range(attempts):
            try:
                response = httpx.get(url)
                if response.status_code == 200:
                    responseJson = response.json()
                    print(f'''Patterin tämän hetken asetettu lämpötila {responseJson['parameters']['heatingSetpoint']} C''')
                    print(f'Status: {responseJson['state']}, Huoneen lämpötila: {responseJson['roomTemperature']} C')
                else:
                    print(f'Patteri vastasi koodilla {response.status_code}')
            except httpx.RequestError as exc:
                print(f"Patteriin ei saatu yhteyttä. Yritetään 5 sekunnin päästä uudelleen.")
                time.sleep(5)
            else:
                return responseJson
        return responseJson
    
    def plotHistory(self):
        print("\n\n")
        return