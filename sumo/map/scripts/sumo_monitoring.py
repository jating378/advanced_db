import traci
import pymongo
import redis
import time
import logging
 
# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
# MongoDB setup
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["bus_data"]
bus_collection = db["buses"]
 
# Redis setup
redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)
 
# Configuration
SUMO_CONFIG_FILE = r"D:\Rohit\SRH Heidelberg Studies\AD\sumo\map\sumo_simulation\map1.sumocfg"
SIMULATION_STEP_DURATION = 0.01  # in seconds
PROXIMITY_THRESHOLD = 20  # Distance in meters within which the vehicle affects the signal
 
# Define traffic light positions manually (example coordinates)
#Bus1
traffic_light_positions = {
    '262447886': (502.64, 2223.12),
    '262447883': (643.43, 2300.88),
    'cluster_271355213_271359038': (692.30, 2314.50),
    '269846336': (786.23, 2351.83),
    '270731055': (919.94,2034.24),
    '269846340': (956.94,1925.68),
    '270418042': (1036.85,1947.01),
    'cluster_270055230_271345366': (1175.56,1989.26),
    '270055232': (1203.15,1897.19),
    '271341399': (1299.33,1586.95),
    'cluster_1822569794_271345328_272258438_272258441': (1374.46,1436.68),
    'cluster_2433632666_266747272_461988444': (1430.94,1353.08),
    'cluster_266747594_270429935': (2079.29,876.65),
    'cluster_17392533_2235605264': (385.05,879.04),
    'cluster_1146265607_1146275324_1146280572_1147317134_#10more': (759.13,1575.41)
}
 
# Define the green phases for each traffic light manually
green_phases = {
    '262447886': 0,
    '262447883': 0,
    'cluster_271355213_271359038': 4,
    '269846336': 0,
    '270731055': 4,
    '269846340': 2,
    '270418042': 2,
    'cluster_270055230_271345366': 2,
    '270055232': 0,
    '271341399': 0,
    'cluster_1822569794_271345328_272258438_272258441': 0,
    'cluster_2433632666_266747272_461988444': 0,
    'cluster_266747594_270429935': 0,
    'cluster_17392533_2235605264': 6,
    'cluster_1146265607_1146275324_1146280572_1147317134_#10more': 5
}

def main():
    try:
        # Check if a TraCI connection already exists
        if traci.getConnection():
            logger.info("TraCI connection is already active.")
            return
    except traci.exceptions.TraCIException:
        pass  # No active connection found, continue to establish a new one
 
    try:
        traci.start(["sumo-gui", "-c", SUMO_CONFIG_FILE])
        logger.info("Connected to TraCI.")
    except Exception as e:
        logger.error(f"Error connecting to TraCI: {e}")
        return
 
    try:
        while True:  # Run simulation loop indefinitely
            traci.simulationStep()
            control_traffic_lights()
            save_bus_data()
            time.sleep(SIMULATION_STEP_DURATION)
    except KeyboardInterrupt:
        pass
    except traci.exceptions.TraCIException as e:
        logger.error(f"Error during simulation loop: {e}")
    finally:
        traci.close()
        mongo_client.close()
 
def control_traffic_lights():
    vehicles = traci.vehicle.getIDList()
    for veh_id in vehicles:
        veh_position = traci.vehicle.getPosition(veh_id)
        for tl_id, tl_position in traffic_light_positions.items():
            distance = traci.simulation.getDistance2D(veh_position[0], veh_position[1], tl_position[0], tl_position[1], False)
            if distance < PROXIMITY_THRESHOLD:
                if tl_id in green_phases:
                    green_phase = green_phases[tl_id]
                    traci.trafficlight.setPhase(tl_id, green_phase)
            current_phase = traci.trafficlight.getPhase(tl_id)
            logger.info(f"Traffic Light {tl_id} is currently at phase {current_phase}")
 
def save_bus_data():
    bus_ids = traci.vehicle.getIDList()
    current_time = traci.simulation.getTime()
    for bus_id in bus_ids:
        bus_route = traci.vehicle.getRoute(bus_id)
        bus_stops = traci.vehicle.getStops(bus_id)
        bus_location = traci.vehicle.getPosition(bus_id)
        stop_data_list = []
        for stop_data in bus_stops:
            stop_data_dict = {
                "lane": stop_data.lane,
                "startPos": stop_data.startPos,
                "endPos": stop_data.endPos,
                "stoppingPlaceID": stop_data.stoppingPlaceID,
                "stopFlags": stop_data.stopFlags,
                "duration": stop_data.duration
            }
            stop_data_list.append(stop_data_dict)
        bus_data = {
            "bus_id": bus_id,
            "bus_route": bus_route,
            "bus_stops": stop_data_list,
            "bus_location": bus_location,
            "timestamp": current_time
        }
        try:
            bus_collection.insert_one(bus_data)
        except Exception as e:
            logger.error(f"Error saving bus data: {e}")
        redis_client.hset("bus_locations", bus_id, f"{bus_location[0]},{bus_location[1]}")
 
if __name__ == "__main__":
    main()