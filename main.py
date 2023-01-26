import sys
import machine
import network
import socket
import time
import onewire
import ds18x20
import _thread
import json
import os

temparray = []
temparray_history = []
rodzil_teplot = 0
sLock = _thread.allocate_lock()


def get_request_file(request_file_name):
    with open(request_file_name, 'r') as file:
        file_requested = file.read()
    return file_requested


config = json.load(open("config.json"))


wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(config['wifi_ssid'], config['wifi_password'])
connectCount = 0

max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    time.sleep(10)

print(wlan.status())
if wlan.status() != 3:
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    print('ip = ' + status[0])

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)

print('listening on', addr)

# Detecting sensors on configured pin
ds_pin = machine.Pin(config['sensor_pin'])
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
sensors_roms = ds_sensor.scan()
print('Detected sensors: ', sensors_roms)


# Mesuring temperature of sensors
def TempSensor():
    while True:
        highesttemp = -200
        lowesttemp = 200
        ds_sensor.convert_temp()
        global temparray
        global rodzil_teplot
        temparray = []
        print('--------------------------')

        for device in sensors_roms:
            temp = ds_sensor.read_temp(device)
            print("Temp: ", temp, " °C  device=", device)
            temparray.append(round(temp, 1))
            if temp > highesttemp:
                highesttemp = temp
            elif temp < lowesttemp:
                lowesttemp = temp

        temparray_history.append(temparray)
        # rodzil_teplot = highesttemp - lowesttemp
        # print("rozdil teplot: ", rodzil_teplot)
        time.sleep(1)


_thread.start_new_thread(TempSensor, ())

while True:
    try:
        cl, addr = s.accept()
        clientIP = addr[0]
        print('Client connected from', clientIP)
        request = cl.recv(1024)
        request = str(request)
        global response
        try:
            request = request.split()[1]
            # print(request)

        except IndexError:
            pass

        # works out what the file type of the request is so we send back the file as the correct MIME type
        if '.html' in request:
            file_header = 'HTTP/1.1 200 OK\r\nContent-type: application/json\r\n\r\n'
            global response
            if request == "/reload.html":
                responsejson = {"actual": temparray, "history": temparray_history}
                response = json.dumps(responsejson)
            else:
                response = get_request_file(request)

        elif '.css' in request:
            file_header = 'HTTP/1.1 200 OK\r\nContent-Type: text/css\r\n\r\n'
            global response
            response = get_request_file(request)

        elif '.js' in request:
            file_header = 'HTTP/1.1 200 OK\r\nContent-Type: text/javascript\r\n\r\n'
            global response
            response = get_request_file(request)

        elif '.svg' in request:
            file_header = 'HTTP/1.1 200 OK\r\nContent-Type: image/svg+xml\r\n\r\n'

        elif '.svgz' in request:
            file_header = 'HTTP/1.1 200 OK\r\nContent-Type: image/svg+xml\r\n\r\n'

        elif '.png' in request:
            file_header = 'HTTP/1.1 200 OK\r\nContent-Type: image/png\r\n\r\n'

        elif '.ico' in request:
            file_header = 'HTTP/1.1 200 OK\r\nContent-Type: image/x-icon\r\n\r\n'

        else:
            file_header = 'HTTP/1.1 200 OK\r\nContent-type: text/html\r\n\r\n'
            global response
            temparray_string = str(temparray)
            # print(temparray_string, type(temparray_string))
            response = get_request_file("index.html").format(temparray_string, rodzil_teplot)

        cl.send(file_header)
        # sends the content back
        cl.send(response)
        # finishes up
        cl.close()
        response = ""

    except OSError as e:
        cl.close()
        print('connection closed')
