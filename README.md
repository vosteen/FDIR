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
- To run the fault diagnosis system, execute the `run` script:
    ```bash
    bash src/run.sh
    ```

