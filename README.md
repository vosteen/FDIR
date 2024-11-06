# Fault Detection Identification and Recovery

This project implements a fault diagnosis system for a set of components including multipliers, adders, temperature sensors, heaters, and simulation units. The system uses the `python-sat` library to perform SAT-based diagnosis to identify faulty components.

## Features
- Monitors a system of multipliers and adders, and a digital twin for building temperature control.
- Uses a SAT solver to diagnose faulty components.
- Identifies minimal diagnoses for the system.

## Installation
### Prerequisites
- Python 3.6 or higher

### Install dependencies
1. Clone the repository:
    ```bash
    git clone https://gitlab.isp.uni-luebeck.de/digitaltwin/fdir.git fault-diagnosis-system
    cd fault-diagnosis-system
    ```

2. Create a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages using `pip`:
    ```bash
    pip install -r requirements.txt
    ```

### Usage
- To run the fault diagnosis system for multipliers and adders, execute the `bauer_leucker_schallhart` script:
    ```bash
    python src/bauer_leucker_schallhart.py
    ```
- To run the fault diagnosis system for the digital twin temperature control, execute the `dt_fdir` script:
    ```bash
    python src/dt_fdir.py
    ```

### Example
The `bauer_leucker_schallhart.py` script initializes a set of components (multipliers and adders), defines expected functions for the monitors, and performs the diagnosis process to identify faulty components. The script outputs the minimal diagnoses for the system.

The `dt_fdir.py` script implements a fault diagnosis system for a digital twin of building temperature control, monitoring temperature sensors and heater control signals. It performs the diagnosis process to identify faulty components and outputs the minimal diagnoses.


### Project Structure
```
fault-diagnosis-system/
│
├── src/
│ ├── bauer_leucker_schallhart.py # Script reimplementing the fault diagnosis from the Bauer et al. paper
│ └── dt_fdir.py # Script for the digital twin fault diagnosis implementation
│
├── requirements.txt # List of required Python packages
└── README.md # Project README
```