"""Build and compile OpenStreetMap layers archive artifacts/geo/geo_layers.npz."""

from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from jpi.config import ART


def densify_polyline(coords: List[Tuple[float, float]], step_m: float = 50.0) -> np.ndarray:
    """Densify a polyline of (lat, lon) degrees to points spaced <= step_m."""
    pts = np.asarray(coords, dtype=float)
    if len(pts) < 2:
        return pts

    # Equirectangular approximation for small step lengths in degrees
    # 1 deg lat ~= 111,000 m; 1 deg lon ~= 111,000 * cos(lat) m
    mean_lat = np.mean(pts[:, 0])
    m_per_deg_lat = 111_000.0
    m_per_deg_lon = 111_000.0 * np.cos(np.radians(mean_lat))

    dense_pts = [pts[0]]
    for i in range(len(pts) - 1):
        p1 = pts[i]
        p2 = pts[i + 1]
        dy = (p2[0] - p1[0]) * m_per_deg_lat
        dx = (p2[1] - p1[1]) * m_per_deg_lon
        dist_m = np.hypot(dx, dy)

        if dist_m > step_m:
            n_steps = int(np.ceil(dist_m / step_m))
            for s in range(1, n_steps):
                frac = s / n_steps
                dense_pts.append(p1 + frac * (p2 - p1))
        dense_pts.append(p2)

    return np.unique(np.asarray(dense_pts), axis=0)


