#!/usr/bin/env python3
'''Module for Home Assistant client.'''
import requests

class HomeAssistantClient:
    '''Client for Home Assistant REST API.'''
    def __init__(self, baseUrl: str, token: str):
        self.baseUrl = baseUrl.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def getState(self, entityId: str):
        '''Get state of an entity from Home Assistant.'''
        url = f"{self.baseUrl}/api/states/{entityId}"
        r = requests.get(url, headers=self.headers, timeout=10)
        r.raise_for_status()
        return r.json()

    def setTemperature(self, entityId: str, temperature: float):
        '''Set temperature of a climate entity in Home Assistant.'''
        url = f"{self.baseUrl}/api/services/climate/set_temperature"
        payload = {
            "entity_id": entityId,
            "temperature": temperature
        }
        r = requests.post(url, headers=self.headers, json=payload, timeout=10)
        r.raise_for_status()

    def turnOn(self, entityId: str):
        '''Turn on a climate entity in Home Assistant.'''
        url = f"{self.baseUrl}/api/services/climate/turn_on"
        r = requests.post(
            url,
            headers=self.headers,
            json={"entity_id": entityId},
            timeout=10
        )
        r.raise_for_status()

    def turnOff(self, entityId: str):
        '''Turn off a climate entity in Home Assistant.'''
        url = f"{self.baseUrl}/api/services/climate/turn_off"
        r = requests.post(
            url,
            headers=self.headers,
            json={"entity_id": entityId},
            timeout=10
        )
        r.raise_for_status()
