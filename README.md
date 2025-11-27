# Spindle Tracking Web App (Flask)

A simple Flask web UI for tracking spindle and yedek records using CSV files. Runs on one PC and is reachable from any browser on the same LAN.

## Features
- Login with fixed credentials (`BAKIM` / `MAXIME`).
- Spindle and yedek lists with search by "Referans ID".
- Add / edit / delete records.
- CSV export combining spindle and yedek data.

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Ensure the `templates/` folder sits beside `app.py`.
3. Start the server:
   ```bash
   python app.py
   ```
4. From the same PC: http://localhost:5000/login
5. From another device on the same network: http://<YOUR_LAN_IP>:5000/login (e.g., http://192.168.1.13:5000/login).

## Data storage
- CSV files (`spindle_data.csv`, `yedek_data.csv`) are created automatically next to `app.py` if missing.
- Exported CSV is written to `takip_export.csv`.
