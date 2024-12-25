import time
import random
import queue

TRANSMISSION_RATES = {
    1: {2: 10, 3: 20, 4: 30},
    2: {1: 10, 3: 20, 4: 30},
    3: {1: 10, 2: 20, 4: 30},
    4: {1: 10, 2: 20, 3: 30}
}

PROCESS_RATE = 10


class Device:
    def __init__(self, device_id, switch_queue, logger, RATIO, DURATION):
        self.device_id = device_id
        self.received_packets = queue.Queue()
        self.switch_queue = switch_queue
        self.running = True
        self.current_rates = TRANSMISSION_RATES[device_id].copy()
        self.logger = logger
        self.ratio_counter = 0
        self.RATIO = RATIO
        self.DURATION = DURATION


    def check_alerts(self):
        start_time = time.time()
        while self.running and time.time() - start_time < self.DURATION:
            try:
                # Look at all packets in the queue (non-destructive peek)
                all_packets = list(self.received_packets.queue)  # Get a snapshot of all packets in the queue

                for packet in all_packets:
                    if packet['id'] in ["BACKPRESSURE", "RESTORE", "CRITICAL_BACKPRESSURE"]:
                        # Remove the alert packet from the queue (destructive removal)
                        self.received_packets.queue.remove(packet)

                        # Process the alert
                        target_device = packet.get('target', None)
                        current_rate = self.current_rates[target_device]

                        if packet['id'] == "BACKPRESSURE":
                            self.current_rates[target_device] = max(1, current_rate // 2)
                            if current_rate != 1:
                                self.logger.warning(
                                    f"Device {self.device_id}: Received BACKPRESSURE signal. Slowing down "
                                    f"transmission to"
                                    f"Device {target_device} to {self.current_rates[target_device]}."
                                )
                        elif packet['id'] == "RESTORE":
                            self.current_rates[target_device] = min(
                                TRANSMISSION_RATES[self.device_id][target_device], current_rate + 1
                            )
                            if current_rate != TRANSMISSION_RATES[self.device_id][target_device]:
                                self.logger.info(
                                    f"Device {self.device_id}: Received RESTORE signal. Speeding up transmission to "
                                    f"Device {target_device} to {self.current_rates[target_device]}."
                                )
                        elif packet['id'] == "CRITICAL_BACKPRESSURE":
                            self.current_rates[target_device] = 0
                            if current_rate != 0:
                                self.logger.critical(
                                    f"Device {self.device_id}: Received CRITICAL_BACKPRESSURE signal. Stopping "
                                    f"transmission"
                                    f"to Device {target_device}."
                                )
            except Exception as e:
                self.logger.error(f"Device {self.device_id}: Error in handling alert: {e}")

            # Sleep for a short time to allow frequent checks
            time.sleep(0.0001)  # Check alerts every 100 ms

    def process_incoming(self):
        start_time = time.time()
        while self.running and time.time() - start_time < self.DURATION:

            # Log buffer status
            buffer_contents = list(self.received_packets.queue)
            filtered_buffer = [packet for packet in buffer_contents if packet['id'] not in ["BACKPRESSURE", "RESTORE",
                                                                                            "CRITICAL_BACKPRESSURE"]]

            if filtered_buffer:
                buffer_details = [{"id": packet['id'], "type": packet['type']} for packet in filtered_buffer]
                buffer_size = len(buffer_details)

                # Format the buffer details into a multi-line string if it exceeds 120 characters
                buffer_details_str = str(buffer_details)
                max_line_length = 120
                wrapped_buffer_details = '\n'.join(
                    [buffer_details_str[i:i + max_line_length] for i in
                     range(0, len(buffer_details_str), max_line_length)]
                )

                self.logger.info(
                    f"Buffer Status: Device {self.device_id}: Buffer Content (IDs and Types):\n{wrapped_buffer_details} "
                    f"Total Packets: {buffer_size}"
                )

            processed_packets = []
            counter = 0
            while True:
                if not self.received_packets.empty():
                    packet = self.received_packets.get()

                    # Ignore alert packets here (handled by `check_alerts`)
                    if packet['id'] in ["BACKPRESSURE", "RESTORE", "CRITICAL_BACKPRESSURE"]:
                        self.received_packets.put(packet)
                        continue
                    counter += 1
                    processed_packets.append(packet)
                    if counter == PROCESS_RATE:
                        break
                else:
                    break

            if processed_packets:
                # Include both packet ID and type in the log
                processed_details = [{"id": packet['id'], "type": packet['type']} for packet in processed_packets]

                # Convert the processed details into a string and wrap lines if necessary
                processed_details_str = str(processed_details)
                max_line_length = 120
                wrapped_processed_details = '\n'.join(
                    [processed_details_str[i:i + max_line_length] for i in
                     range(0, len(processed_details_str), max_line_length)]
                )

                self.logger.process(
                    f"Device {self.device_id}: Processed packets (IDs and Types):\n{wrapped_processed_details}."
                )

            time.sleep(1)  # Process packets every second

    def send_packets(self):
        """Send packets to the switch."""
        start_time = time.time()
        packets_to_send = []  # List to gather packets to send
        while self.running and time.time() - start_time < self.DURATION:
            for target_device, rate in self.current_rates.items():
                for _ in range(rate):
                    if self.ratio_counter <= 0:
                        packet_type = 'type1'
                        self.ratio_counter += 1
                    else:
                        packet_type = 'type2'
                        self.ratio_counter -= self.RATIO

                    packet_id = random.randint(1000, 9999)
                    packet = {
                        "id": packet_id,
                        "size": 512,
                        "target": target_device,
                        "type": packet_type
                    }
                    packets_to_send.append(packet)  # Gather packets

            # Send all gathered packets every second
            for packet in packets_to_send:
                self.switch_queue.put(packet)  # Send all gathered packets to the switch

            packets_to_send.clear()  # Clear the list for the next round
            time.sleep(1)  # Wait for 1 second before sending