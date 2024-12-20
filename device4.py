# import threading
# import time
# import random
# import queue
#
# DURATION = 5
#
# TRANSMISSION_RATES = {
#     1: {2: 10, 3: 20, 4: 30},
#     2: {1: 30, 3: 10, 4: 20},
#     3: {1: 20, 2: 30, 4: 10},
#     4: {1: 10, 2: 20, 3: 30}
# }
#
# PROCESS_RATE = 10
# class Device:
#     def __init__(self, device_id, switch_queue):
#         self.device_id = device_id
#         self.switch_queue = switch_queue
#         self.running = True
#         self.outgoing_packets = TRANSMISSION_RATES[device_id]
#         self.received_packets = queue.Queue()
#
#     def process_incoming(self):
#         start_time = time.time()
#         while self.running and time.time() - start_time < DURATION:
#             time.sleep(1)  # Process packets every second
#             processed_packets = []
#             for _ in range(PROCESS_RATE):
#                 if not self.received_packets.empty():
#                     packet = self.received_packets.get()
#                     processed_packets.append(packet)
#
#                 if processed_packets:
#                     print(f"Device {self.device_id}: Processed packets: {[p['id'] for p in processed_packets]}.\n")
#
#     def send_packets(self):
#         start_time = time.time()
#         while self.running and time.time() - start_time < DURATION:
#             for target_device, rate in self.outgoing_packets.items():
#                 for _ in range(rate):
#                     packet_id = random.randint(1000, 9999)
#                     packet = {"id": packet_id, "size": 512, "target": target_device}
#                     self.switch_queue.put(packet)
#                     # print(f"Device {self.device_id}: Sent packet {packet_id} to Device {target_device}.\n")
#                 time.sleep(1 / sum(self.outgoing_packets.values()))
#
#
#
# if __name__ == "__main__":
#     # Connect to the switch's queue
#     switch_queue = queue.Queue()  # This needs to be shared with `switch.py`
#
#     device = Device(4, switch_queue)
#     send_thread = threading.Thread(target=device.send_packets)
#     process_thread = threading.Thread(target=device.process_incoming)
#
#     send_thread.start()
#     process_thread.start()


# device2.py
import threading
import time
import random
import queue
import logging

DURATION = 5

TRANSMISSION_RATES = {
    1: {2: 10, 3: 20, 4: 30},
    2: {1: 10, 3: 20, 4: 30},
    3: {1: 10, 2: 20, 4: 30},
    4: {1: 10, 2: 20, 3: 30}
}

PROCESS_RATE = 10

class Device:
    def __init__(self, device_id, switch_queue, logger):
        self.device_id = device_id
        self.switch_queue = switch_queue
        self.running = True
        self.outgoing_packets = TRANSMISSION_RATES[device_id]
        self.received_packets = queue.Queue()
        self.logger = logger

    def process_incoming(self):
        start_time = time.time()
        while self.running and time.time() - start_time < DURATION:
            time.sleep(1)  # Process packets every second
            processed_packets = []
            for _ in range(PROCESS_RATE):
                if not self.received_packets.empty():
                    packet = self.received_packets.get()
                    processed_packets.append(packet)

            if processed_packets:
                packet_ids = [p['id'] for p in processed_packets]
                self.logger.info(f"Device {self.device_id}: Processed packets: {packet_ids}.")

    def send_packets(self):
        start_time = time.time()
        while self.running and time.time() - start_time < DURATION:
            for target_device, rate in self.outgoing_packets.items():
                for _ in range(rate):
                    packet_id = random.randint(1000, 9999)
                    packet = {"id": packet_id, "size": 512, "target": target_device}
                    self.switch_queue.put(packet)
                    # self.logger.info(f"Device {self.device_id}: Sent packet {packet_id} to Device {target_device}.")
                time.sleep(1 / sum(self.outgoing_packets.values()))

    def stop(self):
        self.logger.info(f"Device {self.device_id}: Stopping packet transmission.")
        self.running = False

# Start the device only if device2.py is run directly (for standalone testing)
if __name__ == "__main__":
    # Configure logging similarly to central.py or import the logger
    logger = logging.getLogger("SimulationLogger")
    if not logger.handlers:
        fh = logging.FileHandler("simulation.log")
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            fmt='[%(asctime)s] [%(threadName)s] [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    # Connect to the switch's queue
    switch_queue = queue.Queue()  # This needs to be shared with `switch.py`

    device = Device(4, switch_queue, logger)
    send_thread = threading.Thread(target=device.send_packets, name="Device4Sender")
    process_thread = threading.Thread(target=device.process_incoming, name="Device4Processor")

    send_thread.start()
    process_thread.start()

    try:
        # Run the device indefinitely or implement your own termination condition
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Handle graceful shutdown on user interrupt
        device.stop()
        send_thread.join()
        process_thread.join()
        logger.info(f"Device {device.device_id} has been stopped gracefully.")