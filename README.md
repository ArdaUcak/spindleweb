# Spindle Web App

A Flask-based LAN web version of the spindle and spare tracking tool. Data is stored in CSV files on the host machine and accessed through a browser.

## Running locally or on LAN
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server (binds to all interfaces so other devices can reach it):
   ```bash
   python app.py
   ```
3. Find the host machine's LAN IP (e.g., `192.168.1.34`) and open the app from any browser:
   ```
   http://<LAN_IP>:5000/login
   ```
4. Default credentials:
   - Kullanıcı adı: `BAKIM`
   - Şifre: `MAXIME`

CSV files `spindle_data.csv` and `yedek_data.csv` are created automatically if missing and stay on the host device.

## Features
- Login-protected access to spindle and spare (yedek) records
- Search by Referans ID
- Add, edit, delete records
- Export combined CSV report (`/export`)
- Bootstrap-styled UI for quick LAN deployment
