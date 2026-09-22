"""
RPSIT Real Road Data Fetcher
Uses FREE public APIs (no API key needed, zero cost):
  - OSRM Demo Server: Real road routing, distances, durations, waypoints
  - OpenStreetMap Nominatim: Geocoding / address validation

This script is run ONCE at setup. Results are cached in route_waypoints table.
OSRM public server is used sparingly (one request per stop-pair, not on every ping).
"""
import os
import sys
import time
import json
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, Base, engine
from app.models.route import Route, Stop
from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

OSRM_BASE = "http://router.project-osrm.org/route/v1/driving"
NOMINATIM_BASE = "https://nominatim.openstreetmap.org/reverse"

# We store real road data in a new table
class RouteSegment(Base):
    """Stores real road distance + duration + waypoints for each stop pair."""
    __tablename__ = "route_segments"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, index=True)
    from_stop_id = Column(Integer, ForeignKey("stops.id", ondelete="CASCADE"), nullable=False)
    to_stop_id = Column(Integer, ForeignKey("stops.id", ondelete="CASCADE"), nullable=False)
    road_distance_km = Column(Float, nullable=False)   # Real road distance
    road_duration_min = Column(Float, nullable=False)  # OSRM estimated drive time
    waypoints_json = Column(Text, nullable=True)       # JSON array of [lon, lat] road waypoints
    osrm_source = Column(String(50), default="osrm_demo")


def fetch_osrm_route(lat1, lon1, lat2, lon2):
    """
    Query OSRM public demo server for real road routing.
    Returns: {distance_km, duration_min, waypoints: [[lon, lat], ...]}
    """
    url = f"{OSRM_BASE}/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    try:
        resp = httpx.get(url, timeout=15.0, headers={"User-Agent": "RPSIT-BusPrediction/1.0 (academic-project)"})
        data = resp.json()
        if data.get("code") != "Ok" or not data.get("routes"):
            return None
        
        route = data["routes"][0]
        distance_km = round(route["distance"] / 1000.0, 3)
        duration_min = round(route["duration"] / 60.0, 2)
        
        # Road waypoints from GeoJSON LineString (coordinates are [lon, lat])
        waypoints = route["geometry"]["coordinates"]
        
        return {
            "distance_km": distance_km,
            "duration_min": duration_min,
            "waypoints": waypoints
        }
    except Exception as e:
        print(f"    OSRM error: {e}")
        return None


def validate_stop_with_nominatim(lat, lon, stop_name):
    """
    Confirm a stop coordinate resolves to a real place using Nominatim reverse geocoding.
    """
    try:
        resp = httpx.get(
            NOMINATIM_BASE,
            params={"lat": lat, "lon": lon, "format": "json"},
            timeout=10.0,
            headers={"User-Agent": "RPSIT-BusPrediction/1.0 (academic-project)"}
        )
        data = resp.json()
        address = data.get("display_name", "Unknown")
        return address
    except Exception:
        return "Nominatim lookup failed"


