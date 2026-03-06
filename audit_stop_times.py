"""Audit functions for stop_times.txt: mandatory fields, format validation and temporal consistency checks."""
import pandas as pd
from audit_models import CheckResult
from audit_generic_functions import check_id_presence, check_id_unicity, check_field_presence, check_format_field, check_orphan_ids, check_unused_ids, check_at_least_one_field_presence


format_config = {'pickup_type':{'genre':'optional','description':"Validité du champ pickup_type",'type':'listing', 'valid_fields':{'0', '1', '2' ,'3'}},
          'drop_off_type':{'genre':'optional','description':"Validité du champ drop_off_type",'type':'listing', 'valid_fields':{'0', '1', '2', '3'}},
          'departure_time':{'genre':'required','description':"Validité des horaires de départ d\'un arrêt",'type':'time'},
          'arrival_time':{'genre':'required','description':"Validité des horaires d\'arrivée à un arrêt",'type':'time'},
}


def _check_mandatory_fields(df: pd.DataFrame, trips_df: pd.DataFrame, stops_df: pd.DataFrame) -> list[CheckResult]:
    """
    Checks presence and unicity of trip_id and stop_sequence, and cross-file consistency
    with trips.txt and stops.txt.

    :param df: stop_times.txt DataFrame.
    :param trips_df: trips.txt DataFrame.
    :param stops_df: stops.txt DataFrame.
    """
    return [
        check_id_presence(df, "trip_id", weight=3.0),
        check_id_presence(df, "stop_sequence", weight=3.0),
        check_id_unicity(df,  ["trip_id", "stop_sequence"], weight=3.0),
        check_orphan_ids(trips_df, "trip_id", df, "trip_id", weight=3.0, category="mandatory"),
        check_field_presence(df, "stop_id", ["trip_id", "stop_sequence"], weight=1.0),
        check_field_presence(df, "departure_time", ["trip_id", "stop_sequence"], weight=1.0),
        check_field_presence(df, "arrival_time", ["trip_id", "stop_sequence"], weight=1.0),
        check_orphan_ids(stops_df, "stop_id", df, "stop_id", weight=3.0, category = "mandatory"),
    ]


def _check_data_format(df: pd.DataFrame) -> list[CheckResult]:
    """
    Checks format validity of pickup_type and drop_off_type fields against format_config.

    :param df: stop_times.txt DataFrame.
    """
    return [
        check_format_field(df, "pickup_type", format_config["pickup_type"], ["trip_id", "stop_sequence"], weight=1.0),
        check_format_field(df, "drop_off_type", format_config["drop_off_type"], ["trip_id", "stop_sequence"], weight=1.0),
    ]


def _check_temporality(df: pd.DataFrame) -> list[CheckResult]:
    """
    Checks time format validity and temporal consistency (order, dwell time).

    :param df: stop_times.txt DataFrame.
    """
    return [
        check_format_field(df, "arrival_time",   format_config["arrival_time"],   ["trip_id", "stop_sequence"], weight=1.0, category="temporal"),
        check_format_field(df, "departure_time", format_config["departure_time"], ["trip_id", "stop_sequence"], weight=1.0, category="temporal"),
        _check_arrival_before_departure(df),
        _check_sequential_consistency(df),
        _check_excessive_dwell_time(df),
    ]


def _parse_time_to_seconds(time_str: str) -> int | None:
    """
    Converts a GTFS time string (HH:MM:SS) to seconds. Handles hours > 23.
    Returns None if the format is invalid.

    :param time_str: Time string to parse.
    """
    try:
        time_str = str(time_str).strip()
        parts    = time_str.split(":")
        if len(parts) != 3:
            return None
        hours   = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        if hours < 0 or not (0 <= minutes <= 59) or not (0 <= seconds <= 59):
            return None
        return hours * 3600 + minutes * 60 + seconds
    except (ValueError, TypeError):
        return None
    

def _check_arrival_before_departure(df: pd.DataFrame) -> CheckResult:
    """
    Checks that arrival_time <= departure_time for each stop.

    :param df: stop_times.txt DataFrame.
    """
    if "arrival_time" not in df.columns or "departure_time" not in df.columns:
        return CheckResult(
            check_id = "stop_times.temporal.arrival_before_departure",
            label    = "Cohérence intra-arrêt : arrival_time ≤ departure_time",
            category = "temporal",
            status   = "skip",
            weight   = 2.0,
            message  = "Colonnes arrival_time et/ou departure_time absentes",
        )

    affected_ids = []

    for _, row in df.iterrows():
        arrival   = _parse_time_to_seconds(row["arrival_time"])
        departure = _parse_time_to_seconds(row["departure_time"])

        if arrival is None or departure is None:
            continue

        if arrival > departure:
            trip_id       = str(row["trip_id"]) if "trip_id" in df.columns else str(row.name)
            stop_sequence = str(row["stop_sequence"]) if "stop_sequence" in df.columns else "N/A"
            affected_ids.append(f"{trip_id}:{stop_sequence}")

    if affected_ids:
        return CheckResult(
            check_id       = "stop_times.temporal.arrival_before_departure",
            label          = "Cohérence intra-arrêt : arrival_time ≤ departure_time",
            category       = "temporal",
            status         = "error",
            weight         = 2.0,
            message        = f"{len(affected_ids)} arrêt(s) avec arrival_time > departure_time",
            affected_ids   = affected_ids,
            affected_count = len(affected_ids),
            total_count    = len(df),
        )

    return CheckResult(
        check_id    = "stop_times.temporal.arrival_before_departure",
        label       = "Cohérence intra-arrêt : arrival_time ≤ departure_time",
        category    = "temporal",
        status      = "pass",
        weight      = 2.0,
        message     = "Tous les arrival_time sont antérieurs ou égaux aux departure_time",
        total_count = len(df),
    )


