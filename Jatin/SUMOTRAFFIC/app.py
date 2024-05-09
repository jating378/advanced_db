from flask import Flask, render_template, jsonify
import pymongo
import redis

app = Flask(__name__)

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["traffic_data"]
vehicle_collection = db["vehicles_count"]
vehicle_data_collection = db["vehicles_data"]

# Connect to Redis
redis_host = "localhost"
redis_port = 6379
redis_db = 0
redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)

@app.route('/')
def index():
    # Retrieve data from MongoDB and Redis
    vehicle_counts = redis_client.hgetall("vehicle_counts")
    max_waiting_counts = redis_client.hgetall("max_waiting_counts")
    waiting_counts = redis_client.hgetall("waiting_counts")  # Added waiting_counts

    # Render the index.html template with the data
    return render_template('index.html', vehicle_counts=vehicle_counts, max_waiting_counts=max_waiting_counts, waiting_counts=waiting_counts)  # Passed waiting_counts to the template


@app.route('/update_data', methods=['GET'])
def update_data():
    # Update data from MongoDB and Redis
    vehicle_counts = redis_client.hgetall("vehicle_counts")
    max_waiting_counts = redis_client.hgetall("max_waiting_counts")
    waiting_counts = redis_client.hgetall("waiting_counts")  # Added waiting_counts

    # Return JSON response with the updated data
    return jsonify(vehicle_counts=vehicle_counts, max_waiting_counts=max_waiting_counts, waiting_counts=waiting_counts)


if __name__ == '__main__':
    app.run(debug=True)
