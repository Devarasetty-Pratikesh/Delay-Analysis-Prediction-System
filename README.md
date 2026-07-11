# RINL Delay Analysis & Prediction System

A centralized dashboard and prediction system for capturing, analyzing, and predicting delays of critical equipment across major departments of the **Vizag Steel Plant (RINL)**.

---

## Features

- **Centralized Delay Capturing**: Log and track delays for critical equipment.
- **Interactive Reports**: View tabular and graphical metrics of shop-wise, equipment-wise, and agency-wise delays.
- **Monsoon Delay Analysis**: View seasonal and monsoon-specific conveyor delays.
- **Predictive Failure Analysis**: Forecast potential equipment failures and delay duration metrics.

---

## Setup & Running the Application

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.10+ (if running locally without Docker)

### 2. Configure Environment Variables
Copy `.env.example` to a new file named `.env`:
```bash
cp .env.example .env
```
Open `.env` and configure your database credentials:
```env
MYSQL_ROOT_PASSWORD=your_password_here
MYSQL_DATABASE=rinl_delays
```
*(Note: The `.env` file is ignored by Git to keep credentials secure.)*

### 3. Run with Docker Compose
Start the database and Streamlit dashboard containers:
```bash
docker-compose up --build
```
The dashboard will be accessible locally at: **`http://localhost:8501`**

### 4. Database Ingestion (First Time Setup)
To clean the raw datasets and load them into the MySQL database container, run:
```bash
python clean_data.py
python init_db.py
```

---

## Project Specifications

### Data Structures & Tables
1. **User Table**: `emp_no`, `password`, `empname`, `dept`, `designation`, `role`, `active`
2. **Equipment Master Table**: `shop_code`, `shop_desc`, `eqpt_code`, `sub_eqpt_code`
3. **Delays Data**: `shop_code`, `shop_desc`, `eqpt_name`, `sub_eqpt_name`, `agency`, `delay_from`, `delay_upto`, `delay_duration`, `delay_desc`, `user_entered`, `timestamp`

### Dashboard Pages
- **Page 1: Login**
- **Page 2: Delays Entry**: Shop description (combo box), equipment name, sub-equipment name, agency (Operations, Mechanical, Electrical, Shutdown), start/end date time picker, effective duration, and remarks.
- **Page 3: User Management**: Admin controls for user status, roles (`sys_admin`, `dept_user`, `dept_admin`, `ppm_user`, `ppm_admin`).
- **Page 4: Delay Reports & Analytics**: Tabular and graphical displays filtered by shop description, from date, and to date. Includes:
  - Shop-wise, equipment-wise, and agency-wise delays.
  - Duration-wise and conveyor-wise delays.
  - Predictive analysis of likely equipment failure.
  - Monsoon period seasonal analysis.
