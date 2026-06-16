from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json, os, csv, io

app = Flask(__name__)
CORS(app)

latest_data = {}
history = []
MAX_HISTORY = 200

def parse_csv_payload(text):
    data = {}
    try:
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            return data
        field_map = {
            "Heart Rate (count/min)": "hr",
            "Heart Rate Variability (ms)": "hrv",
            "Oxygen Saturation (%)": "spo2",
            "Respiratory Rate (count/min)": "resp",
            "Step Count (count)": "steps",
            "Active Energy Burned (kcal)": "calories",
            "Sleep Analysis (hr)": "sleep",
        }
        aggregated = {}
        for row in rows:
            for col, field in field_map.items():
                if col in row and row[col]:
                    try:
                        val = float(row[col])
                        if field not in aggregated:
                            aggregated[field] = []
                        aggregated[field].append(val)
                    except:
                        pass
        for field, vals in aggregated.items():
            if field == "steps":
                data[field] = int(sum(vals))
            elif field in ["hr", "calories"]:
                data[field] = round(sum(vals) / len(vals))
            else:
                data[field] = round(sum(vals) / len(vals), 1)
    except Exception as e:
        print("Errore CSV: " + str(e))
    return data


def parse_json_payload(payload):
    data = {}
    if "data" in payload and "metrics" in payload.get("data", {}):
        metrics = payload["data"]["metrics"]
        for metric in metrics:
            name = metric.get("name", "")
            pts = metric.get("data", [])
            if not pts:
                continue
            latest_val = pts[-1].get("qty") or pts[-1].get("value") or pts[-1].get("Avg")
            if not latest_val:
                continue
            if "heart_rate_variability" in name:
                data["hrv"] = round(float(latest_val), 1)
            elif "heart_rate" in name and "variability" not in name:
                data["hr"] = round(float(latest_val))
            elif "oxygen_saturation" in name:
                data["spo2"] = round(float(latest_val), 1)
            elif "respiratory_rate" in name:
                data["resp"] = round(float(latest_val), 1)
            elif "step_count" in name:
                data["steps"] = int(latest_val)
            elif "active_energy" in name:
                data["calories"] = round(float(latest_val))
            elif "sleep" in name:
                data["sleep"] = round(float(latest_val), 1)
    else:
        for key in ["hrv", "hr", "spo2", "resp", "steps", "calories", "sleep"]:
            if key in payload:
                data[key] = payload[key]
    return data


def compute_indices(data):
    hrv = data.get("hrv")
    hr = data.get("hr")
    steps = data.get("steps", 0) or 0
    calories = data.get("calories", 0) or 0
    sleep = data.get("sleep", 7) or 7
    if hrv and hr:
        stress = max(0, min(100, round(100 - (hrv - 20) / 75 * 100 + (hr - 55) / 55 * 25)))
        data["stress"] = stress
        data["recovery"] = max(0, min(100, round((hrv / 95) * 50 + (sleep / 9) * 30 + (100 - stress) / 100 * 20)))
    data["activity"] = min(100, round((steps / 10000) * 60 + (calories / 600) * 40))
    return data


@app.route("/webhook", methods=["POST"])
def webhook():
    global latest_data, history
    try:
        content_type = request.content_type or ""
        raw = request.get_data(as_text=True)
        print("Ricevuto: " + raw[:200])
        if "json" in content_type or raw.strip().startswith("{"):
            try:
                payload = json.loads(raw)
                data = parse_json_payload(payload)
            except:
                data = parse_csv_payload(raw)
        else:
            data = parse_csv_payload(raw)
        if not data:
            return jsonify({"status": "ok", "message": "nessun dato"}), 200
        data = compute_indices(data)
        data["received_at"] = datetime.utcnow().isoformat()
        latest_data = data
        history.append(data)
        if len(history) > MAX_HISTORY:
            history = history[-MAX_HISTORY:]
        print("Salvato: " + str(data))
        return jsonify({"status": "ok", "received": data}), 200
    except Exception as e:
        print("Errore: " + str(e))
        return jsonify({"status": "ok", "error": str(e)}), 200


@app.route("/api/latest", methods=["GET"])
def get_latest():
    if not latest_data:
        return jsonify({"status": "no_data"}), 200
    return jsonify({"status": "ok", "data": latest_data}), 200


@app.route("/api/history", methods=["GET"])
def get_history():
    n = min(int(request.args.get("n", 40)), MAX_HISTORY)
    return jsonify({"status": "ok", "data": history[-n:], "count": len(history)}), 200


