import serial
import time

ESP32_PORT = '/dev/ttyUSB0'
ARDUINO_PORT = '/dev/ttyUSB1'
BAUD_RATE_ESP = 38400
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
    

def initialize_positions():
    global current_pos_x, current_pos_y, current_pos_z
    i = 0
    time.sleep(2)
    while i < 5:
        initial_data = read_esp32_data()
        if initial_data:
            current_pos_x, current_pos_y, current_pos_z = initial_data
            print(f"Initialized positions - X: {current_pos_x}, Y: {current_pos_y}, Z: {current_pos_z}")
        else:
            print("Failed to initialize positions. Using default values.")
        i += 1
        
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
    time.sleep(1.5)
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
    except Exception as e:
        print(f"Unexpected error: {e}")
    return None

def parse_esp32_data(response):
    try:
        if response.startswith("AK80"):
            parts = response[5:].split(',')

            if len(parts) == 9:
                pos_x = round(float(parts[0].strip()), 4)
                pos_y = round(float(parts[3].strip()), 4)
                pos_z = round(float(parts[6].strip()), 4)

                print(f"Parsed Data - pos_x: {pos_x}, pos_y: {pos_y}, pos_z: {pos_z}")
                return pos_x, pos_y, pos_z

    except ValueError as e:
        print(f"Error converting data to float: {e}")
    except Exception as e:
        print(f"Error parsing ESP32 data: {e}")
    return None


def delivery_logic():
    # Execute delivery steps
    change_chassis("x")
    send_movement_command("forward", 640)
    time.sleep(2)
    change_chassis("y")
    send_movement_command("left", 1680)
    time.sleep(2)
    change_chassis("x")
    send_movement_command("forward", 2550)
    time.sleep(3)
    change_chassis("stable")
    send_movement_command("down", 1.2)
    time.sleep(2)
    send_nano_command("release")
    time.sleep(1)
    send_nano_command("grasp")
    send_movement_command("up", 1.2)
    time.sleep(2)
    change_chassis("y")
    send_movement_command("right", 840)
    time.sleep(2)
    change_chassis("stable")
    send_movement_command("down", 1.5)
    send_nano_command("release")
    send_movement_command("up", 1.5)
    time.sleep(2)
    send_nano_command("grasp")
    change_chassis("y")
    send_movement_command("left", 840)
    change_chassis("stable")
    send_movement_command("down", 1.5)
    time.sleep(2)
    send_nano_command("release")
    send_nano_command("grasp")
    send_movement_command("up", 1.5)
    change_chassis("x")
    send_movement_command("backward", 2550)
    change_chassis("y")
    send_movement_command("right", 1680)
    change_chassis("x")
    send_movement_command("backward", 640)
    change_chassis("stable")
    send_movement_command("down", 1.2)
    send_nano_command("release")


if __name__ == "__main__":
    initialize_positions()
    delivery_logic()
    print("Delivery logic executed successfully.")
