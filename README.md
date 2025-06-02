# LUMEA – Portable Vital Sign Monitoring System

**LUMEA** is a portable biomedical monitoring system developed using a Raspberry Pi, PyQt5 interface, and biomedical sensors. It is capable of measuring and displaying real-time ECG, temperature, respiratory rate, and SpO₂ levels, with optional cloud storage integration.

---

## Features

- Real-time ECG signal acquisition and heart rate detection
- Temperature monitoring using digital sensors
- SpO₂ and respiratory rate estimation using photoplethysmography (PPG)
- PyQt5-based graphical user interface
- Automatic arrhythmia detection (tachycardia/bradycardia)
- CSV and image export of critical events
- Integration with Google Cloud Platform (GCP) for cloud backup

---

## File Structure
LUMEA/
├── Algorithms/                  # Modules for processing signals and calculations
│   ├── max30102.py             # (Optional) Handler for MAX30102 sensor (PPG)
│   ├── pleth_curve.py          # Widget to display PPG waveform in the GUI
│   ├── resp_curve.py           # Widget for displaying respiratory signal
│   ├── rpm_calc.py             # Module to compute respiratory rate (RPM)
│   └── spo2_calc.py            # Algorithm to calculate SpO₂ from IR and RED signals
│
├── Config/                     # Configuration and cloud uploader
│   ├── lumea-ecg-eccc724cdcd4.json  # Google Cloud credentials (do not upload publicly)
│   └── uploader.py             # Module to upload CSV/PNG evidence to Google Cloud Platform
│
├── Threads/                    # Real-time signal acquisition threads
│   ├── threadecg.py            # ECG signal thread with Pan-Tompkins or find_peaks detection
│   └── threadpleth.py          # Thread for receiving PPG data
│
├── Tests/                      # Unit or manual test scripts (optional)
│   └── test_peak_detection.py  # (Example) test file for validating peak detection accuracy
│
├── interface.py                # Main PyQt5 interface that runs the full GUI system
├── README.md                   # Project documentation (you are here)
├── requirements.txt            # List of Python packages required to run the system


---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/A01661596/LUMEA.git
   cd LUMEA

---

## Create and activate a virtual environment (optional but recommended):

python3 -m venv venv
source venv/bin/activate

---
## Install the required dependencies:

pip install -r requirements.txt

## Running the system
Execute the following to launch the GUI:
python interface.py
Ensure all connected sensors (ECG, temperature, PPG) are properly wired and detected by the Raspberry Pi.

## Cloud Integration
To enable uploading evidence to Google Cloud Platform:

Place your service account key file inside the config/ folder.

The uploader uses google.cloud.storage to send .csv and .png files to a predefined GCP bucket.

Update the bucket name and key filename in uploader.py.

## Authors
This project was developed as part of a biomedical engineering thesis project by Jennifer Alejandra Contreras, Jimena Vivas, Karen Pérez and Alejandra Rios.

## License
This repository is distributed under an academic, non-commercial use license. For inquiries, please contact the authors.