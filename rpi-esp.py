import serial
import time
import re
import threading

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

def update_positions():
    global current_pos_x, current_pos_y, current_pos_z, proceed
    while True:
        data = read_esp32_data()
        if data:
            current_pos_x, current_pos_y, current_pos_z = data
            if proceed:
                proceed=False
                print(f"positions - X: {current_pos_x}, Y: {current_pos_y}, Z: {current_pos_z}")
        else:
            print("Failed to initialize positions. Using default values.")
        
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
def send_movement_command(direction, mode, distance):
    global current_pos_x, current_pos_y, current_pos_z
    # distance = distance/1000        
    # latest_data = read_esp32_data()
    # if latest_data:
    #     current_pos_x, current_pos_y, current_pos_z = latest_data

    cmd = ""
    if direction == "forward":
        current_pos_x += distance
        cmd = f"MOVX,{mode},{current_pos_x:.4f}"
    elif direction == "backward":
        current_pos_x -= distance
        cmd = f"MOVX,{mode},{current_pos_x:.4f}"

    elif direction == "left":
        current_pos_y += distance
        cmd = f"MOVY,{mode},{current_pos_y:.4f}"

    elif direction == "right":
        current_pos_y -= distance
        cmd = f"MOVY,{mode},{current_pos_y:.4f}"

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

def change_chassis(chassis_command, esp32_serial):

    # Map chassis command to the corresponding POLO command
    chassis_map = {
        "stable": "POLO,0",
        "x": "POLO,1",
        "y": "POLO,2"
    }
    
    if chassis_command not in chassis_map:
        print(f"Invalid chassis command: {chassis_command}")
        return

    command = chassis_map[chassis_command]
    esp32_serial.write((command + '\n').encode())
    print(f"Sent chassis command: {command}")

    print("Waiting for chassis change to complete...")
    time.sleep(1.5)
    print("Chassis change completed.")


def read_esp32_data():

    try:
        esp32_serial.reset_input_buffer()
        time.sleep(0.1)
        bad_line = esp32_serial.readline().decode('utf-8').strip()
        # print("before")
        # print(bad_line)
        response = esp32_serial.readline().decode('utf-8').strip()
        # print("after")
        # print(response)
        return parse_esp32_data(response)
    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return None


def parse_esp32_data(response):
    try:
        if response.startswith("AK80"):
            parts = response[5:].split(',')

            if len(parts) == 4:  # Expecting 4 parts now (3 positions and the flag)
                pos_x = round(float(parts[0].strip()), 2)
                pos_y = round(float(parts[1].strip()), 2)
                pos_z = round(float(parts[2].strip()), 2)
                stopped_by_sensor = int(parts[3].strip())  # Parse the flag as an integer

                print(f"Parsed Data - pos_x: {pos_x}, pos_y: {pos_y}, pos_z: {pos_z}, stopped_by_sensor: {stopped_by_sensor}")
                return pos_x, pos_y, pos_z

    except ValueError as e:
        print(f"Error converting data to float: {e}")
    except Exception as e:
        print(f"Error parsing ESP32 data: {e}")
    return None



# def parse_esp32_data(response):
#     try:
#         if response.startswith("AK80"):
#             parts = response[5:].split(',')

#             if len(parts) == 9:
#                 pos_x = round(float(parts[0].strip()), 4)
#                 pos_y = round(float(parts[3].strip()), 4)
#                 pos_z = round(float(parts[6].strip()), 4)

#                 print(f"Parsed Data - pos_x: {pos_x}, pos_y: {pos_y}, pos_z: {pos_z}")
#                 return pos_x, pos_y, pos_z

#     except ValueError as e:
#         print(f"Error converting data to float: {e}")
#     except Exception as e:
#         print(f"Error parsing ESP32 data: {e}")
#     return None


def interactive_control():
    global proceed
    try:
        print("\nInteractive Robot Control")
        print("Commands:")
        print("  move <direction> <distance> - Move robot (forward, backward, left, right, up, down)")
        print("  chassis <mode> - Change chassis mode (stable, x, y)")
        print("  grasp - Close the gripper")
        print("  release - Open the gripper")
        print("  exit - Exit the program")

        while True:
            command = input("\nEnter command: ").strip().lower()
            # read_esp32_data()
            proceed=True


            if command.startswith("move"):
                parts = command.split()
                if len(parts) == 4:
                    direction = parts[1]
                    mode_str = parts[2]
                    try:
                        distance = float(parts[3])
                        mode = -1
                        if mode_str == "sensor-front":
                            mode = 1
                        elif mode_str == "sensor-back":
                            mode = 2
                        elif mode_str == "no-sensor":
                            mode = 0

                        if direction in ["forward", "backward", "left", "right", "up", "down"] and mode != -1:
                            send_movement_command(direction, mode, distance)
                        else:
                            print("Invalid direction or mode. Use valid direction and mode (sensor-front, sensor-back, no-sensor).")
                    except ValueError:
                        print("Invalid distance. Use a numeric value.")
                else:
                    print("Invalid format. Use: move <direction> <mode> <distance>")
                

            elif command.startswith("chassis"):
                parts = command.split()
                if len(parts) == 2:
                    chassis_mode = parts[1]
                    if chassis_mode in ["stable", "x", "y"]:
                        change_chassis(chassis_mode, esp32_serial)
                    else:
                        print("Invalid chassis mode. Use stable, x, or y.")
                else:
                    print("Invalid format. Use: chassis <mode>")

            elif command in ["grasp", "release", "fix", "unfix"]:
                send_nano_command(command)

            elif command == "exit":
                print("Exiting program...")
                break

            else:
                print("Invalid command. Use move, chassis, grasp, release, fix, unfix, or exit.")

    except KeyboardInterrupt:
        print("\nExiting program...")
    finally:
        esp32_serial.close()
        nano_serial.close()
        print("Serial ports closed.")

if __name__ == "__main__":
    current_pos_x = 0.0
    current_pos_y = 0.0
    current_pos_z = 0.0
    proceed = False
    # initialize_positions() 
    pos_thread = threading.Thread(target=update_positions)
    pos_thread.start()
    interactive_control()