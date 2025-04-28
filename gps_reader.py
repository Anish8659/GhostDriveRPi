from pa1010d import PA1010D
import time

gps = PA1010D()

#gps.send_command("PMTK300,100,0,0,0,0")
#time.sleep(0.2)

def get_gps_data():
    """
    Returns:
      {
        "lat": float,
        "lng": float,
        "speed": float (mph),
        "satellites": int,
        "timestamp": str
      }
    or None if update fails or data is missing.
    """
    try:
        result = gps.update()
        if not result or gps.data.get("latitude") is None or gps.data.get("longitude") is None:
            return None

        lat = float(gps.data.get("latitude", 0.0))
        lng = float(gps.data.get("longitude", 0.0))
        sats = int(gps.data.get("num_sats", 0))
        timestamp = gps.data.get("timestamp", "")
        speed_knots = gps.data.get("speed_over_ground", 0.0) or 0.0

        # Convert speed to mph
        speed_mps = speed_knots * 0.514444
        speed_mph = speed_mps * 2.23694

        return {
            "lat": lat,
            "lng": lng,
            "speed": round(speed_mph, 2),
            "satellites": sats,
            "timestamp": timestamp
        }

    except Exception as e:
        print("GPS parsing error:", e)
        return None
