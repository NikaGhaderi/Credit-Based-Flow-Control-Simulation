import threading
import queue
import time
import logging
from switch import Switch
from device1 import Device as Device1
from device2 import Device as Device2
from device3 import Device as Device3
from device4 import Device as Device4

STATE = 1
RATIO = 1
DURATION = 5
PRIORITY_OPTION = 1  # Default priority option

# === Define Custom 'PROCESS' Logging Level ===
PROCESS_LEVEL_NUM = 25
logging.addLevelName(PROCESS_LEVEL_NUM, "PROCESS")


def process(self, message, *args, **kws):
    if self.isEnabledFor(PROCESS_LEVEL_NUM):
        self._log(PROCESS_LEVEL_NUM, message, args, **kws)


# Add the 'process' method to the Logger class
logging.Logger.process = process


# === End of Custom Logging Level ===


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
    global STATE
    while True:
        try:
            user_input = input("Enter the simulation state \n"
                               "1: Packets are equal in priority and number.\n"
                               "2: Packets from type 1 have double priority "
                               "and are 4 times more common than packets of type 2.\n")
            STATE = int(user_input)
            if STATE == 1:
                RATIO = 1
                return
            elif STATE == 2:
                RATIO = 4
                get_priority_option()
                return
            else:
                print("Please enter a valid number for a state.\n")
                continue
        except ValueError:
            print("Invalid input. Please enter a positive integer.\n")


def get_priority_option():
    global PRIORITY_OPTION
    while True:
        try:
            user_input = input("Choose priority management option:\n"
                               "1) Packets of type 1 are always processed before packets of type 2.\n"
                               "2) Only when competing for remaining buffer space, packets of type 1 are preferred to "
                               "type 2.\n"
                               "3) Switch processes 2 packets of type 1 for every 1 packet of type 2.\n"
                               "Enter 1, 2, or 3:\n")

            PRIORITY_OPTION = int(user_input)
            if PRIORITY_OPTION in [1, 2, 3]:
                return
            else:
                print("Please enter a valid option (1, 2 or 3).\n")
        except ValueError:
            print("Invalid input. Please enter 1, 2 or 3.\n")


# Configure Logging: Setup two loggers
def setup_loggers():
    # === Simulation Logger ===
    simulation_logger = logging.getLogger("SimulationLogger")
    simulation_logger.setLevel(logging.DEBUG)

    # Erase previous content
    open('simulation.log', 'w').close()

    # Create a file handler for simulation.log
    fh_sim = logging.FileHandler("simulation.log")
    fh_sim.setLevel(logging.DEBUG)
    formatter_sim = logging.Formatter(
        fmt='[%(asctime)s] [%(threadName)s] [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    fh_sim.setFormatter(formatter_sim)
    simulation_logger.addHandler(fh_sim)

    simulation_logger.info("Switch is running. Ready to process packets...")

    # === Memory Logger ===
    memory_logger = logging.getLogger("MemoryLogger")
    memory_logger.setLevel(logging.DEBUG)

    # Erase previous content
    open('memory.log', 'w').close()

    # Create a file handler for memory.log
    fh_mem = logging.FileHandler("memory.log")
    fh_mem.setLevel(logging.DEBUG)
    formatter_mem = logging.Formatter(
        fmt='[%(asctime)s] [%(threadName)s] [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    fh_mem.setFormatter(formatter_mem)
    memory_logger.addHandler(fh_mem)

    memory_logger.info("Memory is running. Ready to process packets...")

    # Prevent logs from propagating to the root logger
    simulation_logger.propagate = False
    memory_logger.propagate = False

    return simulation_logger, memory_logger


# Initialize the loggers
simulation_logger, memory_logger = setup_loggers()


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
        Device1(1, incoming_queues[1], memory_logger, RATIO, DURATION, STATE, PRIORITY_OPTION),
        Device2(2, incoming_queues[2], memory_logger, RATIO, DURATION, STATE, PRIORITY_OPTION),
        Device3(3, incoming_queues[3], memory_logger, RATIO, DURATION, STATE, PRIORITY_OPTION),
        Device4(4, incoming_queues[4], memory_logger, RATIO, DURATION, STATE, PRIORITY_OPTION)
    ]

    # Outgoing queues: Switch sends to Devices
    outgoing_queues = {
        1: devices[0].received_packets,
        2: devices[1].received_packets,
        3: devices[2].received_packets,
        4: devices[3].received_packets
    }

    # Initialize the switch with both incoming and outgoing queues and priority option
    switch = Switch(incoming_queues, outgoing_queues, simulation_logger, STATE, PRIORITY_OPTION)
    switch_thread = threading.Thread(target=switch.listen, name="SwitchListener")
    buffer_thread = threading.Thread(target=switch.restore_buffers, name="BufferRestorer")

    # Create device threads
    device_threads = []
    for device in devices:
        device_thread_sender = threading.Thread(target=device.send_packets, name=f"Device{device.device_id}Sender")
        device_thread_processor = threading.Thread(target=device.process_incoming,
                                                   name=f"Device{device.device_id}Processor")  # Corrected name
        device_thread_alert = threading.Thread(target=device.check_alerts, name=f"Device{device.device_id}AlertHandler")
        device_threads.append(device_thread_sender)
        device_threads.append(device_thread_processor)
        device_threads.append(device_thread_alert)

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
    print("Simulation completed.")