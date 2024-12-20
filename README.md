![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)

## 📖 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Logging](#logging)
- [License](#license)
- [Contact](#contact)

## 🌟 Overview

**Credit-Based Flow Control Simulation** is a Python-based project that models a network environment where a central switch manages data transmission between four devices. The simulation employs a credit-based mechanism to regulate the flow of packets, preventing buffer overflows and ensuring efficient communication.

## 🎯 Features

- **Credit-Based Flow Control:** Implements a mechanism where each device maintains a credit count, ensuring that the sender does not overwhelm the receiver's buffer.
- **Central Switch:** Manages incoming and outgoing packets, handling buffer allocations and restorations.
- **Multi-Threaded Devices:** Simulates devices that send and process packets concurrently.
- **Comprehensive Logging:** Records simulation events in two separate log files:
  - `simulation.log` for general simulation and switch-related logs.
  - `memory.log` for device-specific logs.

## 🏗️ Architecture

The simulation comprises the following components:

1. **Central Controller (`central.py`):**
   - Initializes and manages the switch and device threads.
   - Sets up two distinct loggers for simulation and device logs.

2. **Switch (`switch.py`):**
   - Listens for incoming packets from devices.
   - Processes packets based on available buffer credits.
   - Restores buffer credits at a defined rate to allow continuous flow.

3. **Devices (`device1.py`, `device2.py`, `device3.py`, `device4.py`):**
   - Each device can send packets to other devices via the switch.
   - Processes incoming packets from the switch, simulating data handling.

## 🛠️ Installation

### **Prerequisites**

- **Python 3.8 or higher**: Ensure you have Python installed. You can download it from [Python.org](https://www.python.org/downloads/).


## 📄 Logging
### Simulation Logs (simulation.log)
Location: Root directory of the project.
Content:
Simulation start and completion messages.
Switch operations, including listening for packets, processing packets, buffer restorations, and shutdown events.
### Memory Logs (memory.log)
Location: Root directory of the project.
Content:
Device activities, including packet transmissions and processing.
Device-specific shutdown messages.
Ensure that both simulation.log and memory.log are present in the root directory after running the simulation.

## 📜 License
This project is licensed under the MIT License.

## 📫 Contact
For any inquiries or feedback, please contact nika_ghaderi@yahoo.com.


### **Clone the Repository**

```bash
git clone https://github.com/yourusername/Credit-Based-Flow-Control-Simulation.git
cd Credit-Based-Flow-Control-Simulation
