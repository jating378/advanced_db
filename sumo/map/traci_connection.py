import traci

def save_bus_data(bus_id, bus_stops):
    try:
        # Attempt to save bus data
        traci.vehicle.setData(bus_id, "bus_stops", bus_stops)
    except Exception as e:
        # Handle encoding errors
        print("Error saving bus data:", e)

def main():
    # Connect to TraCI server
    traci.start(["sumo", "-c", "map1.sumocfg"])

    # Example bus data
    bus_id = "bus_1"
    bus_stops = [(stop.lane, stop.startPos, stop.endPos, stop.stoppingPlaceID, stop.stopFlags, stop.duration) for stop in traci.vehicle.getNextStops(bus_id)]

    # Save bus data
    save_bus_data(bus_id, bus_stops)

    # Close TraCI connection
    traci.close()

if __name__ == "__main__":
    main()
