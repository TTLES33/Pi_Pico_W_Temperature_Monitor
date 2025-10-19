import gc
import machine
import network
import socket
import time
import urequests
import json
import ds18x20
import onewire


config = json.load(open("config.json"))


def wifi_connect():
    print(len(config["wifi"]))
    for i in config["wifi"]:  # Zkusit připojení k sítím
        ssid = i["ssid"]
        password = i["password"]

        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(ssid, password)

        while wlan.isconnected() == False:
            print('Waiting for connection...')
            time.sleep(1)

        print(wlan.ifconfig())

        if wlan.status() == 3:
            print('WLAN Connected')
            teplota()
        # Pokud se nepřipojil, ukončit cyklus
        else:
            print('WLAN NOT Connected to WiFi')
            time.sleep(10)
            wifi_connect()


def teplota():

    # Detecting sensors on configured pin
    ds_pin = machine.Pin(config['sensor_pin'])
    ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
    sensors_roms = ds_sensor.scan()
    print('Detected sensors: ', sensors_roms)

    while True:
        temparray = []
        error = 0

        for device in sensors_roms:
            try:
                iddevice = list(device)[1]
                ds_sensor.convert_temp() # načítá ID čidla

                temp = ds_sensor.read_temp(device)

                if temp is None:
                    error = 1

                if temp > 500:
                    error = 1

                print('--------------------------')
                print("Device: ", iddevice, "   Temp: ", temp, " °C ")
                data = {
                    "sensorId" : iddevice,
                    "teplota": temp
                }

                # print(data)
                temparray.append(data)


                time.sleep(1)

            except Exception as e:
                print(e)
                time.sleep(10)
                machine.reset()

        print(temparray)
        if error == 0:
            print('-------- SENDING DATA TO API----------')
            try:
                url = 'http://192.168.1.109:8081/temp/setData'

                response = urequests.post(url, json=temparray)
                time.sleep(0.5)
                # print(response.text)

                gc.collect()
                # Zpracování odpovědi
                if response.status_code == 201:
                    print("Data byla úspěšně odeslána.")
                    response.close()
                else:
                    print(f"Chyba při odesílání dat: {response.text}")
                    response.close()


            except Exception as e:
                print(e)
                time.sleep(5)
                machine.reset()


        time.sleep(10)

def main():
    #gc.enable()  # maže paměť
    wifi_connect()
    teplota()


if __name__ == "__main__":
    main()