def _check_sequential_consistency(df: pd.DataFrame) -> CheckResult:
    """
    Checks that each stop's departure_time is <= the next stop's arrival_time, for each trip.

    :param df: stop_times.txt DataFrame.
    """
    if "trip_id" not in df.columns or "stop_sequence" not in df.columns \
       or "departure_time" not in df.columns or "arrival_time" not in df.columns:
        return CheckResult(
            check_id = "stop_times.temporal.sequential_consistency",
            label    = "Cohérence séquentielle des horaires",
            category = "temporal",
            status   = "skip",
            weight   = 2.0,
            message  = "Colonnes trip_id, stop_sequence, departure_time ou arrival_time absentes",
        )

    affected_ids = []
    total_pairs  = 0

    # Trier par trip_id et stop_sequence
    df_sorted = df.sort_values(["trip_id", "stop_sequence"])

    for trip_id, group in df_sorted.groupby("trip_id"):
        rows = group.reset_index(drop=True)

        for i in range(len(rows) - 1):
            departure_n  = _parse_time_to_seconds(rows.loc[i,   "departure_time"])
            arrival_n1   = _parse_time_to_seconds(rows.loc[i+1, "arrival_time"])
            seq_n        = str(rows.loc[i,   "stop_sequence"])
            seq_n1       = str(rows.loc[i+1, "stop_sequence"])

            if departure_n is None or arrival_n1 is None:
                continue

            total_pairs += 1

            if departure_n > arrival_n1:
                affected_ids.append(f"{trip_id}:{seq_n}_{seq_n1}")

    if affected_ids:
        return CheckResult(
            check_id       = "stop_times.temporal.sequential_consistency",
            label          = "Cohérence séquentielle des horaires",
            category       = "temporal",
            status         = "error",
            weight         = 2.0,
            message        = f"{len(affected_ids)} transition(s) avec departure_time > arrival_time suivant",
            affected_ids   = affected_ids,
            affected_count = len(affected_ids),
            total_count    = total_pairs,
        )

    return CheckResult(
        check_id    = "stop_times.temporal.sequential_consistency",
        label       = "Cohérence séquentielle des horaires",
        category    = "temporal",
        status      = "pass",
        weight      = 2.0,
        message     = "Tous les horaires sont séquentiellement cohérents",
        total_count = total_pairs,
    )


def _check_excessive_dwell_time(df: pd.DataFrame) -> CheckResult:
    """
    Detects stops where dwell time (departure - arrival) exceeds 1 hour.

    :param df: stop_times.txt DataFrame.
    """
    if "arrival_time" not in df.columns or "departure_time" not in df.columns:
        return CheckResult(
            check_id = "stop_times.temporal.excessive_dwell_time",
            label    = "Détection des temps d'arrêt excessifs (> 1h)",
            category = "temporal",
            status   = "skip",
            weight   = 1.0,
            message  = "Colonnes arrival_time et/ou departure_time absentes",
        )

    affected_ids = []
    details      = {}
    total_count  = 0

    for _, row in df.iterrows():
        arrival   = _parse_time_to_seconds(row["arrival_time"])
        departure = _parse_time_to_seconds(row["departure_time"])

        if arrival is None or departure is None:
            continue

        total_count += 1
        dwell_time   = departure - arrival

        if dwell_time > 3600:
            trip_id       = str(row["trip_id"])       if "trip_id"       in df.columns else str(row.name)
            stop_sequence = str(row["stop_sequence"]) if "stop_sequence" in df.columns else "N/A"
            key           = f"{trip_id}:{stop_sequence}"
            affected_ids.append(key)
            details[key] = {
                "arrival_time":   str(row["arrival_time"]),
                "departure_time": str(row["departure_time"]),
                "dwell_seconds":  dwell_time,
                "dwell_minutes":  round(dwell_time / 60, 1),
            }

    if affected_ids:
        return CheckResult(
            check_id       = "stop_times.temporal.excessive_dwell_time",
            label          = "Détection des temps d'arrêt excessifs (> 1h)",
            category       = "temporal",
            status         = "warning",
            weight         = 1.0,
            message        = f"{len(affected_ids)} arrêt(s) avec un temps d'arrêt supérieur à 1h",
            affected_ids   = affected_ids,
            affected_count = len(affected_ids),
            total_count    = total_count,
            details        = details,
        )

    return CheckResult(
        check_id    = "stop_times.temporal.excessive_dwell_time",
        label       = "Détection des temps d'arrêt excessifs (> 1h)",
        category    = "temporal",
        status      = "pass",
        weight      = 1.0,
        message     = "Aucun temps d'arrêt excessif détecté",
        total_count = total_count,
    )