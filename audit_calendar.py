"""Audit functions for calendar.txt: mandatory fields, format validation and consistency checks."""
import pandas as pd
from audit_models import CheckResult
from audit_generic_functions import check_id_presence, check_id_unicity, check_field_presence, check_format_field, check_unused_ids
from scoring_config import SCORING_CONFIG


format_config = {'monday':{'genre':'required','description':"Validité du champ monday",'type':'listing', 'valid_fields':{'0', '1'}},
          'tuesday':{'genre':'required','description':"Validité du champ tuesday",'type':'listing', 'valid_fields':{'0', '1'}},
          'wednesday':{'genre':'required','description':"Validité du champ wednesday",'type':'listing', 'valid_fields':{'0', '1'}},
          'thursday':{'genre':'required','description':"Validité du champ thursday",'type':'listing', 'valid_fields':{'0', '1'}},
          'friday':{'genre':'required','description':"Validité du champ friday",'type':'listing', 'valid_fields':{'0', '1'}},
          'saturday':{'genre':'required','description':"Validité du champ saturday",'type':'listing', 'valid_fields':{'0', '1'}},
          'sunday':{'genre':'required','description':"Validité du champ sunday",'type':'listing', 'valid_fields':{'0', '1'}},
          'start_date':{'genre':'required','description':"Validité des dates de début de calendrier",'type':'date'},
          'end_date':{'genre':'required','description':"Validité des dates de fin de calendrier",'type':'date'},
}


def _check_mandatory_fields(df: pd.DataFrame) -> list[CheckResult]:
    """
    Checks presence and unicity of service_id, and presence of all day and date fields.

    :param df: calendar.txt DataFrame.
    """
    cfg = SCORING_CONFIG.get("calendar.txt", {})
    return [
        check_id_presence(df, "service_id", weight=cfg.get("calendar.mandatory.service_id_presence", 2.0)),
        check_id_unicity(df,  "service_id",  weight=cfg.get("calendar.mandatory.service_id_unicity", 2.0)),
        check_field_presence(df, "monday", "service_id", weight=cfg.get("calendar.mandatory.monday_presence", 1.0)),
        check_field_presence(df, "tuesday", "service_id", weight=cfg.get("calendar.mandatory.tuesday_presence", 1.0)),
        check_field_presence(df, "wednesday", "service_id", weight=cfg.get("calendar.mandatory.wednesday_presence", 1.0)),
        check_field_presence(df, "thursday", "service_id", weight=cfg.get("calendar.mandatory.thursday_presence", 1.0)),
        check_field_presence(df, "friday", "service_id", weight=cfg.get("calendar.mandatory.friday_presence", 1.0)),
        check_field_presence(df, "saturday", "service_id", weight=cfg.get("calendar.mandatory.saturday_presence", 1.0)),
        check_field_presence(df, "sunday", "service_id", weight=cfg.get("calendar.mandatory.sunday_presence", 1.0)),
        check_field_presence(df, "start_date", "service_id", weight=cfg.get("calendar.mandatory.start_date_presence", 1.0)),
        check_field_presence(df, "end_date", "service_id", weight=cfg.get("calendar.mandatory.end_date_presence", 1.0)),
    ]


def _check_data_format(df: pd.DataFrame) -> list[CheckResult]:
    """
    Checks format validity of all day (0/1) and date fields against format_config.

    :param df: calendar.txt DataFrame.
    """
    cfg = SCORING_CONFIG.get("calendar.txt", {})
    return [
        check_format_field(df, "monday", format_config["monday"], "service_id", weight=cfg.get("format.monday_valid", 1.0)),
        check_format_field(df, "tuesday", format_config["tuesday"], "service_id", weight=cfg.get("format.tuesday_valid", 1.0)),
        check_format_field(df, "wednesday", format_config["wednesday"], "service_id", weight=cfg.get("format.wednesday_valid", 1.0)),
        check_format_field(df, "thursday", format_config["thursday"], "service_id", weight=cfg.get("format.thursday_valid", 1.0)),
        check_format_field(df, "friday", format_config["friday"], "service_id", weight=cfg.get("format.friday_valid", 1.0)),
        check_format_field(df, "saturday", format_config["saturday"], "service_id", weight=cfg.get("format.saturday_valid", 1.0)),
        check_format_field(df, "sunday", format_config["sunday"], "service_id", weight=cfg.get("format.sunday_valid", 1.0)),
        check_format_field(df, "start_date", format_config["start_date"], "service_id", weight=cfg.get("format.start_date_valid", 1.0)),
        check_format_field(df, "end_date", format_config["end_date"], "service_id", weight=cfg.get("format.end_date_valid", 1.0)),
    ]


