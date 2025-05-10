from flask import Flask, request, jsonify
from datetime import datetime
import requests
import os

# === Flask App Initialization ===
app = Flask(__name__)
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
if not DISCORD_WEBHOOK_URL:
    print("❗ DISCORD_WEBHOOK_URL is not set. Check your Secrets tab!")

# === Discord Alert Function ===
def send_discord_alert(tx_sig):
    msg = {
        "embeds": [{
            "title": "🔔 New Wallet Transaction",
            "description": f"[View on Solscan](https://solscan.io/tx/{tx_sig})",
            "color": 16711680,
            "footer": {
                "text": f"LuxaBot | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        }]
    }

    try:
        print(f"🚀 Sending Discord alert for: {tx_sig}")
        print(f"🔗 Using Discord Webhook URL: {DISCORD_WEBHOOK_URL}")
        print(f"📦 Payload: {msg}")
        res = requests.post(DISCORD_WEBHOOK_URL, json=msg)
        print(f"✅ Discord Response: {res.status_code}")
        print(f"📩 Response body: {res.text}")
    except Exception as e:
        print(f"❌ Failed to send Discord alert: {e}")

# === Webhook Receiver ===
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        print("📦 Incoming Webhook Payload:")
        print(data)

        response = jsonify({"status": "received"})
        response.status_code = 200

        sig = None
        if isinstance(data, dict) and "transactions" in data:
            tx_list = data["transactions"]
            if isinstance(tx_list, list) and len(tx_list) > 0:
                sig = tx_list[0].get("signature")

        if sig:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 Webhook TX: https://solscan.io/tx/{sig}")
            send_discord_alert(sig)
        else:
            print("⚠️ No signature found in payload.")

        return response

    except Exception as e:
        print(f"💥 Error processing webhook: {e}")
        return jsonify({"status": "error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