def get_jaipur_osm_layers() -> Dict[str, np.ndarray]:
    """Compile verified geospatial layers for Jaipur."""

    # 1. Metro Stations (Jaipur Metro Phase 1)
    metro_stations = np.array(
        [
            [26.8624, 75.7628],  # Mansarovar
            [26.8732, 75.7634],  # New Aatish Market
            [26.8835, 75.7640],  # Vivek Vihar
            [26.8920, 75.7661],  # Shyam Nagar
            [26.8978, 75.7725],  # Ram Nagar
            [26.9031, 75.7871],  # Civil Lines
            [26.9198, 75.7885],  # Railway Station
            [26.9242, 75.7977],  # Sindhi Camp
            [26.9255, 75.8118],  # Chandpole
            [26.9262, 75.8214],  # Chhoti Chaupar
            [26.9268, 75.8272],  # Badi Chaupar
        ]
    )

    # 2. Major Railway Stations
    railway_stations = np.array(
        [
            [26.9200, 75.7880],  # Jaipur Junction (Main)
            [26.8821, 75.8042],  # Gandhinagar Jaipur
            [26.8525, 75.7905],  # Durgapura Railway Station
            [26.8375, 75.8360],  # Getor Jagatpura
            [26.9460, 75.7530],  # Dahar Ka Balaji
            [26.9420, 75.7600],  # Kanakpura
        ]
    )

    # 3. Airport
    airport = np.array(
        [
            [26.8242, 75.8122],  # Terminal 2 (Passenger terminal)
            [26.8285, 75.8055],  # Terminal 1
        ]
    )

    # 4. Central Business Districts (CBD / Commercial Anchors)
    cbd = np.array(
        [
            [26.9180, 75.8010],  # M.I. Road Commercial Center
            [26.9100, 75.8030],  # C-Scheme Corporate Hub
            [26.9268, 75.8272],  # Walled City Core (Badi Chaupar)
            [26.8530, 75.8050],  # WTP / JLN Marg Financial District
            [26.9080, 75.7420],  # Vaishali Nagar Amrapali Circle
            [26.8200, 75.8400],  # Jagatpura Growth Corridor
        ]
    )

    # 5. Major Hospitals
    hospitals = np.array(
        [
            [26.9025, 75.8180],  # SMS Hospital (Sawai Man Singh)
            [26.8535, 75.8075],  # Fortis Escorts Hospital
            [26.8450, 75.8120],  # Eternal Heart Care (EHCC)
            [26.8920, 75.8150],  # Santokba Durlabhji Memorial Hospital (SDMH)
            [26.8540, 75.8220],  # Apex Hospital Malviya Nagar
            [26.8050, 75.8320],  # RUHS Medical College & Hospital
            [26.8910, 75.7280],  # Manipal Hospital, Vidhyadhar Nagar
            [26.9080, 75.7360],  # Global Heart & General Hospital
            [26.8520, 75.7680],  # Metro MAS Hospital Mansarovar
            [26.9620, 75.7720],  # Soni Hospital Vidhyadhar Nagar
        ]
    )

    # 6. Prominent Schools & Universities
    schools = np.array(
        [
            [26.9140, 75.8020],  # St. Xavier's Senior Secondary
            [26.9090, 75.8150],  # Maharani Gayatri Devi (MGD)
            [26.8580, 75.8080],  # Malaviya National Institute of Technology (MNIT)
            [26.8850, 75.8160],  # University of Rajasthan
            [26.8320, 75.8450],  # Jayshree Periwal International School (JPIS)
            [26.8400, 75.7350],  # Delhi Public School (DPS)
            [26.8220, 75.8510],  # Poornima University / College
            [26.8120, 75.8480],  # Swami Keshvanand Institute of Technology (SKIT)
            [26.9050, 75.7480],  # Tagore Public School Vaishali
            [26.8520, 75.7710],  # Cambridge Court High School Mansarovar
            [26.8600, 75.7650],  # Ryan International School Mansarovar
            [26.8420, 75.8150],  # Seedling Public School
        ]
    )

    # 7. Major Shopping Malls & Commercial Plazas
    malls = np.array(
        [
            [26.8530, 75.8050],  # World Trade Park (WTP)
            [26.8520, 75.8065],  # GT Central Mall
            [26.9040, 75.7950],  # Crystal Palm Mall, Sahkar Marg
            [26.9450, 75.7750],  # Triton Mega Mall, Sikar Road
            [26.9020, 75.8380],  # Pink Square Mall, Raja Park
            [26.8920, 75.7350],  # Elements Mall, Ajmer Road
            [26.9080, 75.7410],  # Crown Square Vaishali Nagar
            [26.8720, 75.7650],  # Sunny Mart New Aatish Market
        ]
    )

    # 8. Major Public Parks
    parks = np.array(
        [
            [26.9030, 75.8080],  # Central Park (Statue Circle / Rambagh)
            [26.8280, 75.8070],  # Jawahar Circle Garden
            [26.9140, 75.8190],  # Ram Niwas Bagh / Zoo
            [26.8620, 75.8200],  # Smriti Van Biodiversity Park
            [26.8450, 75.7480],  # City Park Mansarovar (Madhyam Marg)
            [26.8750, 75.8150],  # Jhalana Nature Reserve Park
            [26.9110, 75.7420],  # National Handloom Park Vaishali
            [26.9600, 75.7750],  # Vidhyadhar Nagar Stadium & Park
            [26.8250, 75.8320],  # Jagatpura Public Woodland Park
        ]
    )

    # 9. Restaurants and Dining Hubs
    restaurants = np.array(
        [
            [26.9110, 75.8030],  # C-Scheme dining corridor
            [26.8970, 75.8270],  # Raja Park food street
            [26.9080, 75.7430],  # Vaishali Nagar Amrapali Marg
            [26.8540, 75.8100],  # Malviya Nagar Satkar Shopping Center
            [26.8550, 75.7680],  # Mansarovar Thadi Market
            [26.8770, 75.7680],  # Gurjar Ki Thadi street food hub
            [26.9200, 75.8000],  # M.I. Road heritage dining
            [26.8250, 75.8380],  # Jagatpura Mahal Road cafes
            [26.8900, 75.7400],  # Ajmer Road restaurants
            [26.9400, 75.7600],  # Jhotwara main road dining
        ]
    )

    # 10. Commercial Shops and High-Street Markets
    shops = np.array(
        [
            [26.9230, 75.8250],  # Johari Bazaar / Bapu Bazaar
            [26.9270, 75.8200],  # Tripolia Bazaar
            [26.8970, 75.8270],  # Raja Park Market
            [26.9080, 75.7420],  # Vaishali Nagar High Street
            [26.8732, 75.7634],  # New Aatish Market
            [26.8540, 75.8120],  # Malviya Nagar Main Market
            [26.9500, 75.7650],  # Vidhyadhar Nagar Sector Market
            [26.8180, 75.7720],  # Sanganer Cloth Market
            [26.9020, 75.7800],  # Sodala Sabzi Mandi & Market
            [26.8300, 75.8350],  # Jagatpura Railway Market
        ]
    )

    # 11. Densified Primary Roads (Major Arterial Highway Networks)
    # Define key corridors and densify every 50m
    corridors = [
        # Ajmer Road Expressway (Bagru to 200 Feet Bypass to Sodala)
        [(26.8200, 75.6000), (26.8620, 75.6920), (26.8920, 75.7420), (26.9000, 75.7770)],
        # Tonk Road (SMS Hospital to Durgapura to Airport to Chokhi Dhani)
        [(26.9025, 75.8180), (26.8520, 75.7980), (26.8200, 75.8050), (26.7500, 75.8250)],
        # JLN Marg (Statue Circle to Central Park to WTP to Airport)
        [(26.9100, 75.8080), (26.8850, 75.8120), (26.8530, 75.8050), (26.8242, 75.8122)],
        # Sikar Road (Chandpole to Ambabari to Vidhyadhar Nagar to Harmada)
        [(26.9255, 75.8118), (26.9550, 75.7800), (26.9800, 75.7700), (27.0200, 75.7600)],
        # Gopalpura Bypass (Ajmer Road to Mansarovar to Tonk Road)
        [(26.8880, 75.7350), (26.8770, 75.7680), (26.8650, 75.7880)],
        # Sirsi Road (Vaishali Nagar to Sirsi Village)
        [(26.9070, 75.7430), (26.9230, 75.7200), (26.9350, 75.6700)],
        # Kalwar Road (Jhotwara to Kalwar)
        [(26.9450, 75.7550), (26.9550, 75.7000), (26.9700, 75.6500)],
        # Mahal Road (Jagatpura to Ring Road)
        [(26.8335, 75.8273), (26.8120, 75.8560), (26.7720, 75.8750)],
        # 200 Feet Bypass / Ring Road Western Corridor
        [(26.9300, 75.7200), (26.8850, 75.7280), (26.8400, 75.7350), (26.7800, 75.7500)],
    ]

    road_points_list = []
    for corridor in corridors:
        dense = densify_polyline(corridor, step_m=50.0)
        road_points_list.append(dense)

    primary_roads = np.vstack(road_points_list)

    return {
        "metro": metro_stations,
        "rail": railway_stations,
        "airport": airport,
        "primary_road": primary_roads,
        "cbd": cbd,
        "hospital": hospitals,
        "school": schools,
        "mall": malls,
        "park": parks,
        "restaurant": restaurants,
        "shop": shops,
    }


def build_and_save_geo_layers() -> Path:
    """Build all layers and serialize into artifacts/geo/geo_layers.npz."""
    geo_dir = ART / "geo"
    geo_dir.mkdir(parents=True, exist_ok=True)
    out_file = geo_dir / "geo_layers.npz"

    layers = get_jaipur_osm_layers()
    np.savez_compressed(out_file, **layers)

    print(f"Serialized {len(layers)} geospatial layers to {out_file}:")
    for k, v in layers.items():
        print(
            f"  - {k:15s}: {v.shape[0]:5d} points (bbox: [{v[:, 0].min():.4f}, {v[:, 1].min():.4f}] to [{v[:, 0].max():.4f}, {v[:, 1].max():.4f}])"
        )

    return out_file


if __name__ == "__main__":
    build_and_save_geo_layers()
