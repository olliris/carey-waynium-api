
# Carey → Waynium API (Webhook Receiver)
This is a lightweight Python/Flask API hosted on your Debian VPS, designed to receive Carey reservations and forward them to Waynium.

---

## ✅ Step-by-step Installation

```bash
# 1. Upload setup.sh to your VPS and run it:
bash setup.sh

# 2. Move into the project directory:
cd /opt/carey-waynium-api

# 3. Activate your virtual environment:
source venv/bin/activate

# 4. Start the Flask server:
python main.py
```

---

## 📂 Virtual Environment (Important)

Every time you reconnect to your VPS (via SSH), remember to **activate your Python environment** before running your server:

```bash
cd /opt/carey-waynium-api
source venv/bin/activate
```

---

## 🧪 Test Carey Webhook (local or remote)

You can test your webhook manually with this payload:

1. Upload `test_carey_payload.json` to your VPS.
2. Then run this command (on your local machine or directly on the VPS):

```bash
curl -X POST http://46.255.164.90:5000/carey/webhook \
  -H "Content-Type: application/json" \
  -d @test_carey_payload.json
```

---

## 🔄 Why Use a `systemd` Service?

Using `systemd` ensures:
- your API runs continuously, even if the server restarts.
- it auto-restarts if it crashes.
- it runs in the background, not tied to your terminal.

You don’t need to restart it regularly. Only restart it if:
- you update the code (`main.py` or environment)
- Flask crashes (rare, but `systemd` will relaunch it)
- you reboot the server

---

## ✅ Next Steps

- Implement the data transformation Carey → Waynium (currently in progress)
- Secure your endpoints with Carey IP whitelisting or signature validation
- Use HTTPS in production (Nginx + certbot)

---


---

## 🛠️ Auto-Start with systemd (Optional but Recommended)

To keep your API running 24/7, even after reboots or crashes:

### 1. Upload `carey_api.service` to your VPS:

```bash
scp carey_api.service root@46.255.164.90:/etc/systemd/system/
```

### 2. Enable and start the service:

```bash
# Reload systemd and enable the service at boot
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable carey_api.service
systemctl start carey_api.service

# Optional: check status or logs
systemctl status carey_api.service
journalctl -u carey_api.service -f
```

Your Flask server is now a background service! 🎉