def fetch_and_store_real_road_data():
    """
    Fetches real road data for all RPSIT routes from OSRM and stores in DB.
    Rate-limited: 1 second delay between requests to respect public API usage policy.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        routes = db.query(Route).filter(Route.is_active == True).order_by(Route.id).all()
        
        total_segments = 0
        total_distance = 0.0
        route_summaries = []

        for route in routes:
            stops = sorted(route.stops, key=lambda s: s.sequence)
            if len(stops) < 2:
                continue

            print(f"\n=== {route.route_code}: {route.route_name} ===")
            
            route_road_distance = 0.0
            route_road_duration = 0.0

            for i in range(len(stops) - 1):
                stop_a = stops[i]
                stop_b = stops[i + 1]

                # Check if already fetched
                existing = db.query(RouteSegment).filter(
                    RouteSegment.from_stop_id == stop_a.id,
                    RouteSegment.to_stop_id == stop_b.id
                ).first()

                if existing:
                    print(f"  [CACHED] {stop_a.stop_name} -> {stop_b.stop_name}: {existing.road_distance_km} km | {existing.road_duration_min} min")
                    route_road_distance += existing.road_distance_km
                    route_road_duration += existing.road_duration_min
                    total_segments += 1
                    continue

                print(f"  Fetching OSRM: {stop_a.stop_name} -> {stop_b.stop_name} ...", end=" ", flush=True)
                
                result = fetch_osrm_route(stop_a.latitude, stop_a.longitude, stop_b.latitude, stop_b.longitude)
                
                if result:
                    segment = RouteSegment(
                        route_id=route.id,
                        from_stop_id=stop_a.id,
                        to_stop_id=stop_b.id,
                        road_distance_km=result["distance_km"],
                        road_duration_min=result["duration_min"],
                        waypoints_json=json.dumps(result["waypoints"]),
                        osrm_source="osrm_demo"
                    )
                    db.add(segment)
                    db.commit()
                    route_road_distance += result["distance_km"]
                    route_road_duration += result["duration_min"]
                    total_segments += 1
                    print(f"{result['distance_km']} km | {result['duration_min']} min | {len(result['waypoints'])} road waypoints")
                else:
                    print("FAILED (using straight-line fallback)")

                # Respectful rate limiting - 1.5 seconds between OSRM requests
                time.sleep(1.5)

            route_summaries.append({
                "code": route.route_code,
                "name": route.route_name,
                "total_road_km": round(route_road_distance, 2),
                "total_duration_min": round(route_road_duration, 1)
            })
            print(f"  Total road distance: {route_road_distance:.2f} km | Est. travel time: {route_road_duration:.1f} min")

        print("\n" + "=" * 60)
        print("RPSIT REAL ROAD DATA SUMMARY (via OSRM + OpenStreetMap)")
        print("=" * 60)
        for r in route_summaries:
            print(f"  {r['code']}: {r['total_road_km']} km | {r['total_duration_min']} min est. travel")
        print(f"\nTotal road segments fetched: {total_segments}")
        print("Real road data stored in route_segments table.")

        # Also validate a few key stops with Nominatim
        print("\n--- Validating Key Stop Coordinates with Nominatim ---")
        key_stops = [
            (11.7210, 78.0350, "RPSIT College Main Gate"),
            (11.6643, 78.1460, "Salem New Bus Stand"),
            (11.7996, 77.7996, "Mettur Dam"),
            (12.1272, 78.1572, "Dharmapuri Bus Stand"),
            (11.5983, 78.5997, "Attur Bus Stand"),
        ]
        for lat, lon, name in key_stops:
            time.sleep(1.0)
            address = validate_stop_with_nominatim(lat, lon, name)
            # Trim for readability
            short_addr = address[:80] + "..." if len(address) > 80 else address
            print(f"  {name}: {short_addr}")

    finally:
        db.close()


def get_route_waypoints_for_trip(route_id: int) -> list:
    """
    Returns ordered list of real road GPS waypoints for a full route.
    Used by the trip simulator to make buses follow actual roads.
    """
    db = SessionLocal()
    try:
        route = db.query(Route).filter(Route.id == route_id).first()
        if not route:
            return []

        stops = sorted(route.stops, key=lambda s: s.sequence)
        all_waypoints = []

        for i in range(len(stops) - 1):
            segment = db.query(RouteSegment).filter(
                RouteSegment.from_stop_id == stops[i].id,
                RouteSegment.to_stop_id == stops[i + 1].id
            ).first()

            if segment and segment.waypoints_json:
                points = json.loads(segment.waypoints_json)
                # OSRM returns [lon, lat], we convert to {lat, lon}
                for pt in points:
                    all_waypoints.append({"lat": pt[1], "lon": pt[0]})
            else:
                # Fallback: use stop coordinates directly
                all_waypoints.append({"lat": stops[i].latitude, "lon": stops[i].longitude})

        # Add final stop
        if stops:
            all_waypoints.append({"lat": stops[-1].latitude, "lon": stops[-1].longitude})

        return all_waypoints
    finally:
        db.close()


def get_real_road_distance(from_stop_id: int, to_stop_id: int) -> dict:
    """Returns real road distance and duration for a stop pair."""
    db = SessionLocal()
    try:
        seg = db.query(RouteSegment).filter(
            RouteSegment.from_stop_id == from_stop_id,
            RouteSegment.to_stop_id == to_stop_id
        ).first()
        if seg:
            return {
                "road_distance_km": seg.road_distance_km,
                "road_duration_min": seg.road_duration_min,
                "source": "osrm_real_road"
            }
        return None
    finally:
        db.close()


if __name__ == "__main__":
    print("Fetching real road data for RPSIT bus routes from OSRM + OpenStreetMap...")
    print("(Free public APIs, rate-limited to respect usage policy)")
    print()
    fetch_and_store_real_road_data()
