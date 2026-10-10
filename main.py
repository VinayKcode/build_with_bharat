import asyncio
import math
import os
from typing import Dict, List, Optional
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Golden Hour - Emergency Response System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-Memory Hospital Database (Kannauj / NH-9 Region)
hospitals_db: Dict[str, dict] = {
    "H101": {
        "id": "H101",
        "name": "District Hospital Kannauj (Rajkiya)",
        "lat": 27.0520,
        "lon": 79.9180,
        "has_trauma": True,
        "icu_beds": 3,
        "blood_units": 12,
        "rating": 4.3,
        "phone": "+91 5694 234101",
        "address": "Makrand Nagar, Kannauj"
    },
    "H102": {
        "id": "H102",
        "name": "Sanjeevani Trauma & Critical Care",
        "lat": 27.0650,
        "lon": 79.9350,
        "has_trauma": True,
        "icu_beds": 5,
        "blood_units": 18,
        "rating": 4.8,
        "phone": "+91 5694 238202",
        "address": "GT Road, Kannauj By-Pass"
    },
    "H103": {
        "id": "H103",
        "name": "City Life Care Clinic",
        "lat": 27.0390,
        "lon": 79.9050,
        "has_trauma": False,
        "icu_beds": 0,
        "blood_units": 2,
        "rating": 3.9,
        "phone": "+91 5694 231303",
        "address": "Saraimeera, Kannauj"
    },
    "H104": {
        "id": "H104",
        "name": "Apex Super Specialty & Neuro Trauma",
        "lat": 27.0800,
        "lon": 79.9500,
        "has_trauma": True,
        "icu_beds": 8,
        "blood_units": 24,
        "rating": 4.6,
        "phone": "+91 5694 245404",
        "address": "NH-9 Expressway Link, Kannauj"
    },
    "H105": {
        "id": "H105",
        "name": "Highway Emergency First-Aid Center",
        "lat": 27.0250,
        "lon": 79.8850,
        "has_trauma": True,
        "icu_beds": 1,
        "blood_units": 4,
        "rating": 4.1,
        "phone": "+91 5694 222505",
        "address": "Tirwa Road Junction, Kannauj"
    }
}

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

class HospitalUpdate(BaseModel):
    icu_beds: Optional[int] = None
    has_trauma: Optional[bool] = None
    blood_units: Optional[int] = None

class CrashPayload(BaseModel):
    lat: float
    lon: float
    confidence: float = 0.92
    speed_before: float = 65.0
    speed_after: float = 0.0
    accel_g: float = 4.8
    emergency_contact: str = "+91 98765 43210"

def haversine_distance_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

async def get_osrm_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float):
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
    try:
        async with httpx.AsyncClient(timeout=3.5) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("routes") and len(data["routes"]) > 0:
                    route = data["routes"][0]
                    duration_mins = round(route["duration"] / 60.0, 1)
                    distance_km = round(route["distance"] / 1000.0, 1)
                    geometry = route["geometry"]
                    return duration_mins, distance_km, geometry
    except Exception as e:
        print(f"OSRM fallback: {e}")

    # Fallback if public OSRM server is slow
    dist = haversine_distance_km(start_lat, start_lon, end_lat, end_lon)
    est_road_km = round(dist * 1.35, 1)
    est_duration_mins = round((est_road_km / 45.0) * 60, 1)
    fallback_geom = {
        "type": "LineString",
        "coordinates": [
            [start_lon, start_lat],
            [(start_lon + end_lon) / 2 + 0.003, (start_lat + end_lat) / 2 - 0.002],
            [end_lon, end_lat]
        ]
    }
    return max(est_duration_mins, 2.0), est_road_km, fallback_geom

@app.get("/api/hospitals")
def get_hospitals():
    return list(hospitals_db.values())

@app.post("/api/hospitals/{hospital_id}")
async def update_hospital(hospital_id: str, update: HospitalUpdate):
    if hospital_id not in hospitals_db:
        return {"error": "Hospital not found"}
    
    h = hospitals_db[hospital_id]
    if update.icu_beds is not None:
        h["icu_beds"] = max(0, update.icu_beds)
    if update.has_trauma is not None:
        h["has_trauma"] = update.has_trauma
    if update.blood_units is not None:
        h["blood_units"] = max(0, update.blood_units)

    await manager.broadcast({
        "type": "HOSPITAL_UPDATED",
        "hospital": h
    })
    return {"status": "success", "hospital": h}

