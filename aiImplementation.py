import time
import json
import pandas as pd
from datetime import datetime
from elasticsearch import Elasticsearch
from sklearn.ensemble import IsolationForest

# ===================== CONFIG =====================
ES_URL = "http://localhost:9200"

SOURCE_INDEX = "mysql-logs-*"
AI_INDEX = "mysql-logs-ai"
SOAR_INDEX = "mysql-soar-alerts"

STATE_FILE = "last_processed_time.txt"
SLEEP_TIME = 60   # seconds

# ===================== CONNECT =====================
es = Elasticsearch(ES_URL)

# ===================== STATE HANDLING =====================
def get_last_processed_time():
    try:
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    except:
        return "now-15m"   # first run fallback

def save_last_processed_time(ts):
    with open(STATE_FILE, "w") as f:
        f.write(ts)

# ===================== AI ENGINE =====================
def run_ai_engine():
    print("🤖 AI Engine: scanning new MySQL logs...")

    last_time = get_last_processed_time()

    query = {
        "size": 2000,
        "sort": [{"@timestamp": "asc"}],
        "query": {
            "range": {
                "@timestamp": {
                    "gt": last_time
                }
            }
        }
    }

    res = es.search(index=SOURCE_INDEX, body=query)
    hits = res["hits"]["hits"]

    if not hits:
        print("ℹ️ No new logs found")
        return

    records = []

    for hit in hits:
        src = hit["_source"]
        msg = src.get("message", "")

        try:
            log_json = json.loads(msg)
        except:
            log_json = {}

        query_time = float(log_json.get("query_time", 0))
        rows_examined = int(log_json.get("rows_examined", len(msg)))

        records.append({
            "@timestamp": src["@timestamp"],
            "message": msg,
            "query_time": query_time,
            "rows_examined": rows_examined
        })

    df = pd.DataFrame(records)

    # ---------- AI MODEL ----------
    model = IsolationForest(
        n_estimators=120,
        contamination=0.03,
        random_state=42
    )

    features = df[["query_time", "rows_examined"]]
    df["anomaly"] = model.fit_predict(features)
    df["anomaly_score"] = model.decision_function(features)

    def severity(score):
        if score < -0.15:
            return "CRITICAL"
        elif score < -0.08:
            return "HIGH"
        elif score < -0.03:
            return "MEDIUM"
        else:
            return "LOW"

    df["severity"] = df["anomaly_score"].apply(severity)

    # ---------- STORE AI RESULTS ----------
    for _, row in df.iterrows():
        es.index(
            index=AI_INDEX,
            document={
                "@timestamp": row["@timestamp"],
                "message": row["message"],
                "query_time": row["query_time"],
                "rows_examined": row["rows_examined"],
                "anomaly": row["anomaly"],
                "anomaly_score": row["anomaly_score"],
                "severity": row["severity"],
                "engine": "IsolationForest"
            }
        )

    save_last_processed_time(df["@timestamp"].iloc[-1])
    print(f"✅ AI Engine processed {len(df)} new logs")

# ===================== SOAR ENGINE =====================
def run_soar_engine():
    print("🚨 SOAR Engine: checking CRITICAL anomalies...")

    query = {
        "size": 10,
        "sort": [{"@timestamp": "desc"}],
        "query": {
            "term": {
                "severity.keyword": "CRITICAL"
            }
        }
    }

    res = es.search(index=AI_INDEX, body=query)
    hits = res["hits"]["hits"]

    if not hits:
        print("ℹ️ No CRITICAL alerts")
        return

    for hit in hits:
        src = hit["_source"]

        alert_doc = {
            "@timestamp": src["@timestamp"],
            "alert_type": "MYSQL_AI_ANOMALY",
            "severity": src["severity"],
            "message": src["message"],
            "anomaly_score": src["anomaly_score"],
            "source": "SOAR",
            "status": "OPEN"
        }

        es.index(
            index=SOAR_INDEX,
            document=alert_doc
        )

        print("🚨 SOAR ALERT SENT → Grafana")

# ===================== MAIN LOOP =====================
if _name_ == "_main_":
    print("🔥 MySQL AI + SOAR system started (continuous mode)")

    while True:
        try:
            run_ai_engine()
            run_soar_engine()
            print(f"⏳ Sleeping {SLEEP_TIME} seconds...\n")
            time.sleep(SLEEP_TIME)

        except Exception as e:
            print("❌ ERROR:", e)
            time.sleep(30)
