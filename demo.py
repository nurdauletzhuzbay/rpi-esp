import serial
import time
from flask import Flask, request

ESP32_PORT = '/dev/ttyUSB0'
ARDUINO_PORT = '/dev/ttyUSB1'
BAUD_RATE_ESP = 19200
BAUD_RATE_NANO = 9600
TIMEOUT = 1

try:
    esp32_serial = serial.Serial(ESP32_PORT, BAUD_RATE_ESP, timeout=TIMEOUT)
    nano_serial = serial.Serial(ARDUINO_PORT, BAUD_RATE_NANO, timeout=TIMEOUT)
    print(f"Connected to ESP32 on {ESP32_PORT}")
    print(f"Connected to NANO on {ARDUINO_PORT}")
except Exception as e:
    print(f"Error initializing serial port: {e}")
    exit()

current_pos_x = 0.0
current_pos_y = 0.0
current_pos_z = 0.0
    
app = Flask(__name__)

def initialize_positions():
    global current_pos_x, current_pos_y, current_pos_z
    i = 0
    time.sleep(2)
    while i<5:
        
        initial_data = read_esp32_data()
        if initial_data:
            current_pos_x, current_pos_y, current_pos_z = initial_data
            print(f"Initialized positions - X: {current_pos_x}, Y: {current_pos_y}, Z: {current_pos_z}")
        else:
            print("Failed to initialize positions. Using default values.")
        i += 1
    
    return current_pos_x, current_pos_y, current_pos_z
        
def send_nano_command(command):
    try:
        if nano_serial.is_open:
            nano_serial.write((command + '\n').encode('utf-8'))
            print(f"Sent command to Nano: {command}")
        else:
            print("Nano serial port is not open.")
    except Exception as e:
        print(f"Error sending command to Nano: {e}")
        
# Function to send a movement command
def send_movement_command(direction, distance):
    global current_pos_x, current_pos_y, current_pos_z
    cmd = ""
    if direction == "forward":
        current_pos_x += distance
        cmd = f"MOVX,{current_pos_x:.4f}"
    elif direction == "backward":
        current_pos_x -= distance
        cmd = f"MOVX,{current_pos_x:.4f}"

    elif direction == "left":
        current_pos_y += distance
        cmd = f"MOVY,{current_pos_y:.4f}"

    elif direction == "right":
        current_pos_y -= distance
        cmd = f"MOVY,{current_pos_y:.4f}"

    elif direction == "up":
        current_pos_z += distance
        cmd = f"LIFT,{current_pos_z:.4f}"

    elif direction == "down":
        current_pos_z -= distance
        cmd = f"LIFT,{current_pos_z:.4f}"

    if cmd:
        try:
            esp32_serial.write((cmd + '\n').encode())
            print(f"Sent to ESP32: {cmd}")
        except Exception as e:
            print(f"Error sending to ESP32: {e}")

def change_chassis(chassis_command):
    # Map chassis command to the corresponding POLO command
    chassis_map = {
        "stable": "POLO,0",
        "x": "POLO,1",
        "y": "POLO,2"
    }
    
    if chassis_command not in chassis_map:
        print(f"Invalid chassis command: {chassis_command}")
        return

    # Send the chassis command to the ESP32
    command = chassis_map[chassis_command]
    esp32_serial.write((command + '\n').encode())
    print(f"Sent chassis command: {command}")

    # Wait for 1.5 seconds to allow the chassis change to complete
    print("Waiting for chassis change to complete...")
    time.sleep(2)
    print("Chassis change completed.")


