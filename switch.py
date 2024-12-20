# # Switch File: switch.py
# import threading
# import queue
# import time
#
# # Buffer size in kilobytes for each device
# BUFFER_SIZES = {
#     1: 4 * 1024 * 8,
#     2: 4 * 1024 * 8,
#     3: 4 * 1024 * 8,
#     4: 4 * 1024 * 8
# }
#
# PROCESS_RATE = 10  # Packets processed per second by each device
#
# PROGRAM_START_TIME = time.time()
# class Switch:
#     def __init__(self, queues):
#         self.queues = queues  # Incoming queues from devices
#         self.outgoing_queues = {1: queue.Queue(), 2: queue.Queue(), 3: queue.Queue(), 4: queue.Queue()}  # Outgoing queues to devices
#         self.buffers = {
#             1: BUFFER_SIZES[1],
#             2: BUFFER_SIZES[2],
#             3: BUFFER_SIZES[3],
#             4: BUFFER_SIZES[4]
#         }
#         self.running = True
#
#     def listen(self):
#         while self.running:
#             for device_id, q in self.queues.items():
#                 if not q.empty():
#                     packet = q.get()
#                     self.process_packet(device_id, packet)
#
#     def process_packet(self, source_device, packet):
#         target_device = packet['target']
#         packet_size = packet['size']
#         elapsed = time.time() - PROGRAM_START_TIME
#         # Check if the target device has enough buffer space
#         if self.buffers[target_device] >= packet_size:
#             self.buffers[target_device] -= packet_size
#             self.outgoing_queues[target_device].put(packet)
#             print(f"#{elapsed:.2f}# Switch: Packet from Device {source_device} to Device {target_device} sent. Remaining buffer for Device {target_device}: {self.buffers[target_device]} bytes.")
#         else:
#             print(f"#{elapsed:.2f}# Switch: Packet from Device {source_device} to Device {target_device} dropped due to buffer overflow.")
#
#     def restore_buffers(self):
#         while self.running:
#             time.sleep(1)  # Every second
#             for device_id in self.buffers.keys():
#                 elapsed = time.time() - PROGRAM_START_TIME
#                 restored_size = PROCESS_RATE * 512  # Restore buffer based on process rate
#                 self.buffers[device_id] = min(self.buffers[device_id] + restored_size, BUFFER_SIZES[device_id])
#                 print(f"#{elapsed:.2f}# Switch: Restored buffer for Device {device_id}. Current buffer size: {self.buffers[device_id]} bits.\n")
#
# # Start the switch
# if __name__ == "__main__":
#     # Shared queues for devices
#     shared_queues = {
#         1: queue.Queue(),
#         2: queue.Queue(),
#         3: queue.Queue(),
#         4: queue.Queue()
#     }
#
#     # Start the switch
#     switch = Switch(shared_queues)
#     switch_thread = threading.Thread(target=switch.listen)
#     buffer_thread = threading.Thread(target=switch.restore_buffers)
#
#     switch_thread.start()
#     buffer_thread.start()
#
#     print("Switch is running. Ready to process packets...")



# switch.py
import threading
import queue
import time
import logging

# Buffer size in bits for each device
BUFFER_SIZES = {
    1: 1 * 1024 * 8,
    2: 1 * 1024 * 8,
    3: 2 * 1024 * 8,
    4: 4 * 1024 * 8
}

PROCESS_RATE = 10  # Packets processed per second by each device

PROGRAM_START_TIME = time.time()

# === Define Custom 'PROCESS' Logging Level ===
PROCESS_LEVEL_NUM = 25
logging.addLevelName(PROCESS_LEVEL_NUM, "PROCESS")

def process(self, message, *args, **kws):
    if self.isEnabledFor(PROCESS_LEVEL_NUM):
        self._log(PROCESS_LEVEL_NUM, message, args, **kws)

# Add the 'process' method to the Logger class
logging.Logger.process = process
# === End of Custom Logging Level ===

class Switch:
    def __init__(self, incoming_queues, outgoing_queues, logger):
        self.incoming_queues = incoming_queues  # Queues from Devices to Switch
        self.outgoing_queues = outgoing_queues  # Queues from Switch to Devices

        self.buffers = {
            1: BUFFER_SIZES[1],
            2: BUFFER_SIZES[2],
            3: BUFFER_SIZES[3],
            4: BUFFER_SIZES[4]
        }
        self.running = True
        self.logger = logger

    def listen(self):
        self.logger.info("Switch: Listening for incoming packets...")
        while self.running:
            for device_id, q in self.incoming_queues.items():
                while not q.empty():
                    packet = q.get()
                    self.process_packet(device_id, packet)
            time.sleep(0.1)  # Prevents tight loop; adjust as needed

    def process_packet(self, source_device, packet):
        target_device = packet['target']
        packet_size = packet['size']
        elapsed = time.time() - PROGRAM_START_TIME
        # Check if the target device has enough buffer space
        if self.buffers[target_device] >= packet_size:
            self.buffers[target_device] -= packet_size
            self.outgoing_queues[target_device].put(packet)
            self.logger.info(
                f"Switch: Packet from Device {source_device} to Device {target_device} sent. "
                f"Remaining buffer for Device {target_device}: {self.buffers[target_device]/8} bytes."
            )
        else:
            self.logger.warning(
                f"Switch: Packet from Device {source_device} to Device {target_device} dropped due to buffer overflow."
            )

    def restore_buffers(self):
        self.logger.info("Switch: Buffer restoration thread started.")
        while self.running:
            time.sleep(1)  # Every second
            for device_id in self.buffers.keys():
                restored_size = PROCESS_RATE * 512  # Restore buffer based on process rate
                before_restore = self.buffers[device_id]
                self.buffers[device_id] = min(self.buffers[device_id] + restored_size, BUFFER_SIZES[device_id])
                restored = self.buffers[device_id] - before_restore
                self.logger.process(
                    f"Switch: Restored buffer for Device {device_id} by {restored/8} bytes. "
                    f"Current buffer size: {self.buffers[device_id]/8} bytes."
                )

    def stop(self):
        self.logger.info("Switch: Stopping switch operations...")
        self.running = False

# Start the switch only if switch.py is run directly (for standalone testing)
if __name__ == "__main__":
    # Configure logging similarly to central.py or import the logger
    import logging

    # Setup logger
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

    logger.info("Switch is running. Ready to process packets...")

    # Shared queues for devices
    shared_queues = {
        1: queue.Queue(),
        2: queue.Queue(),
        3: queue.Queue(),
        4: queue.Queue()
    }

    # Initialize the switch
    switch = Switch(shared_queues, logger)
    switch_thread = threading.Thread(target=switch.listen, name="SwitchListener")
    buffer_thread = threading.Thread(target=switch.restore_buffers, name="BufferRestorer")

    switch_thread.start()
    buffer_thread.start()

    try:
        # Run the switch indefinitely or implement your own termination condition
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Handle graceful shutdown on user interrupt
        switch.stop()
        switch_thread.join()
        buffer_thread.join()
        logger.info("Switch has been stopped gracefully.")