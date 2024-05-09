import traci
import os
import random
import pymongo
import redis

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["traffic_data"]
vehicle_collection = db["vehicles_count"]
vehicle_data_collection = db["vehicles_data"]

redis_host = "localhost"
redis_port = 6379
redis_db = 0
redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)

vehicle_count = {"private": 0, "bus": 0, "emergency": 0}
max_waiting_time = {"private": 0, "bus": 0, "emergency": 0}
max_waiting_counts = {'1i_0': 0, '2i_0': 0, '3i_0': 0, '4i_0': 0}

CAR_DEPART_SPEED = 10

used_ids = set()

STATE_GREEN = "GGGGrrrrGGGGrrrr"
STATE_YELLOW = "YYYYrrrrYYYYrrrr"
STATE_RED = "rrrrGGGGrrrrGGGG"
current_state = STATE_RED
GREEN_TIME = 60
YELLOW_TIME = 5
current_timer = 0

def main():
    global current_state, current_timer
    script_dir = os.path.dirname(os.path.realpath(__file__))

    try:
        print("Attempting to connect to TraCI...")
        traci.start(["sumo-gui", "-c", os.path.join(script_dir, "final.sumocfg")])
        print("Connected to TraCI.")
    except Exception as e:
        print(f"Error connecting to TraCI: {e}")
        return

    print("SUMO simulation started.")

    step = 0
    try:
        while step <= 1000:
            traci.simulationStep()
            step += 1

            if step % 50 == 0:
                add_random_vehicles()

            if step % 10 == 0:
                collect_simulation_data()
                adjust_traffic_lights()
                update_state()
                update_max_waiting_counts()
                update_redis_waiting_counts()

            if current_state != STATE_RED:
                current_timer += 1
                if current_timer >= GREEN_TIME:
                    switch_traffic_light_state("1", STATE_YELLOW)
                elif current_timer >= GREEN_TIME + YELLOW_TIME:
                    switch_traffic_light_state("1", STATE_RED)

        print_max_waiting_counts()
        store_max_waiting_counts_in_redis()
        print_vehicle_counts()
        print("Simulation ended.")
    except Exception as e:
        print(f"Error during simulation loop: {e}")

    traci.close()
    client.close()

def add_random_vehicles():
    private_count = random.randint(5, 15)
    bus_emergency_count = random.randint(1, 5)

    for _ in range(private_count):
        vehicle_type = "private"
        traci.vehicle.add(generate_unique_id(), random.choice(["r_0", "r_1", "r_2", "r_3"]),
                          typeID=vehicle_type, departSpeed=CAR_DEPART_SPEED, departPos="random")
        increment_vehicle_count(vehicle_type)

    for _ in range(bus_emergency_count):
        vehicle_type = random.choice(["bus", "emergency"])
        traci.vehicle.add(generate_unique_id(), random.choice(["r_0", "r_1", "r_2", "r_3"]),
                          typeID=vehicle_type, departSpeed=CAR_DEPART_SPEED, departPos="random")
        increment_vehicle_count(vehicle_type)

def generate_unique_id():
    while True:
        vehicle_id = f"vehicle_{random.randint(1, 1000)}"
        if vehicle_id not in used_ids:
            used_ids.add(vehicle_id)
            return vehicle_id

def collect_simulation_data():
    global vehicle_count, max_waiting_time

    vehicle_ids = traci.vehicle.getIDList()

    for vehicle_id in vehicle_ids:
        vehicle_type = traci.vehicle.getTypeID(vehicle_id)
        if vehicle_type in vehicle_count:
            vehicle_count[vehicle_type] += 1

        waiting_time = traci.vehicle.getWaitingTime(vehicle_id)
        if waiting_time > max_waiting_time[vehicle_type]:
            max_waiting_time[vehicle_type] = waiting_time

        lane_id = traci.vehicle.getLaneID(vehicle_id)
        speed = traci.vehicle.getSpeed(vehicle_id)

        vehicle_data = {
            "vehicle_id": vehicle_id,
            "vehicle_type": vehicle_type,
            "lane_id": lane_id,
            "speed": speed,
            "waiting_time": waiting_time,
            "time": traci.simulation.getCurrentTime()
        }

        vehicle_data_collection.insert_one(vehicle_data)

    simulation_data = {
        "time": traci.simulation.getCurrentTime(),
        "vehicle_count": vehicle_count.copy(),
        "max_waiting_time": max_waiting_time.copy()
    }

    vehicle_collection.insert_one(simulation_data)
    update_redis_vehicle_counts()

