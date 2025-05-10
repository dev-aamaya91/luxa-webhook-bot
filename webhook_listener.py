# === Imports ===
from flask import Flask, request, jsonify
from datetime import datetime
import requests
import os
import json

# === Flask App Initialization ===
app = Flask(__name__)
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

if not DISCORD_WEBHOOK_URL:
    print("⚠️ DISCORD_WEBHOOK_URL is not set. Check your environment variables!")

# === Root Health Check Route ===
@app.route("/", methods=["GET"])
def index():
    return "LuxaBot Online!", 200

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
#       print(f"🔗 Using Webhook URL: {DISCORD_WEBHOOK_URL}")  # <- left out for security
        res = requests.post(DISCORD_WEBHOOK_URL, json=msg)
        print(f"✅ Discord Response: {res.status_code}")
        print(f"📝 Response Body: {res.text}")
    except Exception as e:
        print(f"❌ Failed to send Discord alert: {e}")

# === Webhook Receiver ===
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        print("📦 Incoming Webhook Payload:")
        print(json.dumps(data, indent=2))  # Pretty print the payload

        # === Respond Immediately ===
        response = jsonify({"status": "received"})
        response.status_code = 200

        # === Extract Signature ===
        sig = None
        if isinstance(data, dict):
            if "transactions" in data:
                tx_list = data["transactions"]
                print(f"🔍 Found transactions list with {len(tx_list)} entries")
                if isinstance(tx_list, list) and len(tx_list) > 0:
                    sig = tx_list[0].get("signature")
                    print(f"📌 Extracted signature: {sig}")
                else:
                    print("⚠️ 'transactions' key exists but list is empty or invalid")
            elif isinstance(data, list) and len(data) > 0:
                events = data[0].get("events", {})
                if "nft" in events and "signature" in events["nft"]:
                    sig = events["nft"]["signature"]
                    print(f"🧪 Extracted Signature from Helius-style list: {sig}")
            else:
                print("❗ No valid transaction signature found in payload")

        # === Send Discord Alert ===
        if sig:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 Webhook TX: https://solscan.io/tx/{sig}")
            send_discord_alert(sig)
        else:
            print("⚠️ No signature found in payload.")

        return response

    except Exception as e:
        print(f"💥 Error processing webhook: {e}")
        return jsonify({"status": "error"}), 500

# === Entry Point for Local Testing ===
if __name__ == "__main__":
    app.run(port=8080)
