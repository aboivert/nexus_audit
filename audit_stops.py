import pandas as pd
from audit_models import CheckResult
from audit_generic_functions import check_id_presence, check_id_unicity, check_field_presence, check_format_field, check_accessibility_metrics, check_orphan_ids, check_unused_ids
import pytz

format_config = {'stop_timezone':{'genre':'optional','description':"Validité des fuseaux horaires", 'type':'listing', 'valid_fields':set(pytz.all_timezones)},
          'stop_url':{'genre':'optional','description':"Validité des URL",'type':'url'},
          'stop_lat':{'genre':'required','description':"Validité des latitudes",'type':'coordinates'},
          'stop_lon':{'genre':'required','description':"Validité des longitudes",'type':'coordinates'},
          'wheelchair_boarding':{'genre':'optional','description':"Validité des embarquements UFR",'type':'listing', 'valid_fields':{'0', '1', '2'}},
          'location_type':{'genre':'optional','description':"Validité des types de location",'type':'listing', 'valid_fields':{'0','1','2', '3', '4'}},
}


def _check_mandatory_fields(df: pd.DataFrame) -> list[CheckResult]:
    """
    Vérifie la présence des champs obligatoires agency_name, agency_url, agency_timezone.
    """
    return [
        check_id_presence(df, "stop_id", weight=3.0),
        check_id_unicity(df,  "stop_id", weight=3.0),
        check_field_presence(df, "stop_name", "stop_id", weight=1.0),
        check_field_presence(df, "stop_lat", "stop_id", weight=1.0),
        check_field_presence(df, "stop_lon", "stop_id", weight=1.0),
    ]


def _check_data_format(df: pd.DataFrame) -> list[CheckResult]:
    return [
        check_format_field(df, "stop_url", format_config["stop_url"], "stop_id", weight=1.0),
        check_format_field(df, "stop_timezone", format_config["stop_timezone"], "stop_id", weight=1.0),
        check_format_field(df, "stop_lat", format_config["stop_lat"], "stop_id", weight=1.0),
        check_format_field(df, "stop_lon", format_config["stop_lon"], "stop_id", weight=1.0),
    ]


def _check_data_consistency(df: pd.DataFrame, stop_times_df: pd.DataFrame) -> list[CheckResult]:
    return [
        check_orphan_ids(df, "stop_id", stop_times_df, "stop_id", weight=2.0),
        check_unused_ids(df, "stop_id", stop_times_df, "stop_id", weight=2.0),
    ]


def _check_stops_hierarchy(df: pd.DataFrame) -> list[CheckResult]:
    stations_df = df[df["location_type"].astype(str).str.strip() == "1"] if "location_type" in df.columns else pd.DataFrame()
    df_with_parent = df[
        df["parent_station"].notna() &
        (df["parent_station"].astype(str).str.strip() != "") &
        (df["parent_station"].astype(str).str.strip() != "nan")
    ] if "parent_station" in df.columns else pd.DataFrame()
    return [
        check_format_field(df, "location_type", format_config["location_type"], "stop_id", weight=2.0, category="stops_hierarchy"),
        _check_station_no_parent(df),
        check_orphan_ids(df, "stop_id", df_with_parent, "parent_station", weight=2.0, category="stops_hierarchy"),
        _check_parent_station_is_station(df),
        check_unused_ids(stations_df, "stop_id", df, "parent_station", weight=1.0, category="stops_hierarchy"),
        _check_stop_distance_from_station(df),
    ]


def _check_accessibility(df: pd.DataFrame) -> list[CheckResult]:
    return [
        check_format_field(df, "wheelchair_boarding", format_config["wheelchair_boarding"], "stop_id", weight=1.0, category="accessibility"),
        check_accessibility_metrics(df, "wheelchair_boarding", "stop_id", weight=1.0),
    ]


