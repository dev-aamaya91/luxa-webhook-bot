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
def send_discord_alert(tx_sig, mint=None, price=None, buyer=None, seller=None, marketplace=None):
    msg = {
        "embeds": [{
            "title": "🧾 New NFT Sale Detected!",
            "description": f"[View Transaction on Solscan](https://solscan.io/tx/{tx_sig})",
            "fields": [
                {"name": "💰 Sale Amount", "value": f"{price:.2f} SOL" if price else "N/A", "inline": True},
                {"name": "🎨 NFT Mint", "value": mint or "N/A", "inline": True},
                {"name": "🧑‍💼 Buyer", "value": buyer or "Unknown", "inline": False},
                {"name": "🧑‍🔧 Seller", "value": seller or "Unknown", "inline": False},
                {"name": "🏪 Marketplace", "value": marketplace or "Unknown", "inline": True}
            ],
            "color": 3066993,
            "footer": {
                "text": f"LuxaBot | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        }]
    }

    try:
        print(f"🚀 Sending Discord alert for: {tx_sig}")
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

        # === Visual Header for Logs ===
        print("\n" + "=" * 60)
        print(f"🛰️  Incoming Transaction — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # === Respond Immediately ===
        response = jsonify({"status": "received"})
        response.status_code = 200

        sig, mint, price, buyer, seller, marketplace = (None, None, None, None, None, None)

        # ✅ Helius-style list payload
        if isinstance(data, list) and len(data) > 0:
            nft_event = data[0].get("events", {}).get("nft", {})
            sig = nft_event.get("signature")
            mint = nft_event.get("nfts", [{}])[0].get("mint")
            price = nft_event.get("amount") / 1e9 if nft_event.get("amount") else None
            buyer = nft_event.get("buyer")
            seller = nft_event.get("seller")
            marketplace = nft_event.get("source")

            print(f"🧪 Extracted Signature from Helius-style list: {sig}")
            print(f"💰 Price: {price} SOL")
            print(f"🎨 Mint: {mint}")
            print(f"🧑‍💼 Buyer: {buyer}")
            print(f"🧑‍🔧 Seller: {seller}")
            print(f"🏪 Marketplace: {marketplace}")

        # 🔁 Fallback for legacy dicts
        elif isinstance(data, dict):
            if "transactions" in data:
                tx_list = data["transactions"]
                print(f"🔍 Found transactions list with {len(tx_list)} entries")
                if isinstance(tx_list, list) and len(tx_list) > 0:
                    sig = tx_list[0].get("signature")
                    print(f"📌 Extracted signature: {sig}")
            elif "transaction" in data and "signature" in data["transaction"]:
                sig = data["transaction"]["signature"]
                print(f"📌 Extracted legacy transaction signature: {sig}")
            else:
                print("❗ No valid transaction signature found in dict payload")

        # === Send Discord Alert ===
        if sig:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 Webhook TX: https://solscan.io/tx/{sig}")
            send_discord_alert(sig, mint, price, buyer, seller, marketplace)
        else:
            print("⚠️ No signature found in payload.")

        return response

    except Exception as e:
        print(f"💥 Error processing webhook: {e}")
        return jsonify({"status": "error"}), 500

# === Entry Point for Local Testing ===
if __name__ == "__main__":
    app.run(port=8080)
