import serial
import time

# Serial port settings
ESP32_PORT = '/dev/ttyUSB0'
ARDUINO_PORT = '/dev/ttyUSB1'
BAUD_RATE_ESP = 38400
BAUD_RATE_NANO = 9600
TIMEOUT = 1

# Initialize serial connection
try:
    esp32_serial = serial.Serial(ESP32_PORT, BAUD_RATE_ESP, timeout=TIMEOUT)
    # nano_serial = serial.Serial(ARDUINO_PORT, BAUD_RATE_NANO, timeout=TIMEOUT)
    print(f"Connected to ESP32 on {ESP32_PORT}")
    # print(f"Connected to NANO on {ARDUINO_PORT}")
except Exception as e:
    print(f"Error initializing serial port: {e}")
    exit()

# Global positions
current_pos_x = 0.0
current_pos_y = 0.0
current_pos_z = 0.0
    
    
# Function to send a movement command
def send_movement_command(direction, distance):
    global current_pos_x, current_pos_y, current_pos_z
    cmd = ""

    if direction == "forward":
        target_pos_x = current_pos_x + distance
        cmd = f"AK80,{target_pos_x:.4f},{current_pos_y:.4f},{current_pos_z:.4f}"
    elif direction == "backward":
        target_pos_x = current_pos_x - distance
        cmd = f"AK80,{target_pos_x:.4f},{current_pos_y:.4f},{current_pos_z:.4f}"
    elif direction == "left":
        target_pos_y = current_pos_y + distance
        cmd = f"AK80,{current_pos_x:.4f},{target_pos_y:.4f},{current_pos_z:.4f}"
    elif direction == "right":
        target_pos_y = current_pos_y - distance
        cmd = f"AK80,{current_pos_x:.4f},{target_pos_y:.4f},{current_pos_z:.4f}"
    elif direction == "up":
        target_pos_z = current_pos_z + distance
        cmd = f"AK80,{current_pos_x:.4f},{current_pos_y:.4f},{target_pos_z:.4f}"
    elif direction == "down":
        target_pos_z = current_pos_z - distance
        cmd = f"AK80,{current_pos_x:.4f},{current_pos_y:.4f},{target_pos_z:.4f}"

    # Send the command to ESP32
    if cmd:
        try:
            esp32_serial.write((cmd + '\n').encode())
            print(f"Sent to ESP32: {cmd}")
        except Exception as e:
            print(f"Error sending to ESP32: {e}")

def change_chassis(chassis_command, esp32_serial):
    """
    Changes the chassis state of the robot.
    
    Args:
        chassis_command (str): The chassis command to send. Should be one of "stable", "x", or "y".
        esp_serial (serial.Serial): Serial connection to the ESP32.
    """
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


def read_esp32_data(esp32_serial):
    """
    Reads and parses a line of data from the ESP32 via serial communication.

    Args:
        esp32_serial (serial.Serial): A pre-initialized serial connection to the ESP32.
    
    Returns:
        str: The raw line of data received from the ESP32, or None if no valid data is received.
    """
    try:
        if esp32_serial.in_waiting > 0:
            # Read a single line of data
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
            # Remove "AK80" and split the remaining data by commas
            parts = response[5:].split(',')

            if len(parts) == 9:  # Ensure exactly 9 parts are present
                # Extract positions (x, y, z)
                pos_x = float(parts[0].strip())
                pos_y = float(parts[3].strip())
                pos_z = float(parts[6].strip())

                # Ensure 4 decimal points in the output
                pos_x = f"{pos_x:.4f}"
                pos_y = f"{pos_y:.4f}"
                pos_z = f"{pos_z:.4f}"

                # Debug output
                print(f"Parsed Data - pos_x: {pos_x}, pos_y: {pos_y}, pos_z: {pos_z}")

                return pos_x, pos_y, pos_z
            else:
                print(f"Unexpected number of data points: {len(parts)}")
    except ValueError as e:
        print(f"Error converting data to float: {e}")
    except Exception as e:
        print(f"Error parsing ESP32 data: {e}")
    return None



# Function to wait for the distance to be reached
def wait_until_target_reached(direction, distance):
    global current_pos_x, current_pos_y, current_pos_z
    target_reached = False
    target_pos_x = current_pos_x
    target_pos_y = current_pos_y
    target_pos_z = current_pos_z

    if direction in ["forward", "backward"]:
        target_pos_x += distance if direction == "forward" else -distance
    elif direction in ["left", "right"]:
        target_pos_y += distance if direction == "left" else -distance
    elif direction in ["up", "down"]:
        target_pos_z += distance if direction == "up" else -distance

    while not target_reached:
        data = read_esp32_data()
        if data:
            pos_x, pos_y, pos_z = data
            # Check if the target position is reached
            if (abs(pos_x - target_pos_x) < 0.001 and
                abs(pos_y - target_pos_y) < 0.001 and
                abs(pos_z - target_pos_z) < 0.001):
                print(f"Target reached: x={pos_x:.4f}, y={pos_y:.4f}, z={pos_z:.4f}")
                current_pos_x = pos_x
                current_pos_y = pos_y
                current_pos_z = pos_z
                target_reached = True
            else:
                print(f"Waiting for target... Current: x={pos_x:.4f}, y={pos_y:.4f}, z={pos_z:.4f}")
                send_movement_command(direction, distance)
        # time.sleep(0.5)

# Interactive control loop
def interactive_control():
    try:
        print("\nInteractive Robot Control")
        print("Commands:")
        print("  move <direction> <distance> - Move robot (forward, backward, left, right, up, down)")
        print("  chassis <mode> - Change chassis mode (stable, x, y)")
        print("  exit - Exit the program")

        while True:
            command = input("\nEnter command: ").strip().lower()

            if command.startswith("move"):
                parts = command.split()
                if len(parts) == 3:
                    direction = parts[1]
                    try:
                        distance = float(parts[2])
                        if direction in ["forward", "backward", "left", "right", "up", "down"]:
                            send_movement_command(direction, distance)
                            wait_until_target_reached(direction, distance)
                        else:
                            print("Invalid direction. Use forward, backward, left, right, up, or down.")
                    except ValueError:
                        print("Invalid distance. Use a numeric value.")
                else:
                    print("Invalid format. Use: move <direction> <distance>")

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

            elif command == "exit":
                print("Exiting program...")
                break

            else:
                print("Invalid command. Use move, chassis, or exit.")


    except KeyboardInterrupt:
        print("\nExiting program...")
    finally:
        esp32_serial.close()
        print("Serial port closed.")

if __name__ == "__main__":
    # interactive_control()
    while True:
        data = read_esp32_data(esp32_serial)
        # if data is not None:
            # print(f"Parsed data: {data}")
