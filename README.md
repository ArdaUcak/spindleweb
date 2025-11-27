# Spindle Web App (Node.js/Express)

A LAN-friendly spindle and spare (yedek) tracking app built with Node.js, Express, EJS templates, and CSV storage on the host machine. Runs in any browser on the same network as the server.

## Setup
1. Install Node.js (v18+ recommended).
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the server (binds to all interfaces so other devices can reach it):
   ```bash
   npm start
   ```
4. In the console you'll see `Local: http://localhost:5000` and the detected LAN URLs. From another device on the same Wi‑Fi/LAN, open the LAN URL, e.g.:
   ```
   http://192.168.1.13:5000/login
   ```
5. Default credentials:
   - Kullanıcı adı: `BAKIM`
   - Şifre: `MAXIME`

If a phone or another PC shows `127.0.0.1 refused to connect`, it means that device is trying to reach itself. Use the host's LAN IP shown when the server starts. Ensure the host firewall allows inbound traffic on the chosen port (default 5000).

### Picking the correct IP (Windows example)
When `ipconfig` lists multiple adapters (VPN, virtual NICs, Ethernet, Wi‑Fi):
- Choose the **IPv4 Address** on the adapter that has the **Default Gateway** your phone/router uses (commonly `192.168.x.x` or `10.x.x.x`).
- Ignore loopback (`127.0.0.1`) and VPN-only subnets (e.g., `26.x.x.x`).
- Example from `ipconfig`:
  - Radmin VPN: `26.203.80.225` (VPN-only, **do not use** for LAN phones)
  - Ethernet: `192.168.1.13` with gateway `192.168.1.1` (matches home Wi‑Fi, **use this** → `http://192.168.1.13:5000/login`)
  - Wi‑Fi (disconnected): no IPv4 shown (not active)

If unsure, connect your phone to the same Wi‑Fi and pick the IPv4 address on the adapter whose gateway matches the router IP on your phone. The server also prints detected LAN URLs at startup.

CSV files `spindle_data.csv` and `yedek_data.csv` are created automatically if missing and stay on the host device.

## Features
- Login-protected access to spindle and spare (yedek) records
- Search by Referans ID
- Add, edit, delete records
- Export combined CSV report (`/export`)
- Bootstrap-styled UI for quick LAN deployment