@app.post("/api/emergency/dispatch")
async def dispatch_emergency(payload: CrashPayload):
    crash_lat = payload.lat
    crash_lon = payload.lon

    candidates = []
    rejected = []

    # Filter: Trauma == True and ICU Beds > 0
    for h_id, h in hospitals_db.items():
        if not h["has_trauma"]:
            rejected.append({
                "hospital": h,
                "reason": "REJECTED: No Trauma Care Unit"
            })
            continue
        if h["icu_beds"] <= 0:
            rejected.append({
                "hospital": h,
                "reason": "REJECTED: Zero ICU Beds Available"
            })
            continue

        duration_mins, distance_km, geometry = await get_osrm_route(
            crash_lat, crash_lon, h["lat"], h["lon"]
        )

        # Ranking Score = (0.5 * rating) + (0.3 * beds) - (0.2 * ETA)
        score = round((0.5 * h["rating"]) + (0.3 * h["icu_beds"]) - (0.2 * duration_mins), 3)

        candidates.append({
            "hospital": h,
            "eta_mins": duration_mins,
            "distance_km": distance_km,
            "score": score,
            "geometry": geometry
        })

    if not candidates:
        return {
            "status": "error",
            "message": "No suitable trauma-equipped hospitals with available beds found in radius!",
            "rejected": rejected
        }

    # Best candidate has highest score
    candidates.sort(key=lambda x: x["score"], reverse=True)
    best_candidate = candidates[0]
    best_hospital = best_candidate["hospital"]

    # Temporarily hold 1 bed
    if best_hospital["icu_beds"] > 0:
        best_hospital["icu_beds"] -= 1

    h_lat = best_hospital["lat"]
    h_lon = best_hospital["lon"]
    h_name = best_hospital["name"]
    h_phone = best_hospital["phone"]
    eta = best_candidate["eta_mins"]
    dist = best_candidate["distance_km"]

    google_maps_link = f"https://www.google.com/maps/dir/?api=1&origin={crash_lat},{crash_lon}&destination={h_lat},{h_lon}"
    whatsapp_message = (
        f"🚨 *CRITICAL EMERGENCY ALERT: ROAD CRASH DETECTED*\n\n"
        f"📍 *Location:* Lat {crash_lat:.4f}, Lon {crash_lon:.4f} (NH-9 Corridor)\n"
        f"⚡ *Crash Sensor:* Impact {payload.accel_g}g | Speed drop {payload.speed_before} -> {payload.speed_after} km/h (Confidence {int(payload.confidence * 100)}%)\n\n"
        f"🏥 *Designated Hospital:* *{h_name}*\n"
        f"⏱️ *Road ETA:* ~{eta} mins ({dist} km via OSRM)\n"
        f"🛏️ *Bed Status:* 1 Trauma ICU Bed LOCKED & Pre-Alerted\n"
        f"📞 *Hospital Emergency Contact:* {h_phone}\n\n"
        f"🔗 *Live Navigation & Route:* {google_maps_link}\n"
        f"🟢 *Status:* 108 Ambulance Unit Assigned | Green Corridor Requested"
    )

    dispatch_result = {
        "status": "dispatched",
        "crash_location": {"lat": crash_lat, "lon": crash_lon},
        "selected_hospital": best_hospital,
        "eta_mins": eta,
        "distance_km": dist,
        "score": best_candidate["score"],
        "route_geometry": best_candidate["geometry"],
        "all_ranked_candidates": candidates,
        "rejected_hospitals": rejected,
        "whatsapp_preview": whatsapp_message
    }

    # Broadcast to all connected WebSockets
    await manager.broadcast({
        "type": "EMERGENCY_DISPATCHED",
        "data": dispatch_result
    })

    return dispatch_result

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json({
            "type": "INITIAL_STATE",
            "hospitals": list(hospitals_db.values())
        })
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

@app.get("/")
def get_index():
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
