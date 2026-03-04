"""
Orchestrateurs d'audit GTFS.
Chaque fonction publique appelle les fonctions privées du fichier d'audit correspondant,
construit les CategoryScore et retourne un FileScore.
"""
import pandas as pd
from audit_models import CategoryScore, FileScore

from audit_agency import (
    _check_agency_id        as agency_id,
    _check_mandatory_fields as agency_mandatory,
    _check_data_format      as agency_format,
    _check_data_consistency as agency_consistency,
)
from audit_calendar import (
    _check_calendar_id      as calendar_id,
    _check_mandatory_fields as calendar_mandatory,
    _check_data_format      as calendar_format,
    _check_data_consistency as calendar_consistency,
)
from audit_calendar_dates import (
    _check_mandatory_fields as calendar_dates_mandatory,
    _check_data_format      as calendar_dates_format,
    _check_data_consistency as calendar_dates_consistency,
)
from audit_routes import (
    _check_route_id         as routes_id,
    _check_mandatory_fields as routes_mandatory,
    _check_data_format      as routes_format,
    _check_data_consistency as routes_consistency,
    _check_accessibility    as routes_accessibility,
)
from audit_stop_times import (
    _check_trip_id          as stop_times_id,
    _check_mandatory_fields as stop_times_mandatory,
    _check_data_format      as stop_times_format,
    _check_temporality      as stop_times_temporality,
)
from audit_stops import (
    _check_stop_id          as stops_id,
    _check_mandatory_fields as stops_mandatory,
    _check_data_format      as stops_format,
    _check_data_consistency as stops_consistency,
    _check_stops_hierarchy  as stops_hierarchy,
    _check_accessibility    as stops_accessibility,
)
from audit_trips import (
    _check_trip_id          as trips_id,
    _check_mandatory_fields as trips_mandatory,
    _check_data_format      as trips_format,
    _check_data_consistency as trips_consistency,
    _check_accessibility    as trips_accessibility,
)


# ============================================================
# agency.txt
# ============================================================

def audit_agency(df: pd.DataFrame, routes_df: pd.DataFrame) -> FileScore:
    id_checks           = agency_id(df)
    mandatory_checks    = agency_mandatory(df)
    format_checks       = agency_format(df)
    consistency_checks  = agency_consistency(df, routes_df)

    return FileScore(
        file       = "agency.txt",
        categories = [
            CategoryScore(category="mandatory",   checks=id_checks + mandatory_checks),
            CategoryScore(category="format",      checks=format_checks),
            CategoryScore(category="consistency", checks=consistency_checks),
        ]
    )


# ============================================================
# calendar.txt
# ============================================================

def audit_calendar(df: pd.DataFrame, trips_df: pd.DataFrame) -> FileScore:
    id_checks           = calendar_id(df)
    mandatory_checks    = calendar_mandatory(df)
    format_checks       = calendar_format(df)
    consistency_checks  = calendar_consistency(df, trips_df)

    return FileScore(
        file       = "calendar.txt",
        categories = [
            CategoryScore(category="mandatory",   checks=id_checks + mandatory_checks),
            CategoryScore(category="format",      checks=format_checks),
            CategoryScore(category="consistency", checks=consistency_checks),
        ]
    )


# ============================================================
# calendar_dates.txt
# ============================================================

def audit_calendar_dates(df: pd.DataFrame, calendar_df: pd.DataFrame | None) -> FileScore:
    mandatory_checks    = calendar_dates_mandatory(df, calendar_df)
    format_checks       = calendar_dates_format(df)
    consistency_checks  = calendar_dates_consistency(df, calendar_df)

    return FileScore(
        file       = "calendar_dates.txt",
        categories = [
            CategoryScore(category="mandatory",   checks=mandatory_checks),
            CategoryScore(category="format",      checks=format_checks),
            CategoryScore(category="consistency", checks=consistency_checks),
        ]
    )


# ============================================================
# routes.txt
# ============================================================

def audit_routes(df: pd.DataFrame, agency_df: pd.DataFrame, trips_df: pd.DataFrame) -> FileScore:
    id_checks           = routes_id(df)
    mandatory_checks    = routes_mandatory(df, agency_df)
    format_checks       = routes_format(df)
    consistency_checks  = routes_consistency(df, trips_df)
    accessibility_checks = routes_accessibility(df)

    return FileScore(
        file       = "routes.txt",
        categories = [
            CategoryScore(category="mandatory",      checks=id_checks + mandatory_checks),
            CategoryScore(category="format",         checks=format_checks),
            CategoryScore(category="consistency",    checks=consistency_checks),
            CategoryScore(category="accessibility",  checks=accessibility_checks),
        ]
    )


# ============================================================
# stop_times.txt
# ============================================================

def audit_stop_times(df: pd.DataFrame, trips_df: pd.DataFrame, stops_df: pd.DataFrame) -> FileScore:
    id_checks           = stop_times_id(df)
    mandatory_checks    = stop_times_mandatory(df, trips_df, stops_df)
    format_checks       = stop_times_format(df)
    temporality_checks  = stop_times_temporality(df)

    return FileScore(
        file       = "stop_times.txt",
        categories = [
            CategoryScore(category="mandatory",   checks=id_checks + mandatory_checks),
            CategoryScore(category="format",      checks=format_checks),
            CategoryScore(category="temporal",    checks=temporality_checks),
        ]
    )


# ============================================================
# stops.txt
# ============================================================

def audit_stops(df: pd.DataFrame, stop_times_df: pd.DataFrame) -> FileScore:
    id_checks            = stops_id(df)
    mandatory_checks     = stops_mandatory(df)
    format_checks        = stops_format(df)
    consistency_checks   = stops_consistency(df, stop_times_df)
    hierarchy_checks     = stops_hierarchy(df)
    accessibility_checks = stops_accessibility(df)

    return FileScore(
        file       = "stops.txt",
        categories = [
            CategoryScore(category="mandatory",      checks=id_checks + mandatory_checks),
            CategoryScore(category="format",         checks=format_checks),
            CategoryScore(category="consistency",    checks=consistency_checks),
            CategoryScore(category="stops_hierarchy", checks=hierarchy_checks),
            CategoryScore(category="accessibility",  checks=accessibility_checks),
        ]
    )


# ============================================================
# trips.txt
# ============================================================

def audit_trips(df: pd.DataFrame, routes_df: pd.DataFrame, calendar_df: pd.DataFrame | None, calendar_dates_df: pd.DataFrame | None, shapes_df: pd.DataFrame | None, stop_times_df: pd.DataFrame) -> FileScore:
    id_checks            = trips_id(df)
    mandatory_checks     = trips_mandatory(df, routes_df, calendar_df, calendar_dates_df)
    format_checks        = trips_format(df)
    consistency_checks   = trips_consistency(df, shapes_df, stop_times_df)
    accessibility_checks = trips_accessibility(df)

    return FileScore(
        file       = "trips.txt",
        categories = [
            CategoryScore(category="mandatory",     checks=id_checks + mandatory_checks),
            CategoryScore(category="format",        checks=format_checks),
            CategoryScore(category="consistency",   checks=consistency_checks),
            CategoryScore(category="accessibility", checks=accessibility_checks),
        ]
    )
