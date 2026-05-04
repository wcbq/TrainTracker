from google.transit import gtfs_realtime_pb2
import requests
from datetime import datetime, timedelta

# Add or remove stops here
TrainStops = {
    "New Dorp Northbound":  "S22N",
    "New Dorp Southbound":  "S22S",
    #"Grant City Northbound": "S23N",
    #"Grant City Southbound": "S23S",
}

BUS_API_KEY = "e25112ec-d969-48bb-9b10-fcc2d8f7c8a5"

BUS_STOPS = {

    "SIM1C - Manhattan": ("201020", "SIM1C"),
    #"SIM1C - Staten Island": ("201124", "SIM1C"),

    "S79 - Bay Ridge":  ("201020", "S79+"),
    #"S79 - SI Mall":  ("201124", "S79+"),

    "S78 - St George":   ("201020", "S78"),
    #"S78 - Bricktown Mall":   ("201124", "S78"),
    
    "S76 - St George":   ("202390", "S76"),
    #"S76 - Oakwood":   ("202483", "S76"),

}


def get_next_bus(stop_id, line_ref):
    url = "http://bustime.mta.info/api/siri/stop-monitoring.json"
    params = {
        "key": BUS_API_KEY,
        "MonitoringRef": stop_id,
        "LineRef": f"MTA NYCT_{line_ref}",
    }
    response = requests.get(url, params=params)
    data = response.json()

    visits = data["Siri"]["ServiceDelivery"]["StopMonitoringDelivery"][0].get("MonitoredStopVisit", [])

    if not visits:
        return None

    call = visits[0]["MonitoredVehicleJourney"]["MonitoredCall"]
    time_str = call.get("ExpectedArrivalTime") or call.get("AimedArrivalTime")

    if not time_str:
        return None

    arrival = datetime.fromisoformat(time_str)
    return int((arrival - datetime.now(arrival.tzinfo)).seconds / 60)

FERRY_WEEKEND = [(h, m) for h in range(24) for m in (0, 30)]
FERRY_WEEKDAY_ST_GEORGE = [
    (0,0),(0,30),(1,0),(1,30),(2,0),(2,30),(3,0),(3,30),(4,0),(4,30),
    (5,0),(5,30),(6,0),(6,20),(6,40),(7,0),(7,15),(7,30),(7,45),(8,0),
    (8,15),(8,30),(8,45),(9,0),(9,30),(10,0),(10,30),(11,0),(11,30),
    (12,0),(12,30),(13,0),(13,30),(14,0),(14,30),(15,0),(15,30),(15,50),
    (16,10),(16,30),(16,50),(17,10),(17,30),(17,45),(18,0),(18,15),(18,30),
    (18,45),(19,0),(19,30),(20,0),(20,30),(21,0),(21,30),(22,0),(22,30),
    (23,0),(23,30)
]
#FERRY_WEEKDAY_WHITEHALL = [
#    (0,0),(0,30),(1,0),(1,30),(2,0),(2,30),(3,0),(3,30),(4,0),(4,30),
#    (5,0),(5,30),(6,0),(6,30),(6,50),(7,10),(7,30),(7,45),(8,0),(8,15),
#    (8,30),(8,45),(9,0),(9,15),(9,30),(10,0),(10,30),(11,0),(11,30),
#    (12,0),(12,30),(13,0),(13,30),(14,0),(14,30),(15,0),(15,30),(16,0),
#    (16,20),(16,40),(17,0),(17,15),(17,30),(17,45),(18,0),(18,15),(18,30),
#    (18,45),(19,0),(19,20),(19,40),(20,0),(20,30),(21,0),(21,30),(22,0),
#    (22,30),(23,0),(23,30)
#]

def get_next_ferry():
    now = datetime.now()
    schedule = FERRY_WEEKEND if (is_weekend()) else FERRY_WEEKDAY_ST_GEORGE
    today_times = [
        datetime(now.year, now.month, now.day, h, m)
        for h, m in schedule
    ]
    upcoming = [t for t in today_times if t > now]
    return int((upcoming[0] - now).seconds / 60)

def is_weekend():
    return datetime.now().weekday() >= 5

url = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si"
response = requests.get(url)
feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(response.content)

# Build a results dict with one next arrival per stop
results = {name: None for name in TrainStops}

for entity in feed.entity:
    if entity.HasField('trip_update'):
        for stop in entity.trip_update.stop_time_update:
            for name, stop_id in TrainStops.items():
                if stop.stop_id == stop_id and stop.arrival.time > 0:
                    mins = (stop.arrival.time - datetime.now().timestamp()) / 60
                    if mins >= 0:
                        if results[name] is None or mins < results[name]:
                            results[name] = mins

ferry_mins = get_next_ferry()

# Print results
print("\n-==STATEN ISLAND RAILWAY==-\n") #train results
for name, mins in results.items():
    if mins is None:
        print(f"{name}: No upcoming trains")
    elif mins < 1:
        print(f"{name}: Arriving Now")
    else:
        print(f"{name}: {int(mins)} min")

print("\n -==STATEN ISLAND FERRY==- \n")
if ferry_mins < 1: #ferry arrivals
    print(f"SI Ferry Whitehall Bound: Arriving Now")
else: 
    print(f"SI Ferry Whitehall Bound: {int(ferry_mins)} min")

print("\n     -==BUS TIMES==-    \n")
for name, (stop_id, line) in BUS_STOPS.items(): #bus arrivals
    mins = get_next_bus(stop_id, line)
    print(f"{name}: {mins} min" if mins is not None and mins <= 60 else f"{name}: No buses")