def _check_station_no_parent(df: pd.DataFrame) -> CheckResult:
    """
    Vérifie que les zones d'arrêt (location_type=1) n'ont pas de parent_station.
    """
    if "location_type" not in df.columns or "parent_station" not in df.columns:
        return CheckResult(
            check_id = "stops.stops_hierarchy.station_no_parent",
            label    = "Les zones d'arrêt ne doivent pas avoir de parent_station",
            category = "stops_hierarchy",
            status   = "skip",
            weight   = 2.0,
            message  = "Colonnes location_type et/ou parent_station absentes",
        )

    # Filtrer les zones d'arrêt (location_type=1)
    stations = df[df["location_type"].astype(str).str.strip() == "1"]

    if stations.empty:
        return CheckResult(
            check_id    = "stops.stops_hierarchy.station_no_parent",
            label       = "Les zones d'arrêt ne doivent pas avoir de parent_station",
            category    = "stops_hierarchy",
            status      = "skip",
            weight      = 2.0,
            message     = "Aucune zone d'arrêt (location_type=1) trouvée",
            total_count = 0,
        )

    # Zones d'arrêt avec parent_station renseigné
    invalid = stations[
        stations["parent_station"].notna() &
        (stations["parent_station"].astype(str).str.strip() != "") &
        (stations["parent_station"].astype(str).str.strip() != "nan")
    ]

    if not invalid.empty:
        affected_ids = (
            invalid["stop_id"].astype(str).tolist()
            if "stop_id" in df.columns
            else invalid.index.astype(str).tolist()
        )
        return CheckResult(
            check_id       = "stops.stops_hierarchy.station_no_parent",
            label          = "Les zones d'arrêt ne doivent pas avoir de parent_station",
            category       = "stops_hierarchy",
            status         = "error",
            weight         = 2.0,
            message        = f"{len(invalid)} zone(s) d'arrêt avec un parent_station renseigné",
            affected_ids   = affected_ids,
            affected_count = len(invalid),
            total_count    = len(stations),
        )

    return CheckResult(
        check_id    = "stops.stops_hierarchy.station_no_parent",
        label       = "Les zones d'arrêt ne doivent pas avoir de parent_station",
        category    = "stops_hierarchy",
        status      = "pass",
        weight      = 2.0,
        message     = "Aucune zone d'arrêt avec un parent_station renseigné",
        total_count = len(stations),
    )


def _check_parent_station_is_station(df: pd.DataFrame) -> CheckResult:
    """
    Vérifie que parent_station pointe vers une zone d'arrêt (location_type=1)
    et non vers un point d'arrêt.
    """
    if "parent_station" not in df.columns or "location_type" not in df.columns or "stop_id" not in df.columns:
        return CheckResult(
            check_id = "stops.stops_hierarchy.parent_station_is_station",
            label    = "parent_station pointe vers une zone d'arrêt (location_type=1)",
            category = "stops_hierarchy",
            status   = "skip",
            weight   = 2.0,
            message  = "Colonnes parent_station, location_type et/ou stop_id absentes",
        )

    # Construire un dict stop_id → location_type
    location_map = df.set_index("stop_id")["location_type"].astype(str).str.strip().to_dict()

    # Filtrer les lignes avec parent_station renseigné
    df_with_parent = df[
        df["parent_station"].notna() &
        (df["parent_station"].astype(str).str.strip() != "") &
        (df["parent_station"].astype(str).str.strip() != "nan")
    ]

    if df_with_parent.empty:
        return CheckResult(
            check_id    = "stops.stops_hierarchy.parent_station_is_station",
            label       = "parent_station pointe vers une zone d'arrêt (location_type=1)",
            category    = "stops_hierarchy",
            status      = "skip",
            weight      = 2.0,
            message     = "Aucun parent_station renseigné",
            total_count = 0,
        )

    affected_ids = []
    total_count  = 0

    for _, row in df_with_parent.iterrows():
        parent_station = str(row["parent_station"]).strip()
        stop_id        = str(row["stop_id"])

        # parent_station absent du fichier → déjà couvert par check 3
        if parent_station not in location_map:
            continue

        total_count += 1
        if location_map[parent_station] != "1":
            affected_ids.append(stop_id)

    if affected_ids:
        return CheckResult(
            check_id       = "stops.stops_hierarchy.parent_station_is_station",
            label          = "parent_station pointe vers une zone d'arrêt (location_type=1)",
            category       = "stops_hierarchy",
            status         = "error",
            weight         = 2.0,
            message        = f"{len(affected_ids)} arrêt(s) dont le parent_station n'est pas une zone d'arrêt",
            affected_ids   = affected_ids,
            affected_count = len(affected_ids),
            total_count    = total_count,
        )

    return CheckResult(
        check_id    = "stops.stops_hierarchy.parent_station_is_station",
        label       = "parent_station pointe vers une zone d'arrêt (location_type=1)",
        category    = "stops_hierarchy",
        status      = "pass",
        weight      = 2.0,
        message     = "Tous les parent_station pointent vers des zones d'arrêt",
        total_count = total_count,
    )


