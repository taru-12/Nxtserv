from elasticsearch import Elasticsearch
import pandas as pd
from sklearn.ensemble import IsolationForest

# Connect to Elasticsearch
es = Elasticsearch("http://localhost:9200")

# Fetch logs
res = es.search(index="filebeat-*", size=500)

data = []
for hit in res["hits"]["hits"]:
    src = hit["_source"]
    data.append({
        "bytes": src.get("bytes", 0),
        "status": src.get("http", {}).get("response", {}).get("status_code", 200)
    })

df = pd.DataFrame(data)

# Train AI model
model = IsolationForest(contamination=0.05, random_state=42)
df["anomaly"] = model.fit_predict(df)

# Store anomalies
for _, row in df[df["anomaly"] == -1].iterrows():
    es.index(
        index="siem-anomalies",
        document={
            "bytes": row["bytes"],
            "status": row["status"],
            "result": "anomaly"
        }
    )

print("✅ AI Isolation Model executed successfully")
