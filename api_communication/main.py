from flask import Flask, request, jsonify

app = Flask(__name__)

# Endpoint to handle GET requests from ESP32
@app.route('/esp32', methods=['GET'])
def handle_get():
    message = "Hello from Python server!"
    return jsonify({"message": message})

# Endpoint to handle POST requests from ESP32
@app.route('/esp32', methods=['POST'])
def handle_post():
    if request.is_json:
        data = request.get_json()
        print(f"Received data from ESP32: {data['data']}")

        # Send a response back to ESP32
        response = {"response": "Data received successfully"}
        return jsonify(response), 200
    else:
        return jsonify({"error": "Request must be JSON"}), 400

# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6678)
