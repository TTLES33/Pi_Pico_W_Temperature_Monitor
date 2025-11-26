import gc
import machine
import network
import time
import urequests
import json
import ds18x20
import onewire
import uasyncio

config = json.load(open("config.json"))
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

sensors_roms = []
ds_sensor = None

#watchdog - pokud nedostane data max každých 20s, restartuje program
wdt = machine.WDT(timeout=8000)
wdt.feed()


async def wifi_connect():
    global wlan, config
    print("Checking network...")
    if wlan.isconnected():
        print("Network already connected")
        return 1

    print("Connecting to network...")
    for i in config["wifi"]:  # Zkusit připojení k sítím
        ssid = i["ssid"]
        password = i["password"]

        wlan.connect(ssid, password)
        tries = 0
        while (wlan.isconnected() == False and tries < 5):
            tries += 1
            print("Waiting for connection.. (tries:", tries, ")")
            wdt.feed()
            await uasyncio.sleep(1)

        if wlan.isconnected():  # Připojeno
            print('WLAN Connected to WiFi')
            print('WLAN IP address:', wlan.ifconfig()[0])
            print('WLAN STATUS START:', wlan.status())
            print('WLAN SSID: ', ssid)
            print('WLAN wifi_password: ', password)
            return 1

    #no wifi connected
    print('WLAN NOT Connected, trying again in 10s')
    await wait_with_wtd(10)
    await wifi_connect()


async def get_sensors_with_retry():
    global sensors_roms, ds_sensor
    ds_pin = machine.Pin(config['sensor_pin'])
    ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))

    while not sensors_roms:
        wdt.feed()
        print("Scanning for sensors...")
        sensors_roms = ds_sensor.scan()  # **Await the async function**

        if not sensors_roms:
            print("No sensors found, retrying in 1 second...")
            await wait_with_wtd(1)

    return 1

async def read_temperatures():
    global sensors_roms, ds_sensor
    temparray = []
    temparrayKALEMP = []
    error = 0
    print('---------- READING TEMPERATURES ----------')
    try:
        ds_sensor.convert_temp()
        await uasyncio.sleep_ms(800)

        for device in sensors_roms:
            temp = ds_sensor.read_temp(device)
            iddevice = list(device)[1]

            if temp is None or temp > 85 or temp < -50:
                error = 1
                break

            print("Device: ", iddevice, "   Temp: ", temp, " °C ")
            temparray.append({
                "sensorId": iddevice,
                "teplota": temp
            })

            dataKALEMP = []
            dataKALEMP.append(str(iddevice))
            dataKALEMP.append(str(temp))
            temparrayKALEMP.append(dataKALEMP)


    except Exception as e:
        print(e)
        error = 1

    print("------------------------------------------")
    return temparray, temparrayKALEMP, error

async def send_data_to_server(url, temparray, serverName):
    if not temparray:
        return

    response = None
    try:
        response = urequests.post(url, json=temparray, timeout=4)
        if response.status_code == 201 or response.status_code == 200:
            print(f"Data byla úspěšně odeslána na {serverName}.")
        else:
            print(f"Chyba při odesílání dat: {response.text}")

    except Exception as e:
        print("Chaba při odesílání dat: ", e)

    finally:
        if response:
            try:
                response.close()
            except:
                pass

async def wait_with_wtd(count):
    for _ in range(count):
        await uasyncio.sleep(1)  # Sleep in 1s intervals to keep feeding watchdog
        wdt.feed()


async def main_loop():
    wdt.feed()
    # 1. Connect WiFi
    await wifi_connect()

    # 2. Find Sensors
    await get_sensors_with_retry()


    while True:
        wdt.feed()
        gc.collect()

        # Kontrola připojení k Wi-Fi
        await wifi_connect()

        # získání dat z senzorů
        temparray, temparrayKALEMP, error = await read_temperatures()

        # chyba senzorů
        if error == 1 or not temparray or not temparrayKALEMP:
            print("Error has occurred")
            await wait_with_wtd(10)
            continue

        wdt.feed()
        #odeslání dat na servery
        print('---------- SENDING DATA TO API  ----------')
        await send_data_to_server("http://192.168.1.109:8081/temp/setData", temparray, "NasServer")
        await send_data_to_server("https://www.kalemp.cz/teplomery/zapisdat.php", temparrayKALEMP, "KALEMP")
        print('------------------------------------------')

        await wait_with_wtd(10)


def main():
    try:
        uasyncio.run(main_loop())
    except KeyboardInterrupt:
        print("Stopped by user")
    except Exception as e:
        print("CRITICAL CRASH:", e)
        time.sleep(1)
        machine.reset() # Hard reboot on critical async failure

if __name__ == "__main__":
    main()

