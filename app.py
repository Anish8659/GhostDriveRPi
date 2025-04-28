#!/usr/bin/env python3
import eventlet
eventlet.monkey_patch()

import math
import sqlite3
import threading
import time
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from gps_reader import get_gps_data

app = Flask(__name__, template_folder='templates')
socketio = SocketIO(
    app,
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    cors_allowed_origins='*'
)

def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi/2)**2 +
         math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def find_nearest_camera(lat, lon):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT latitude, longitude, camera_type, speed_limit FROM speed_cameras"
    )
    rows = cursor.fetchall()
    conn.close()

    nearest = None
    min_dist = float('inf')
    for la, lo, cam_type, speed_limit in rows:
        dist = haversine(lat, lon, la, lo)
        if dist < min_dist:
            min_dist = dist
            nearest = {
                "lat":          la,
                "lng":          lo,
                "type":         cam_type,
                "distance_mi":  round(dist, 2),
                "speed_limit":  speed_limit
            }
    return nearest

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_data')
def get_data():
    data = get_gps_data()
    if not data:
        return jsonify({"error": "No GPS data"}), 500

    nearest = find_nearest_camera(data['lat'], data['lng'])
    return jsonify({
        "lat":             data['lat'],
        "lng":             data['lng'],
        "speed":           round(data['speed'], 1),
        "satellites":      data['satellites'],
        "nearest_camera":  nearest,
        "timestamp":       data['timestamp']
    })

@app.route('/get_speed_cameras')
def get_speed_cameras():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT latitude, longitude, camera_type, speed_limit FROM speed_cameras")
    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {"lat": r[0], "lng": r[1], "type": r[2]}
        for r in rows
    ])

def gps_thread():
    while True:
        gps = get_gps_data()
        if gps:
            # serialize timestamp as string
            ts = gps['timestamp'].strftime("%H:%M:%S") if gps['timestamp'] else ""
            payload = {
                "lat":            gps['lat'],
                "lng":            gps['lng'],
                "speed":          round(gps['speed'], 1),
                "satellites":     gps['satellites'],
                "nearest_camera": find_nearest_camera(gps['lat'], gps['lng']),
                "timestamp":      ts
            }
            print("Emitting payload:", payload)
            socketio.emit('update_location', payload)
        time.sleep(1)


if __name__ == '__main__':
    threading.Thread(target=gps_thread, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