def increment_vehicle_count(vehicle_type):
    vehicle_count[vehicle_type] += 1
    update_redis_vehicle_counts()

def update_redis_vehicle_counts():
    for vehicle_type, count in vehicle_count.items():
        redis_client.hset("vehicle_counts", vehicle_type, count)

def detect_emergency_vehicles():
    # Get a list of all emergency vehicles within a certain range of the traffic light
    emergency_vehicles = []
    for vehicle_id in traci.vehicle.getIDList():
        if traci.vehicle.getTypeID(vehicle_id) == "emergency":
            position = traci.vehicle.getPosition(vehicle_id)
            if 0 <= position[0] <= 100 and 0 <= position[1] <= 100:
                lane_id = traci.vehicle.getLaneID(vehicle_id)
                emergency_vehicles.append({"vehicle_id": vehicle_id, "lane_id": lane_id})

    return emergency_vehicles


def adjust_traffic_lights():
    global current_state

    # Check if emergency vehicles are nearby
    emergency_detected = detect_emergency_vehicles()

    # Control traffic lights based on emergency detection
    if emergency_detected:
        switch_traffic_light_state("1", STATE_GREEN)
        print("Traffic light turned GREEN due to emergency vehicles.")
    else:
        switch_traffic_light_state("1", STATE_RED)
        print("Traffic light turned RED.")

def update_state():
    global current_state, current_timer
    # Your state update logic

def switch_traffic_light_state(lane_id, new_state):
    global current_state, current_timer

    # Check if the lane should turn green based on detection
    should_turn_green = lane_id in detect_emergency_vehicles()

    # Set the new state accordingly
    if should_turn_green:
        new_state = STATE_GREEN
    else:
        new_state = STATE_RED

    if current_state != new_state:
        if new_state == STATE_RED:
            traci.trafficlight.setRedYellowGreenState(lane_id, "rrrrGGGGrrrrGGGG")
            current_state = new_state
        elif new_state == STATE_YELLOW:
            traci.trafficlight.setRedYellowGreenState(lane_id, "YYYYrrrrYYYYrrrr")
            current_state = new_state
        elif new_state == STATE_GREEN:
            # Immediately switch to green if an emergency vehicle is detected
            if should_turn_green:
                traci.trafficlight.setRedYellowGreenState(lane_id, "GGGGrrrrGGGGrrrr")
                current_state = new_state
                current_timer = 0
            else:
                # Optionally, you can set a yellow state before turning green
                traci.trafficlight.setRedYellowGreenState(lane_id, "YYYYrrrrYYYYrrrr")
                current_state = STATE_YELLOW


def print_vehicle_counts():
    vehicle_counts = redis_client.hgetall("vehicle_counts")
    print("Vehicle Counts in Redis:")
    for vehicle_type, count in vehicle_counts.items():
        print(f"{vehicle_type}: {count.decode()}")

def update_redis_waiting_counts():
    for lane_id, count in max_waiting_counts.items():
        redis_client.hset("waiting_counts", lane_id, count)

def update_max_waiting_counts():
    global max_waiting_counts
    incoming_lanes = ["1i_0", "2i_0", "3i_0", "4i_0"]
    for lane_id in incoming_lanes:
        try:
            lane_cars = traci.lane.getLastStepVehicleNumber(lane_id)
            if lane_cars > max_waiting_counts[lane_id]:
                max_waiting_counts[lane_id] = lane_cars
        except traci.TraCIException as e:
            print(f"Error accessing lane {lane_id}: {e}")

def print_max_waiting_counts():
    print("Maximum Waiting Counts per Lane:")
    for lane_id, max_count in max_waiting_counts.items():
        print(f"{lane_id}: {max_count}")

def store_max_waiting_counts_in_redis():
    for lane_id, max_count in max_waiting_counts.items():
        redis_client.hset("max_waiting_counts", lane_id, max_count)

if __name__ == "__main__":
    main()