def read_esp32_data():

    try:
        if esp32_serial.in_waiting > 0:
            response = esp32_serial.readline().decode('utf-8', errors='ignore').strip()
            if response:
                print(f"Raw data received: {response}")  # Debug raw data
                return parse_esp32_data(response.strip())
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        
def parse_esp32_data(response):
    try:
        if response.startswith("AK80"):
            parts = response[5:].split(',')

            if len(parts) == 4:  # Expecting 4 parts now (3 positions and the flag)
                pos_x = round(float(parts[0].strip()), 2)
                pos_y = round(float(parts[1].strip()), 2)
                pos_z = round(float(parts[2].strip()), 2)
                stopped_by_sensor = int(parts[3].strip())  # Parse the flag as an integer

                # print(f"Parsed Data - pos_x: {pos_x}, pos_y: {pos_y}, pos_z: {pos_z}, stopped_by_sensor: {stopped_by_sensor}")
                return pos_x, pos_y, pos_z

    except ValueError as e:
        print(f"Error converting data to float: {e}")
    except Exception as e:
        print(f"Error parsing ESP32 data: {e}")
    return None


def return_logic():
    send_movement_command("down", 1.22)
    time.sleep(7)
    send_nano_command("release")
    time.sleep(9)
    send_nano_command("grasp")
    send_movement_command("up", 1.22)
    time.sleep(16)
    change_chassis("x")
    send_movement_command("forward", 652)
    time.sleep(6)
    change_chassis("stable")
    send_movement_command("down", 1.75)
    time.sleep(20)
    send_nano_command("release")
    send_movement_command("up", 1.75)
    time.sleep(4)
    send_nano_command("grasp")

 
def delivery_logic():
    # Execute delivery steps
    # time.sleep(5)
    change_chassis("x")
    send_movement_command("forward", 652)
    time.sleep(6)
    change_chassis("y")
    send_movement_command("left", 1677)
    time.sleep(9)
    change_chassis("x")
    send_movement_command("forward", 2545)
    time.sleep(12)
    change_chassis("stable")
    send_movement_command("down", 1.35)
    time.sleep(7)
    send_nano_command("release")
    time.sleep(10)
    send_nano_command("grasp")
    send_movement_command("up", 1.35)
    time.sleep(17)
    change_chassis("y")
    send_movement_command("right", 853)
    time.sleep(7)
    change_chassis("stable")
    send_movement_command("down", 1.75)
    time.sleep(21)
    send_nano_command("release")
    send_movement_command("up", 1.75)
    time.sleep(4)
    send_nano_command("grasp")
    time.sleep(17)
    change_chassis("y")
    send_movement_command("left", 851)
    time.sleep(7)
    change_chassis("stable")
    send_movement_command("down", 1.75)
    time.sleep(7)
    send_nano_command("release")
    time.sleep(14)
    send_nano_command("grasp")
    send_movement_command("up", 1.75)
    time.sleep(21)
    change_chassis("x")
    send_movement_command("backward", 2552)
    time.sleep(12)
    change_chassis("y")
    send_movement_command("right", 1688)
    time.sleep(9)
    change_chassis("x")
    send_movement_command("backward", 638)
    time.sleep(6)
    change_chassis("stable")
    send_movement_command("down", 1.22)
    time.sleep(16)
    send_nano_command("release")
    send_movement_command("up", 1.22)
    time.sleep(4)
    send_nano_command("grasp")

    
    
    
    
    
@app.route('/delivery', methods=['GET'])
def delivery_flask():
        print("Executing delivery logic...")
        delivery_logic()
        return 0

@app.route('/return', methods=['GET'])
def return_flask():
        print("Executing return logic...")
        return_logic()
        return 0
           
if __name__ == "__main__":
    current_pos_x = 0.0
    current_pos_y = 0.0
    current_pos_z = 0.0
    initialize_positions()
    app.run(host='0.0.0.0', port=5000)
    # print("Press Enter to execute delivery logic...")
    # while True:
    #     user_input = input("\nPress Enter to start or type 'exit' to quit: ")
    #     if user_input.strip().lower() == 'exit':
    #         print("Exiting program.")
    #         break
    #     elif user_input.strip() == '':
    #         delivery_logic()
    #         print("Delivery logic executed successfully.")
