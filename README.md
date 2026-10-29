# 🌾 Grain Guardian

### IoT-Based Grain Spoilage Risk Prediction & UV-Assisted Contamination Screening

Grain Guardian is an IoT-based grain storage monitoring project designed to support early identification of conditions associated with grain spoilage. It combines environmental sensing, software-based risk prediction, and an on-demand UV inspection concept within a unified monitoring platform.

The project aims to make grain storage monitoring more accessible by bringing sensor data, risk insights, and storage information together in one dashboard.

> **Project status:** Prototype under development. AI prediction, sensor integration, camera-based inspection, and UV-assisted screening capabilities must be evaluated individually as implementation progresses.

---

## 📌 Table of Contents

* [Overview](#-overview)
* [Problem Statement](#-problem-statement)
* [Proposed Solution](#-proposed-solution)
* [Key Features](#-key-features)
* [System Architecture](#-system-architecture)
* [Hardware Components](#-hardware-components)
* [Technology Stack](#-technology-stack)
* [Project Structure](#-project-structure)
* [How It Works](#-how-it-works)
* [Installation and Setup](#-installation-and-setup)
* [Running the Application](#-running-the-application)
* [API Health Check](#-api-health-check)
* [Current Limitations](#-current-limitations)
* [Future Improvements](#-future-improvements)
* [Contributing](#-contributing)
* [Disclaimer](#-disclaimer)
* [License](#-license)

---

## 🔍 Overview

Grain storage conditions can change over time due to factors such as moisture, temperature, humidity, and inadequate storage practices. These conditions may contribute to grain deterioration and increase the risk of contamination.

Grain Guardian proposes an integrated monitoring system that combines:

* Environmental data collection.
* Grain storage monitoring.
* AI-assisted spoilage-risk prediction.
* Camera-assisted visual inspection.
* An on-demand UV inspection workflow.
* A web-based dashboard for presenting monitoring information.

The objective is to help users observe storage conditions and identify situations that may require further inspection.

## ⚠️ Problem Statement

Traditional grain storage practices may rely heavily on periodic manual inspection. Changes in environmental conditions can go unnoticed between inspections, potentially allowing grain quality to deteriorate.

A practical monitoring system should help users observe relevant environmental parameters, recognize potentially unfavorable storage conditions, and organize inspection results in one place.

Grain Guardian explores how IoT, machine learning, and a web-based monitoring interface could contribute to this process.

---

## 💡 Proposed Solution

Grain Guardian uses a modular architecture consisting of a monitoring interface, a backend API, a database, an AI-related component, and an embedded hardware system.

The proposed workflow is:

1. **Monitor:** Collect environmental readings from connected sensors.
2. **Process:** Transfer available readings to the software system.
3. **Predict:** Estimate spoilage risk using a suitable prediction model.
4. **Inspect:** Allow the user to initiate a separate UV-assisted inspection workflow.
5. **Display:** Present available readings, predictions, and inspection information through the dashboard.

The actual availability and accuracy of each function depend on the corresponding hardware and software integration being completed and tested.

---

## ✨ Key Features

### 1. Environmental Monitoring

Designed to collect and display relevant grain-storage environmental parameters, including temperature, humidity, and moisture-related readings.

### 2. AI-Based Spoilage-Risk Prediction

A planned machine-learning component estimates spoilage risk from suitable input data. Its reliability depends on training data, validation, and integration with the live monitoring system.

### 3. UV-Assisted Inspection Workflow

The proposed system uses separate white-light and UV-light modes to support an on-demand inspection workflow inside a suitable enclosure.

The intended interaction is:

* **Normal mode:** White illumination supports routine camera viewing.
* **Inspection mode:** The system switches to the UV illumination workflow.
* **Result display:** Available inspection information can be presented through the application.

UV illumination alone does not establish the presence or absence of aflatoxin. Any contamination-screening method requires appropriate validation.

### 4. Camera Integration

A webcam or compatible ESP32-CAM module is considered for capturing images during the monitoring and inspection workflow.

Camera availability, image acquisition, and analysis depend on the selected hardware and integration.

### 5. Storage Management Dashboard

The frontend includes pages for storage monitoring, analytics, alerts, AI prediction, and contamination scanning.

### 6. Backend API

A Flask-based backend provides an interface for application operations and uses SQLite for local database storage in the current development setup.

---

## 🏗️ System Architecture

The intended system architecture is:

```text
          GRAIN STORAGE UNIT
                  |
       +----------+----------+
       |                     |
 Environmental Sensors   Camera / Lighting
       |                     |
       +----------+----------+
                  |
          Embedded Controller
                  |
           Hardware Interface
                  |
          Flask Backend API
                  |
          SQLite Database
                  |
        Frontend Web Dashboard
                  |
       +----------+----------+
       |          |          |
   Monitoring  Prediction  Inspection
       |          |          |
       +----------+----------+
                  |
          User-Facing Results
```

**Note:** This diagram represents the intended system design. The complete hardware-to-cloud data flow must be verified against the actual implementation.

---

## 🔧 Hardware Components

The proposed hardware setup includes the following components, subject to the final assembled configuration.

| Component                                      | Intended purpose                  |
| ---------------------------------------------- | --------------------------------- |
| ESP32 / compatible controller                  | Embedded control and connectivity |
| Temperature and humidity sensor                | Environmental monitoring          |
| Grain moisture sensor                          | Moisture-related measurements     |
| Gas sensor, if configured                      | Experimental gas-related readings |
| Webcam or ESP32-CAM                            | Image capture                     |
| White LED                                      | Normal illumination               |
| UV LED                                         | UV-assisted inspection workflow   |
| Two-channel control arrangement / relay module | Switching lighting modes          |
| Grain storage enclosure                        | Containing the grain sample       |

Sensor models, wiring, electrical requirements, and final pin assignments should be documented in the hardware section once the physical setup is finalized.

### Hardware Safety

UV sources can present eye and skin hazards. The final design should use an appropriately selected UV source, suitable shielding, and safe operating procedures. A relay does not by itself make a UV enclosure safe.

---

## 💻 Technology Stack

The current software project includes the following technologies.

| Technology                               | Purpose                                  |
| ---------------------------------------- | ---------------------------------------- |
| Python                                   | Backend and supporting logic             |
| Flask                                    | Backend API                              |
| SQLite                                   | Local database                           |
| HTML                                     | Web page structure                       |
| CSS                                      | Interface styling                        |
| JavaScript                               | Frontend behavior and API communication  |
| OpenCV                                   | Potential image-processing functionality |
| ESP32-compatible development environment | Embedded hardware integration            |

Additional machine-learning libraries and hardware communication tools should be listed here once their actual use in the implemented system has been confirmed.

---

## 📁 Project Structure

```text
grain-guardian-iot/
│
├── ai-model/
│   └──              # AI model code and related resources
│
├── backend/
│   ├── app.py        # Flask application entry point
│   ├── requirements.txt
│   └──              # Database and backend resources
│
├── docs/
│   └──              # Project documentation
│
├── embedded/
│   └──              # Embedded controller code
│
├── frontend/
│   ├── index.html
│   ├── signup.html
│   ├── css/
│   │   └── theme.css
│   ├── js/
│   │   ├── api.js
│   │   ├── layout.js
│   │   └── state.js
│   └── pages/
│       ├── dashboard.html
│       ├── ai-prediction.html
│       ├── alerts.html
│       ├── analytics.html
│       ├── contamination-scan.html
│       └── storage-monitoring.html
│
├── hardware_bridge.py
├── .env.example
└── README.md
```

This is a high-level overview. Additional files may exist in each directory.

---

## ⚙️ Installation and Setup

### Prerequisites

Install the following before running the application:

* Python 3.11 or another supported Python version.
* Git.
* A code editor such as Visual Studio Code.
* A modern web browser.

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/grain-guardian-iot.git
```

Navigate into the project:

```bash
cd grain-guardian-iot
```

Replace `YOUR-USERNAME` with the repository owner's GitHub username.

### 2. Create a Virtual Environment

**Windows PowerShell:**

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```bat
venv\Scripts\activate.bat
```

### 3. Install Backend Dependencies

```bash
python -m pip install -r backend/requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Configure the required values in `.env` according to the backend configuration.

**Never commit `.env`, passwords, API keys, or production secrets to GitHub.**

---

## ▶️ Running the Application

The frontend and backend run separately during local development.

### Terminal 1: Start the Backend

From the repository root:

```powershell
python backend/app.py
```

The Flask development server should start on port `5000` if the application is configured with that port.

### Terminal 2: Start the Frontend

Open a second terminal in the repository root:

```powershell
python -m http.server 8000 --directory frontend
```

Open the frontend in your browser:

```text
http://localhost:8000/
```

The backend should be available locally at:

```text
http://localhost:5000/
```

**Important:** The frontend API configuration must point to the backend's actual address. A local frontend will not automatically connect to a separately hosted backend without the correct API URL and CORS configuration.

---

## 🩺 API Health Check

If the backend exposes the health endpoint, open:

```text
http://localhost:5000/api/health
```

A successful response indicates that the endpoint is reachable.

Other endpoints, request formats, authentication requirements, and response schemas should be documented after they have been verified against the backend implementation.

---

## 🚧 Current Limitations

Grain Guardian is a prototype, and its capabilities should be evaluated against the implemented code and tested hardware.

Important limitations include:

* The physical sensors must be connected and calibrated before their readings can be relied upon.
* The prediction model requires suitable training data and performance evaluation.
* Camera-based analysis must be implemented and validated before it can support meaningful inspection results.
* UV-assisted inspection must use a validated method before it can support claims about contamination.
* The current SQLite database is intended for local development; production deployment requires an appropriate persistent database strategy.
* Cloud deployment does not automatically connect the physical hardware to the hosted application.

No specific prediction accuracy or contamination-detection performance is claimed in this README.

---

## 🚀 Future Improvements

Potential improvements include:

* Complete ESP32-to-backend communication.
* Live sensor updates in the dashboard.
* Sensor calibration and data-quality checks.
* Machine-learning model training and evaluation.
* Historical storage-condition analytics.
* Threshold-based alerts and notifications.
* Validated image-analysis workflows.
* A properly validated contamination-screening method.
* Secure cloud database integration.
* Automated testing and deployment.
* Technical documentation for hardware wiring and calibration.

These are development goals, not claims that every feature is already implemented.

---

## 🤝 Contributing

Contributions, suggestions, and technical feedback are welcome.

To propose a change:

1. Fork the repository.
2. Create a feature branch.
3. Implement and test your changes.
4. Commit your changes with a descriptive message.
5. Open a pull request explaining the change.

For substantial changes, open an issue first to discuss the proposed improvement.

---

## ⚠️ Disclaimer

Grain Guardian is an educational and prototype development project.

Its predictions and inspection outputs must not be treated as certified food-safety assessments. UV illumination or ordinary camera images alone cannot confirm the presence or absence of aflatoxin. Reliable contamination assessment requires an appropriate, validated testing method.

The project is not a substitute for professional grain-quality assessment, laboratory testing, or established food-safety procedures.

---

## 📄 License

A license has not yet been selected for this repository.

Before distributing or permitting reuse of the project, choose a license that reflects the project owner's intentions and add its corresponding license file.