def _check_data_consistency(df: pd.DataFrame, trips_df: pd.DataFrame) -> list[CheckResult]:
    """
    Checks service_id usage and date/day logical consistency.

    :param df: calendar.txt DataFrame.
    :param trips_df: trips.txt DataFrame, used to detect unused service_ids.
    """
    cfg = SCORING_CONFIG.get("calendar.txt", {})
    return [
        check_unused_ids(df, "service_id", trips_df, "service_id", weight=cfg.get("calendar.consistency.service_id_no_unused", 1.0)),
        _check_start_before_end(df, weight=cfg.get("calendar.consistency.start_before_end", 2.0)),
        _check_at_least_one_active_day(df, weight=cfg.get("calendar.consistency.at_least_one_active_day", 1.0)),
    ]


def _check_start_before_end(df: pd.DataFrame, weight: float) -> CheckResult:
    """
    Checks that start_date is strictly before end_date for each service.

    :param df: calendar.txt DataFrame.
    """
    if "start_date" not in df.columns or "end_date" not in df.columns:
        return CheckResult(
            check_id = "calendar.consistency.start_before_end",
            label    = "start_date antérieure à end_date",
            category = "consistency",
            status   = "skip",
            weight   = weight,
            message  = "Colonnes start_date et/ou end_date absentes",
        )

    invalid = df[df["start_date"] >= df["end_date"]]

    if not invalid.empty:
        affected_ids = (
            invalid["service_id"].astype(str).tolist()
            if "service_id" in df.columns
            else invalid.index.astype(str).tolist()
        )
        return CheckResult(
            check_id       = "calendar.consistency.start_before_end",
            label          = "start_date antérieure à end_date",
            category       = "consistency",
            status         = "error",
            weight         = weight,
            message        = f"{len(invalid)} service(s) avec start_date >= end_date",
            affected_ids   = affected_ids,
            affected_count = len(invalid),
            total_count    = len(df),
        )

    return CheckResult(
        check_id    = "calendar.consistency.start_before_end",
        label       = "start_date antérieure à end_date",
        category    = "consistency",
        status      = "pass",
        weight      = weight,
        message     = "Toutes les start_date sont antérieures aux end_date",
        total_count = len(df),
    )


def _check_at_least_one_active_day(df: pd.DataFrame, weight: float) -> CheckResult:
    """
    Checks that each service has at least one active day (not all days set to 0).

    :param df: calendar.txt DataFrame.
    """
    day_columns = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    existing_cols = [c for c in day_columns if c in df.columns]

    if not existing_cols:
        return CheckResult(
            check_id = "calendar.consistency.at_least_one_active_day",
            label    = "Au moins un jour actif par service",
            category = "consistency",
            status   = "skip",
            weight   = weight,
            message  = "Colonnes de jours absentes",
        )

    invalid = df[df[existing_cols].astype(int).sum(axis=1) == 0]

    if not invalid.empty:
        affected_ids = (
            invalid["service_id"].astype(str).tolist()
            if "service_id" in df.columns
            else invalid.index.astype(str).tolist()
        )
        return CheckResult(
            check_id       = "calendar.consistency.at_least_one_active_day",
            label          = "Au moins un jour actif par service",
            category       = "consistency",
            status         = "error",
            weight         = weight,
            message        = f"{len(invalid)} service(s) sans aucun jour actif",
            affected_ids   = affected_ids,
            affected_count = len(invalid),
            total_count    = len(df),
        )

    return CheckResult(
        check_id    = "calendar.consistency.at_least_one_active_day",
        label       = "Au moins un jour actif par service",
        category    = "consistency",
        status      = "pass",
        weight      = weight,
        message     = "Tous les services ont au moins un jour actif",
        total_count = len(df),
    )