@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify({
        "status": "online",
        "samples_stored": len(history),
        "last_received": latest_data.get("received_at", "mai"),
        "server_time": datetime.utcnow().isoformat()
    }), 200


@app.route("/", methods=["GET"])
def index():
    return jsonify({"service": "Health Monitor Server v2", "status": "online"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
        }

        # Aggrega per campo — prende la media degli ultimi valori
        aggregated = {}
        for row in rows:
            for col, field in field_map.items():
                if col in row and row[col]:
                    try:
                        val = float(row[col])
                        if field not in aggregated:
                            aggregated[field] = []
                        aggregated[field].append(val)
                    except:
                        pass

        for field, vals in aggregated.items():
            if field == "steps":
                data[field] = int(sum(vals))
            elif field in ["hr", "calories"]:
                data[field] = round(sum(vals) / len(vals))
            else:
                data[field] = round(sum(vals) / len(vals), 1)

    except Exception as e:
        print(f"Errore parsing CSV: {e}")
    return data


def parse_json_payload(payload):
    """Parsa JSON da Health Auto Export"""
    data = {}
    if "data" in payload and "metrics" in payload.get("data", {}):
        metrics = payload["data"]["metrics"]
        for metric in metrics:
            name = metric.get("name", "")
            pts = metric.get("data", [])
            if not pts:
                continue
            latest_val = pts[-1].get("qty") or pts[-1].get("value") or pts[-1].get("Avg")
            if not latest_val:
                continue
            if "heart_rate_variability" in name: data["hrv"] = round(float(latest_val), 1)
            elif "heart_rate" in name and "variability" not in name: data["hr"] = round(float(latest_val))
            elif "oxygen_saturation" in name: data["spo2"] = round(float(latest_val), 1)
            elif "respiratory_rate" in name: data["resp"] = round(float(latest_val), 1)
            elif "step_count" in name: data["steps"] = int(latest_val)
            elif "active_energy" in name: data["calories"] = round(float(latest_val))
            elif "sleep" in name: data["sleep"] = round(float(latest_val), 1)
    else:
        for key in ["hrv","hr","spo2","resp","steps","calories","sleep"]:
            if key in payload:
                data[key] = payload[key]
    return data


def compute_indices(data):
    hrv = data.get("hrv")
    hr = data.get("hr")
    steps = data.get("steps", 0) or 0
    calories = data.get("calories", 0) or 0
    sleep = data.get("sleep", 7) or 7

    if hrv and hr:
        stress = max(0, min(100, round(100 - (hrv - 20) / 75 * 100 + (hr - 55) / 55 * 25)))
        data["stress"] = stress
        data["recovery"] = max(0, min(100, round((hrv/95)*50 + (sleep/9)*30 + (100-stress)/100*20)))
    data["activity"] = min(100, round((steps/10000)*60 + (calories/600)*40))
    return data


@app.route("/webhook", methods=["POST"])
def webhook():
    global latest_data, history
    try:
        content_type = request.content_type or ""
        raw = request.get_data(as_text=True)
        
        # Prova JSON prima
        if "json" in content_type or raw.strip().startswith("{"):
            try:
                payload = json.loads(raw)
                data = parse_json_payload(payload)
            except:
                data = parse_csv_payload(raw)
        else:
            # CSV
            data = parse_csv_payload(raw)

        if not data:
            return jsonify({"status": "ok", "message": "Nessun dato riconosciuto"}), 200

        data = compute_indices(data)
        data["received_at"] = datetime.utcnow().isoformat()
        latest_data = data
        history.append(data)
        if len(history) > MAX_HISTORY:
            history = history[-MAX_HISTORY:]

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Dati: {data}")
        return jsonify({"status": "ok", "received": data}), 200

    except Exception as e:
        print(f"Errore: {e}")
        return jsonify({"status": "ok", "message": str(e)}), 200  # 200 per non far riprovare l'app


@app.route("/api/latest", methods=["GET"])
def get_latest():
    if not latest_data:
        return jsonify({"status": "no_data"}), 200
    return jsonify({"status": "ok", "data": latest_data}), 200


@app.route("/api/history", methods=["GET"])
def get_history():
    n = min(int(request.args.get("n", 40)), MAX_HISTORY)
    return jsonify({"status": "ok", "data": history[-n:], "count": len(history)}), 200


@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify({"status": "online", "samples_stored": len(history), "last_received": latest_data.get("received_at", "mai"), "server_time": datetime.utcnow().isoformat()}), 200


@app.route("/", methods=["GET"])
def index():
    return jsonify({"service": "Health Monitor Server v2", "status": "online"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
        }

        # Aggrega per campo — prende la media degli ultimi valori
        aggregated = {}
        for row in rows:
            for col, field in field_map.items():
                if col in row and row[col]:
                    try:
                        val = float(row[col])
                        if field not in aggregated:
                            aggregated[field] = []
                        aggregated[field].append(val)
                    except:
                        pass

        for field, vals in aggregated.items():
            if field == "steps":
                data[field] = int(sum(vals))
            elif field in ["hr", "calories"]:
                data[field] = round(sum(vals) / len(vals))
            else:
                data[field] = round(sum(vals) / len(vals), 1)

    except Exception as e:
        print(f"Errore parsing CSV: {e}")
    return data


def parse_json_payload(payload):
    """Parsa JSON da Health Auto Export"""
    data = {}
    if "data" in payload and "metrics" in payload.get("data", {}):
        metrics = payload["data"]["metrics"]
        for metric in metrics:
            name = metric.get("name", "")
            pts = metric.get("data", [])
            if not pts:
                continue
            latest_val = pts[-1].get("qty") or pts[-1].get("value") or pts[-1].get("Avg")
            if not latest_val:
                continue
            if "heart_rate_variability" in name: data["hrv"] = round(float(latest_val), 1)
            elif "heart_rate" in name and "variability" not in name: data["hr"] = round(float(latest_val))
            elif "oxygen_saturation" in name: data["spo2"] = round(float(latest_val), 1)
            elif "respiratory_rate" in name: data["resp"] = round(float(latest_val), 1)
            elif "step_count" in name: data["steps"] = int(latest_val)
            elif "active_energy" in name: data["calories"] = round(float(latest_val))
            elif "sleep" in name: data["sleep"] = round(float(latest_val), 1)
    else:
        for key in ["hrv","hr","spo2","resp","steps","calories","sleep"]:
            if key in payload:
                data[key] = payload[key]
    return data


def compute_indices(data):
    hrv = data.get("hrv")
    hr = data.get("hr")
    steps = data.get("steps", 0) or 0
    calories = data.get("calories", 0) or 0
    sleep = data.get("sleep", 7) or 7

    if hrv and hr:
        stress = max(0, min(100, round(100 - (hrv - 20) / 75 * 100 + (hr - 55) / 55 * 25)))
        data["stress"] = stress
        data["recovery"] = max(0, min(100, round((hrv/95)*50 + (sleep/9)*30 + (100-stress)/100*20)))
    data["activity"] = min(100, round((steps/10000)*60 + (calories/600)*40))
    return data


@app.route("/webhook", methods=["POST"])
def webhook():
    global latest_data, history
    try:
        content_type = request.content_type or ""
        raw = request.get_data(as_text=True)
        
        # Prova JSON prima
        if "json" in content_type or raw.strip().startswith("{"):
            try:
                payload = json.loads(raw)
                data = parse_json_payload(payload)
            except:
                data = parse_csv_payload(raw)
        else:
            # CSV
            data = parse_csv_payload(raw)

        if not data:
            return jsonify({"status": "ok", "message": "Nessun dato riconosciuto"}), 200

        data = compute_indices(data)
        data["received_at"] = datetime.utcnow().isoformat()
        latest_data = data
        history.append(data)
        if len(history) > MAX_HISTORY:
            history = history[-MAX_HISTORY:]

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Dati: {data}")
        return jsonify({"status": "ok", "received": data}), 200

    except Exception as e:
        print(f"Errore: {e}")
        return jsonify({"status": "ok", "message": str(e)}), 200  # 200 per non far riprovare l'app


@app.route("/api/latest", methods=["GET"])
def get_latest():
    if not latest_data:
        return jsonify({"status": "no_data"}), 200
    return jsonify({"status": "ok", "data": latest_data}), 200


@app.route("/api/history", methods=["GET"])
def get_history():
    n = min(int(request.args.get("n", 40)), MAX_HISTORY)
    return jsonify({"status": "ok", "data": history[-n:], "count": len(history)}), 200


@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify({"status": "online", "samples_stored": len(history), "last_received": latest_data.get("received_at", "mai"), "server_time": datetime.utcnow().isoformat()}), 200


@app.route("/", methods=["GET"])
def index():
    return jsonify({"service": "Health Monitor Server v2", "status": "online"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
