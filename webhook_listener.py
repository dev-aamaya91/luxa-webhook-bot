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

# === Discord Alert Function (NFT-specific for now) ===
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

        response = jsonify({"status": "received"})
        response.status_code = 200

        sig = mint = price = buyer = seller = marketplace = None

        # ✅ Helius-style list (preferred)
        if isinstance(data, list) and len(data) > 0:
            sig = data[0].get("signature")

            # If it's an NFT sale, extract sale-specific info
            nft_event = data[0].get("events", {}).get("nft")
            if nft_event:
                mint = nft_event.get("nfts", [{}])[0].get("mint")
                price = nft_event.get("amount", 0) / 1e9
                buyer = nft_event.get("buyer")
                seller = nft_event.get("seller")
                marketplace = nft_event.get("source")

                print(f"🧪 NFT Sale Event Detected")
                print(f"💰 Price: {price} SOL")
                print(f"🎨 Mint: {mint}")
                print(f"🧑‍💼 Buyer: {buyer}")
                print(f"🧑‍🔧 Seller: {seller}")
                print(f"🏪 Marketplace: {marketplace}")
            else:
                print("⚠️ Non-NFT transaction detected — ignoring for now")
        
        # 🔁 Fallback for legacy dict-style
        elif isinstance(data, dict):
            if "transactions" in data:
                tx_list = data["transactions"]
                if isinstance(tx_list, list) and len(tx_list) > 0:
                    sig = tx_list[0].get("signature")
                    print(f"📌 Extracted legacy signature: {sig}")
            elif "transaction" in data and "signature" in data["transaction"]:
                sig = data["transaction"]["signature"]
                print(f"📌 Extracted legacy single signature: {sig}")
            else:
                print("❗ No valid transaction signature in dict payload")

        # === Discord Alert ===
        if sig:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 Webhook TX: https://solscan.io/tx/{sig}")
            if mint:  # NFT logic only for now
                send_discord_alert(sig, mint, price, buyer, seller, marketplace)
            else:
                print("📭 No NFT mint — skipping Discord alert.")
        else:
            print("⚠️ No signature found in payload.")

        return response

    except Exception as e:
        print(f"💥 Error processing webhook: {e}")
        return jsonify({"status": "error"}), 500

# === Entry Point ===
if __name__ == "__main__":
    app.run(port=8080)