def _check_stop_distance_from_station(df: pd.DataFrame) -> CheckResult:
    """
    Vérifie la distance géographique entre un arrêt et sa zone (parent_station).
    Erreur si distance > 2000m.
    """
    if "parent_station" not in df.columns or "stop_lat" not in df.columns \
       or "stop_lon" not in df.columns or "stop_id" not in df.columns:
        return CheckResult(
            check_id = "stops.stops_hierarchy.stop_distance_from_station",
            label    = "Distance géographique entre arrêt et zone",
            category = "stops_hierarchy",
            status   = "skip",
            weight   = 1.0,
            message  = "Colonnes parent_station, stop_lat, stop_lon et/ou stop_id absentes",
        )

    def haversine(lat1, lon1, lat2, lon2) -> float:
        """Calcule la distance en mètres entre deux points GPS."""
        import math
        R = 6371000  # rayon de la Terre en mètres
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi       = math.radians(lat2 - lat1)
        dlambda    = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Construire un dict stop_id → (lat, lon)
    coords_map = {}
    for _, row in df.iterrows():
        try:
            coords_map[str(row["stop_id"])] = (float(row["stop_lat"]), float(row["stop_lon"]))
        except (ValueError, TypeError):
            continue

    # Filtrer les arrêts avec parent_station renseigné
    df_with_parent = df[
        df["parent_station"].notna() &
        (df["parent_station"].astype(str).str.strip() != "") &
        (df["parent_station"].astype(str).str.strip() != "nan")
    ]

    if df_with_parent.empty:
        return CheckResult(
            check_id    = "stops.stops_hierarchy.stop_distance_from_station",
            label       = "Distance géographique entre arrêt et zone",
            category    = "stops_hierarchy",
            status      = "skip",
            weight      = 1.0,
            message     = "Aucun arrêt avec parent_station renseigné",
            total_count = 0,
        )

    affected_ids = []
    details      = {}
    total_count  = 0

    for _, row in df_with_parent.iterrows():
        stop_id        = str(row["stop_id"])
        parent_station = str(row["parent_station"]).strip()

        if stop_id not in coords_map or parent_station not in coords_map:
            continue

        total_count += 1
        lat1, lon1   = coords_map[stop_id]
        lat2, lon2   = coords_map[parent_station]

        try:
            distance = round(haversine(lat1, lon1, lat2, lon2), 1)
            if distance > 2000:
                affected_ids.append(stop_id)
                details[stop_id] = {
                    "distance_m":      distance,
                    "parent_station":  parent_station,
                }
        except Exception:
            continue

    if affected_ids:
        return CheckResult(
            check_id       = "stops.stops_hierarchy.stop_distance_from_station",
            label          = "Distance géographique entre arrêt et zone",
            category       = "stops_hierarchy",
            status         = "error",
            weight         = 1.0,
            message        = f"{len(affected_ids)} arrêt(s) à plus de 2000m de leur zone",
            affected_ids   = affected_ids,
            affected_count = len(affected_ids),
            total_count    = total_count,
            details        = details,
        )

    return CheckResult(
        check_id    = "stops.stops_hierarchy.stop_distance_from_station",
        label       = "Distance géographique entre arrêt et zone",
        category    = "stops_hierarchy",
        status      = "pass",
        weight      = 1.0,
        message     = "Tous les arrêts sont à moins de 2000m de leur zone",
        total_count = total_count,
    )