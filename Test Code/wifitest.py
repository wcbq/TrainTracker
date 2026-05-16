import network
import time
import urequests

wlan = network.WLAN(network.STA_IF)
wlan.active(False)
time.sleep(1)
wlan.active(True)
time.sleep(1)

wlan.connect("network_name", "network_password")

timeout = 10
while not wlan.isconnected() and timeout > 0:
    print("Connecting...")
    time.sleep(1)
    timeout -= 1

if wlan.isconnected():
    print("Connected:", wlan.ifconfig()[0])
else:
    print("Failed to connect")
    
    
url = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si"
response = urequests.get(url)
print("Status:", response.status_code)
print("Bytes received:", len(response.content))
print(response.content[1])
response.close()
