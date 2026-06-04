import os
import requests
import psycopg2
from datetime import datetime

WG_EMAIL = os.getenv("WG_EMAIL")
WG_PASSWORD = os.getenv("WG_PASSWORD")
DB_URL = os.getenv("DB_URL")

LOGIN_URL = "https://app.waterguru.com/api/auth/login"
DATA_URL = "https://app.waterguru.com/api/devices"

def fetch_waterguru_data():
    session = requests.Session()
    login_payload = {"email": WG_EMAIL, "password": WG_PASSWORD}

    login_resp = session.post(LOGIN_URL, json=login_payload)
    login_resp.raise_for_status()

    devices_resp = session.get(DATA_URL)
    devices_resp.raise_for_status()

    devices = devices_resp.json()

    readings = []
    for device in devices:
        if "latest_reading" in device:
            r = device["latest_reading"]
            readings.append({
                "device_id": device["id"],
                "timestamp": r.get("timestamp"),
                "fc": r.get("fc"),
                "ph": r.get("ph"),
                "alk": r.get("alk"),
                "cya": r.get("cya"),
                "temp": r.get("temp"),
            })

    return readings

def write_to_db(readings):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS waterguru_readings (
            id SERIAL PRIMARY KEY,
            device_id TEXT,
            timestamp TIMESTAMPTZ,
            fc FLOAT,
            ph FLOAT,
            alk FLOAT,
            cya FLOAT,
            temp FLOAT
        );
    """)

    for r in readings:
        cur.execute("""
            INSERT INTO waterguru_readings
            (device_id, timestamp, fc, ph, alk, cya, temp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            r["device_id"],
            r["timestamp"],
            r["fc"],
            r["ph"],
            r["alk"],
            r["cya"],
            r["temp"]
        ))

    conn.commit()
    cur.close()
    conn.close()

def main():
    readings = fetch_waterguru_data()
    if readings:
        write_to_db(readings)
        print("WaterGuru data saved.")
    else:
        print("No readings found.")

if __name__ == "__main__":
    main()
