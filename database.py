import sqlite3

def get_camera_data():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT latitude, longitude, camera_type, speed_limit FROM speed_cameras")
    rows = cursor.fetchall()
    conn.close()
    return rows
