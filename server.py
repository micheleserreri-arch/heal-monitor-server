"""
Health Monitor Server
Riceve dati da Health Auto Export (iPhone) e li serve alla dashboard.
Deploy su Railway.app
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import os

app = Flask(__name__)
CORS(app)  # Permette accesso dalla dashboard su qualsiasi dispositivo

# Storage in memoria (Railway mantiene il processo attivo)
# Per persistenza lunga usa Railway + PostgreSQL add-on
latest_data = {}
history = []
MAX_HISTORY = 200  # ultimi 200 campioni

# ── Ricezione dati da Health Auto Export ──────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Health Auto Export manda qui i dati.
    Formato supportato: JSON con metriche HealthKit.
    """
    global latest_data, history

    try:
        payload = request.get_json(force=True)
        if not payload:
            return jsonify({"error": "No JSON payload"}), 400

        # Health Auto Export manda i dati in vari formati
        # Normalizziamo tutto in un formato standard
        normalized = normalize_health_export(payload)
        normalized["received_at"] = datetime.utcnow().isoformat()

        latest_data = normalized

        # Aggiungi alla history
        history.append(normalized)
        if len(history) > MAX_HISTORY:
            history = history[-MAX_HISTORY:]

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Dati ricevuti: HRV={normalized.get('hrv')} HR={normalized.get('hr')} SpO2={normalized.get('spo2')}")
        return jsonify({"status": "ok", "received": normalized}), 200

    except Exception as e:
        print(f"Errore webhook: {e}")
        return jsonify({"error": str(e)}), 500


def normalize_health_export(payload):
    """
    Health Auto Export può mandare i dati in formati diversi.
    Questa funzione normalizza tutto nel nostro formato.
    """
    data = {}

    # Formato 1: Health Auto Export standard
    # { "data": { "metrics": [ {"name": "heart_rate", "data": [...]} ] } }
    if "data" in payload and "metrics" in payload.get("data", {}):
        metrics = payload["data"]["metrics"]
        for metric in metrics:
            name = metric.get("name", "")
            pts = metric.get("data", [])
            if not pts:
                continue
            latest_val = pts[-1].get("qty") or pts[-1].get("value") or pts[-1].get("Avg")

            if "heart_rate_variability" in name or "hrv" in name.lower():
                data["hrv"] = round(float(latest_val), 1) if latest_val else None
            elif "heart_rate" in name and "variability" not in name:
                data["hr"] = round(float(latest_val)) if latest_val else None
            elif "oxygen_saturation" in name or "spo2" in name.lower():
                data["spo2"] = round(float(latest_val), 1) if latest_val else None
            elif "respiratory_rate" in name:
                data["resp"] = round(float(latest_val), 1) if latest_val else None
            elif "step_count" in name or "steps" in name.lower():
                data["steps"] = int(latest_val) if latest_val else None
            elif "active_energy" in name or "calories" in name.lower():
                data["calories"] = round(float(latest_val)) if latest_val else None
            elif "sleep" in name.lower():
                data["sleep"] = round(float(latest_val), 1) if latest_val else None
            elif "body_temperature" in name:
                data["temp"] = round(float(latest_val), 1) if latest_val else None

    # Formato 2: flat JSON diretto
    # { "hrv": 52, "hr": 68, "spo2": 97.5, ... }
    else:
        field_map = {
            "hrv": ["hrv", "heart_rate_variability", "HRV"],
            "hr": ["hr", "heart_rate", "heartRate", "HR"],
            "spo2": ["spo2", "oxygen_saturation", "SpO2", "oxygenSaturation"],
            "resp": ["resp", "respiratory_rate", "respiratoryRate"],
            "steps": ["steps", "step_count", "stepCount"],
            "calories": ["calories", "active_energy", "activeEnergy"],
            "sleep": ["sleep", "sleep_duration", "sleepDuration"],
            "temp": ["temp", "body_temperature", "bodyTemperature"],
        }
        for key, aliases in field_map.items():
            for alias in aliases:
                if alias in payload:
                    data[key] = payload[alias]
                    break

    # Calcola indici sintetici se abbiamo HRV e HR
    hrv = data.get("hrv")
    hr = data.get("hr")
    steps = data.get("steps", 0)
    calories = data.get("calories", 0)
    sleep = data.get("sleep", 7)

    if hrv and hr:
        stress = max(0, min(100, round(100 - (hrv - 20) / 75 * 100 + (hr - 55) / 55 * 25)))
        data["stress"] = stress
    if steps is not None and calories is not None:
        data["activity"] = min(100, round((steps / 10000) * 60 + (calories / 600) * 40))
    if hrv and sleep:
        stress_val = data.get("stress", 50)
        data["recovery"] = max(0, min(100, round((hrv / 95) * 50 + (sleep / 9) * 30 + (100 - stress_val) / 100 * 20)))

    return data


# ── API per la dashboard ───────────────────────────────────────
@app.route("/api/latest", methods=["GET"])
def get_latest():
    """Restituisce l'ultimo campione ricevuto."""
    if not latest_data:
        return jsonify({"status": "no_data", "message": "Nessun dato ricevuto ancora. Configura Health Auto Export."}), 200
    return jsonify({"status": "ok", "data": latest_data}), 200


@app.route("/api/history", methods=["GET"])
def get_history():
    """Restituisce la storia degli ultimi campioni."""
    n = min(int(request.args.get("n", 40)), MAX_HISTORY)
    return jsonify({"status": "ok", "data": history[-n:], "count": len(history)}), 200


@app.route("/api/status", methods=["GET"])
def get_status():
    """Health check del server."""
    return jsonify({
        "status": "online",
        "samples_stored": len(history),
        "last_received": latest_data.get("received_at", "mai"),
        "server_time": datetime.utcnow().isoformat(),
    }), 200


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "Health Monitor Server",
        "endpoints": {
            "POST /webhook": "Health Auto Export → manda i dati qui",
            "GET /api/latest": "Ultimo campione",
            "GET /api/history": "Storico campioni",
            "GET /api/status": "Stato server",
        }
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🏥 Health Monitor Server avviato su porta {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
