#!/usr/bin/env python3

import datetime
import time
import schedule

from thermostat import Thermostat


# MODIABLE SECTION OF THE CODE #
def adjustEteinenSettings(eteinen: Thermostat) -> None:
    eteinen.HeatingHours_Plus20 = 4 # Number of heating hours at +20C
    eteinen.HeatingHours_Plus10 = 8 # Number of heating hours at +10C
    eteinen.HeatingHours_Zero = 12    # Number of heating hours at 0C
    eteinen.HeatingHours_Minus10 = 16 	# Number of heating hours at -10C
    eteinen.HeatingHours_Minus20 = 20 	# Number of heating hours at -20C
    eteinen.HeatingHours_Minus30 = 24 	# Number of heating hours at -30C
    
    eteinen.MinimumHoursPeriod_PriceAllowed = 20
    eteinen.MinimumHoursPeriod_NumberOfHours = 3

def adjustWcSettings(wc: Thermostat) -> None:
    wc.setTemps(18, 24)

    wc.HeatingHours_Plus20 = 8 # Number of heating hours at +20C
    wc.HeatingHours_Plus10 = 12 # Number of heating hours at +10C
    wc.HeatingHours_Zero = 16    # Number of heating hours at 0C
    wc.HeatingHours_Minus10 = 20 	# Number of heating hours at -10C
    wc.HeatingHours_Minus20 = 24 	# Number of heating hours at -20C
    wc.HeatingHours_Minus30 = 24 	# Number of heating hours at -30C

    wc.PriceAlwaysAllowed = 2
# MODIABLE SECTION OF THE CODE ENDS #

def setHeating(target: Thermostat) -> None:

    #Printataan perustiedot
    name = target.getConfiguration()['name']
    timestamp = time.localtime(time.time())
    useBackup = False
    strTime = time.strftime("%H:%M:%S (%a %d %b)", timestamp)
    print(f"Kello on {strTime}. Asetetaan säädöt kohteeseen: {name}")

    #Käydään hakemassa tämän hetkinen tilanne termarilta
    status = target.getCurrentStatus()
    if (not status):
        print("Termostaattiin ei saatu yhteyttä ja säätöä ei jatketa. Yritetään tunnin päästä uudelleen.")
        return

    #Käydään hakemassa API:lta lämmityksen tarve
    heatingDemand = target.getHeatingDemand()
    if (not heatingDemand):
        print("api-spot-hinta.fi:stä ei saatu tarvittavia tietoja. Käytetään asetettuja backup-tunteja.")
        useBackup = True

    #Asetetaan lämmitys seuraavalle tunnille saatujen tietojen perusteella
    hour = timestamp.tm_hour
    successful = target.adjustTempSetpoint(status, heatingDemand, useBackup, hour)
    if not successful:
        print('Lämpötilan asettaminen termostaattiin epäonnistui.')
    else:
        target.plotHistory()    

def main():
    # Luodaan objektit jokaiselle ohjattavalle kohteelle. Annetaan nimet ja IP-osoitteet
    kph = Thermostat("configs/kph.json")
    eteinen = Thermostat("configs/eteinen.json")
    wc = Thermostat("configs/wc.json")

    #Ajastetaan säätöfunktio jokaiselle kohteelle
    schedule.every().hour.at("01:30").do(setHeating, kph)
    schedule.every().hour.at("01:40").do(setHeating, eteinen)
    schedule.every().hour.at("01:50").do(setHeating, wc)
    schedule.run_all()
    while True:
        schedule.run_pending()
        time.sleep(1)




if __name__ == '__main__':
    main()