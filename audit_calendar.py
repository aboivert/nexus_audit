import pandas as pd
from audit_models import CheckResult
from audit_generic_functions import check_id_presence, check_id_unicity, check_field_presence, check_format_field, check_unused_ids


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
    Vérifie la présence des champs obligatoires de dates et de jours
    """
    return [
        check_id_presence(df, "service_id", weight=3.0),
        check_id_unicity(df,  "service_id", weight=3.0),
        check_field_presence(df, "monday", "service_id", weight=1.0),
        check_field_presence(df, "tuesday", "service_id", weight=1.0),
        check_field_presence(df, "wednesday", "service_id", weight=1.0),
        check_field_presence(df, "thursday", "service_id", weight=1.0),
        check_field_presence(df, "friday", "service_id", weight=1.0),
        check_field_presence(df, "saturday", "service_id", weight=1.0),
        check_field_presence(df, "sunday", "service_id", weight=1.0),
        check_field_presence(df, "start_date", "service_id", weight=1.0),
        check_field_presence(df, "end_date", "service_id", weight=1.0),
    ]


def _check_data_format(df: pd.DataFrame) -> list[CheckResult]:
    return [
        check_format_field(df, "monday", format_config["monday"], "service_id", weight=1.0),
        check_format_field(df, "tuesday", format_config["tuesday"], "service_id", weight=1.0),
        check_format_field(df, "wednesday", format_config["wednesday"], "service_id", weight=1.0),
        check_format_field(df, "thursday", format_config["thursday"], "service_id", weight=1.0),
        check_format_field(df, "friday", format_config["friday"], "service_id", weight=1.0),
        check_format_field(df, "saturday", format_config["saturday"], "service_id", weight=1.0),
        check_format_field(df, "sunday", format_config["sunday"], "service_id", weight=1.0),
        check_format_field(df, "start_date", format_config["start_date"], "service_id", weight=1.0),
        check_format_field(df, "end_date", format_config["end_date"], "service_id", weight=1.0),
    ]


def _check_data_consistency(df: pd.DataFrame, trips_df: pd.DataFrame) -> list[CheckResult]:
    return [
        check_unused_ids(df, "service_id", trips_df, "service_id", weight=2.0),
        _check_start_before_end(df),
        _check_at_least_one_active_day(df),
    ]


def _check_start_before_end(df: pd.DataFrame) -> CheckResult:
    """
    Vérifie que start_date est antérieure à end_date pour chaque service.
    """
    if "start_date" not in df.columns or "end_date" not in df.columns:
        return CheckResult(
            check_id = "calendar.consistency.start_before_end",
            label    = "start_date antérieure à end_date",
            category = "consistency",
            status   = "skip",
            weight   = 2.0,
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
            weight         = 2.0,
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
        weight      = 2.0,
        message     = "Toutes les start_date sont antérieures aux end_date",
        total_count = len(df),
    )


def _check_at_least_one_active_day(df: pd.DataFrame) -> CheckResult:
    """
    Vérifie qu'au moins un jour est actif par service (pas tous à 0).
    """
    day_columns = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    existing_cols = [c for c in day_columns if c in df.columns]

    if not existing_cols:
        return CheckResult(
            check_id = "calendar.consistency.at_least_one_active_day",
            label    = "Au moins un jour actif par service",
            category = "consistency",
            status   = "skip",
            weight   = 2.0,
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
            weight         = 2.0,
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
        weight      = 2.0,
        message     = "Tous les services ont au moins un jour actif",
        total_count = len(df),
    )