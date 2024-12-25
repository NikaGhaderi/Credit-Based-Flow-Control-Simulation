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

DEVICES_NUMBER = 4

PROGRAM_START_TIME = time.time()


class Switch:
    def __init__(self, incoming_queues, outgoing_queues, logger, STATE, PRIORITY_OPTION):
        self.incoming_queues = incoming_queues  # Queues from Devices to Switch
        self.outgoing_queues = outgoing_queues  # Queues from Switch to Devices
        self.STATE = STATE
        self.PRIORITY_MODE = PRIORITY_OPTION

        self.buffers = {
            1: BUFFER_SIZES[1],
            2: BUFFER_SIZES[2],
            3: BUFFER_SIZES[3],
            4: BUFFER_SIZES[4]
        }
        self.running = True
        self.logger = logger
        self.lock = threading.Lock()

    def listen(self):
        self.logger.info("Switch: Listening for incoming packets...")
        while self.running:
            # Initialize a data structure (dictionary of lists) to save packets and device_id for each target device
            packets_to_process = {}

            for device_id, q in self.incoming_queues.items():
                if not q.empty():
                    packet = q.get()
                    target_device = packet["target"]  # Get the target device for this packet
                    # Add a tuple (device_id, packet) to the list for the target device
                    if target_device not in packets_to_process:
                        packets_to_process[target_device] = []
                    packets_to_process[target_device].append((device_id, packet))

            # Now, sort the packets before processing
            if self.STATE == 1:
                # If state 1, no sorting needed
                pass
            else:
                # State 2: Handle sorting based on priority mode, for each target device
                for target_device, packets in packets_to_process.items():
                    if self.PRIORITY_MODE == 1:
                        # Option 1: Prioritize packet type 1 before type 2 for this specific target_device
                        packets.sort(key=lambda pkt: pkt[1]["type"] == 2)  # Type 1 comes before Type 2
                    elif self.PRIORITY_MODE == 2:
                        # Option 2: Prioritize packet type 1 only when buffer is low for this specific target_device
                        buffer_usage = self.buffers[target_device]
                        if buffer_usage < 0.10 * BUFFER_SIZES[target_device]:
                            # If buffer is low, prioritize type 1 over type 2 for this target device
                            packets.sort(key=lambda pkt: pkt[1]["type"] == 2)  # Type 1 comes before Type 2
                    elif self.PRIORITY_MODE == 3:
                        # Option 3: Process 2 packets of type1 for every 1 packet of type2
                        type1_packets = [pkt for pkt in packets if pkt[1]["type"] == "type1"]
                        type2_packets = [pkt for pkt in packets if pkt[1]["type"] == "type2"]

                        # Combine type1 and type2 packets in a 2:1 ratio
                        combined_packets = []
                        type1_index, type2_index = 0, 0

                        # Create a loop to maintain the 2:1 processing ratio
                        while type1_index < len(type1_packets) or type2_index < len(type2_packets):
                            if type1_index < len(type1_packets):
                                combined_packets.append(type1_packets[type1_index])
                                type1_index += 1
                            if type1_index < len(type1_packets):
                                combined_packets.append(type1_packets[type1_index])
                                type1_index += 1
                            if type2_index < len(type2_packets):
                                combined_packets.append(type2_packets[type2_index])
                                type2_index += 1

                        # Replace packets with the combined list maintaining the 2:1 ratio
                        packets[:] = combined_packets

            # Process all packets for each target device after sorting
            for target_device, packets in packets_to_process.items():
                for device_id, packet in packets:
                    self.process_packet(device_id, packet)

            # time.sleep(0.1)  # Prevents tight loop; adjust as needed

    def broadcast(self, message, exclude=None):
        if exclude is None:
            exclude = []
        for device_id in self.outgoing_queues:
            if device_id not in exclude:
                self.outgoing_queues[device_id].put(message)

    def process_packet(self, source_device, packet):
        target_device = packet['target']
        packet_size = packet['size']

        # Threshold to trigger backpressure (e.g., 80% buffer utilization)
        BACKPRESSURE_THRESHOLD = 0.4 * BUFFER_SIZES[target_device]
        CRITICAL_THRESHOLD = 0
        packet_type = packet.get('type', 'unknown')

        with self.lock:  # Lock the critical section
            if self.buffers[target_device] >= packet_size:
                # Enough space, send the packet
                self.buffers[target_device] -= packet_size
                self.outgoing_queues[target_device].put(packet)
                self.logger.info(
                    f"Switch: {packet_type} packet from Device {source_device} to Device {target_device} sent. "
                    f"Remaining buffer for Device {target_device}: {self.buffers[target_device]} bytes."
                )

                # Check if buffer usage exceeds threshold
                if self.buffers[target_device] < BACKPRESSURE_THRESHOLD and self.buffers[target_device] != 0:
                    # Send a backpressure signal (e.g., via a special packet or message)
                    backpressure_packet = {"id": "BACKPRESSURE", "size": 0, "target": target_device}
                    self.broadcast(backpressure_packet, exclude=[target_device])

                    self.logger.warning(
                        f"Switch: Backpressure signal sent to devices for Device {target_device} "
                        f"due to high buffer utilization."
                    )

                if self.buffers[target_device] == CRITICAL_THRESHOLD:
                    # Send a critical backpressure signal to stop sending
                    critical_backpressure_packet = {"id": "CRITICAL_BACKPRESSURE", "size": 0, "target": target_device}
                    self.broadcast(critical_backpressure_packet, exclude=[target_device])
                    self.logger.critical(
                        f"Switch: Critical backpressure signal sent to all devices to stop sending to Device {target_device} "
                        f"due to buffer overflow."
                    )

            else:
                # Packet is dropped due to insufficient buffer space
                self.logger.warning(
                    f"Switch: Packet from Device {source_device} to Device {target_device} dropped due to buffer overflow. "
                    f"Buffer space remaining: {self.buffers[target_device]} bits, Packet size: {packet_size} bits."
                )
                # Re-add the packet to the source device's queue
                self.incoming_queues[source_device].put(packet)
                self.logger.info(
                    f"Switch: Re-queued packet {packet['id']} from Device {source_device} back to incoming queue."
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
                    f"Switch: Restored credit for Device {device_id} by {restored / 8} bytes. "
                    f"Current credit size: {self.buffers[device_id] / 8} bytes."
                )

                # Check if buffer usage is now below backpressure threshold
                BACKPRESSURE_THRESHOLD = 0.15 * BUFFER_SIZES[device_id]
                if self.buffers[device_id] >= BACKPRESSURE_THRESHOLD:
                    # Send "RESTORE" signal to all devices
                    restore_packet = {"id": "RESTORE", "size": 0, "target": device_id}
                    self.broadcast(restore_packet, exclude=[device_id])
                    self.logger.process(
                        f"Switch: Sent RESTORE signal for Device {device_id} as buffer usage is below the threshold."
                    )
                elif self.buffers[device_id] < BACKPRESSURE_THRESHOLD:
                    # Continue backpressure if threshold is still exceeded
                    backpressure_packet = {"id": "BACKPRESSURE", "size": 0, "target": device_id}
                    self.broadcast(backpressure_packet, exclude=[device_id])
                    self.logger.process(
                        f"Switch: Continued backpressure for Device {device_id} due to high buffer utilization."
                    )

    def stop(self):
        self.logger.info("Switch: Stopping switch operations...")
        self.running = False