#!/usr/bin/env python3
'''Module for Home Assistant client.'''
import httpx

class HomeAssistantClient:
    '''Client for Home Assistant REST API.'''
    def __init__(self, baseUrl: str, token: str) -> None:
        self.baseUrl = baseUrl.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def getStatus(self, entityId: str) -> httpx.Response:
        '''Get state of an entity from Home Assistant.'''
        url = f"{self.baseUrl}/api/states/{entityId}"
        response = httpx.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        return response

    def setTemperature(self, entityId: str, temperature: float) -> None:
        '''Set temperature of a climate entity in Home Assistant.'''
        url = f"{self.baseUrl}/api/services/climate/set_temperature"
        payload = {
            "entity_id": entityId,
            "temperature": temperature
        }
        r = httpx.post(url, headers=self.headers, json=payload, timeout=10)
        r.raise_for_status()

    def turnOn(self, entityId: str) -> None:
        '''Turn on a climate entity in Home Assistant.'''
        url = f"{self.baseUrl}/api/services/climate/turn_on"
        r = httpx.post(
            url,
            headers=self.headers,
            json={"entity_id": entityId},
            timeout=10
        )
        r.raise_for_status()

    def turnOff(self, entityId: str) -> None:
        '''Turn off a climate entity in Home Assistant.'''
        url = f"{self.baseUrl}/api/services/climate/turn_off"
        r = httpx.post(
            url,
            headers=self.headers,
            json={"entity_id": entityId},
            timeout=10
        )
        r.raise_for_status()
