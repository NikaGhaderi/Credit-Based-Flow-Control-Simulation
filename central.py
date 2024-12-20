import threading
import queue
import time
import logging
from switch import Switch
from device1 import Device as Device1
from device2 import Device as Device2
from device3 import Device as Device3
from device4 import Device as Device4

RATIO = 1
DURATION = 5

def get_simulation_duration():
    global DURATION
    while True:
        try:
            user_input = input("Enter the simulation duration in seconds (positive integer):\n")
            DURATION = int(user_input)
            if DURATION <= 0:
                print("Please enter a positive integer.\n")
                continue
            return
        except ValueError:
            print("Invalid input. Please enter a positive integer.\n")

def get_simulation_RATIO():
    global RATIO
    while True:
        try:
            user_input = input("Enter the simulation state \n"
                               "1: Packets are equal in priority and number.\n"
                               "2: Packets from type 1 have double priority "
                               "and are 4 times more common that packets of type 2\n")
            state = int(user_input)
            if state == 1:
                RATIO = 1
            elif state == 2:
                RATIO = 4
            else:
                print("Please enter a valid number for a state.\n")
                continue
            return
        except ValueError:
            print("Invalid input. Please enter a positive integer.\n")



# Configure Logging: Setup two loggers
def setup_loggers():

    # === Simulation Logger ===
    simulation_logger = logging.getLogger("SimulationLogger")
    simulation_logger.setLevel(logging.DEBUG)

    # Erase previous content
    open('simulation.log', 'w').close()

    # Create a file handler for simulation.log
    fh_sim = logging.FileHandler("simulation.log", mode='a')
    fh_sim.setLevel(logging.DEBUG)
    formatter_sim = logging.Formatter(
        fmt='[%(asctime)s] [%(threadName)s] [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    fh_sim.setFormatter(formatter_sim)
    simulation_logger.addHandler(fh_sim)

    # === Memory Logger ===
    memory_logger = logging.getLogger("MemoryLogger")
    memory_logger.setLevel(logging.DEBUG)

    # Erase previous content
    open('memory.log', 'w').close()

    # Create a file handler for memory.log
    fh_mem = logging.FileHandler("memory.log", mode='a')
    fh_mem.setLevel(logging.DEBUG)
    formatter_mem = logging.Formatter(
        fmt='[%(asctime)s] [%(threadName)s] [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    fh_mem.setFormatter(formatter_mem)
    memory_logger.addHandler(fh_mem)

    # Prevent logs from propagating to the root logger
    simulation_logger.propagate = False
    memory_logger.propagate = False

    return simulation_logger, memory_logger

# Initialize the loggers
simulation_logger, memory_logger = setup_loggers()

DURATION = 5  # Simulation duration in seconds

def stop_simulation(switch, devices, logger):
    # Signal the switch and devices to stop
    logger.info("Stopping simulation...")
    switch.running = False
    for device in devices:
        device.running = False

if __name__ == "__main__":

    get_simulation_duration()
    get_simulation_RATIO()

    simulation_logger.info("Starting simulation...")

    # Shared queues for devices (Incoming queues: Devices send to Switch)
    incoming_queues = {
        1: queue.Queue(),
        2: queue.Queue(),
        3: queue.Queue(),
        4: queue.Queue()
    }

    # Initialize devices first to access their received_packets
    devices = [
        Device1(1, incoming_queues[1], memory_logger, RATIO, DURATION),
        Device2(2, incoming_queues[2], memory_logger, RATIO, DURATION),
        Device3(3, incoming_queues[3], memory_logger, RATIO, DURATION),
        Device4(4, incoming_queues[4], memory_logger, RATIO, DURATION)
    ]

    # Outgoing queues: Switch sends to Devices
    outgoing_queues = {
        1: devices[0].received_packets,
        2: devices[1].received_packets,
        3: devices[2].received_packets,
        4: devices[3].received_packets
    }

    # Initialize the switch with both incoming and outgoing queues
    switch = Switch(incoming_queues, outgoing_queues, simulation_logger)
    switch_thread = threading.Thread(target=switch.listen, name="SwitchListener")
    buffer_thread = threading.Thread(target=switch.restore_buffers, name="BufferRestorer")

    # Create device threads
    device_threads = []
    for device in devices:
        device_thread_sender = threading.Thread(target=device.send_packets, name=f"Device{device.device_id}Sender")
        device_thread_processor = threading.Thread(target=device.process_incoming, name=f"Device{device.device_id}Processor")  # Corrected name
        device_threads.append(device_thread_sender)
        device_threads.append(device_thread_processor)

    # Start the switch and device threads
    switch_thread.start()
    buffer_thread.start()
    for thread in device_threads:
        thread.start()

    # Run the simulation for DURATION seconds
    time.sleep(DURATION)

    # Stop the switch and devices
    stop_simulation(switch, devices, simulation_logger)

    # Wait for all threads to finish
    switch_thread.join()
    buffer_thread.join()
    for thread in device_threads:
        thread.join()

    simulation_logger.info("Simulation completed.")