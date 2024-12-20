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
        self.switch_queue = switch_queue
        self.running = True
        self.outgoing_packets = TRANSMISSION_RATES[device_id]
        self.received_packets = queue.Queue()
        self.logger = logger
        self.ratio_counter = 0
        self.RATIO = RATIO
        self.DURATION = DURATION

    def process_incoming(self):
        start_time = time.time()
        while self.running and time.time() - start_time < self.DURATION:
            time.sleep(1)  # Process packets every second
            processed_packets = []
            for _ in range(PROCESS_RATE):
                if not self.received_packets.empty():
                    packet = self.received_packets.get()
                    if packet['id'] == "BACKPRESSURE":
                        target_device = packet['target']
                        original_rate = self.outgoing_packets[target_device]
                        self.outgoing_packets[target_device] = max(1, original_rate // 2)
                        if original_rate != 1:
                            self.logger.warning(
                                f"Device {self.device_id}: Received backpressure signal. Slowing down transmission to "
                                f"Device {target_device} to {self.outgoing_packets[target_device]}."
                            )
                        continue
                    processed_packets.append(packet)

            if processed_packets:
                packet_ids = [p['id'] for p in processed_packets]
                self.logger.info(f"Device {self.device_id}: Processed packets: {packet_ids}.")

    def send_packets(self):
        start_time = time.time()
        while self.running and time.time() - start_time < self.DURATION:
            for target_device, rate in self.outgoing_packets.items():
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
                    self.switch_queue.put(packet)
                    # self.logger.info(
                    #     f"Device {self.device_id}: Sent packet {packet_id} ({packet_type}) to Device {target_device}."
                    # )
                time.sleep(1 / sum(self.outgoing_packets.values()))

    def stop(self):
        self.logger.info(f"Device {self.device_id}: Stopping packet transmission.")
        self.running = False