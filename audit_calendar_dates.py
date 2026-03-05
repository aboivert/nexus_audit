import pandas as pd
from audit_models import CheckResult
from audit_generic_functions import check_id_presence, check_id_unicity, check_field_presence, check_format_field, check_orphan_ids


format_config = {'exception_type':{'genre':'required','description':"Validité du champ exception_type",'type':'listing', 'valid_fields':{'1', '2'}},
          'date':{'genre':'required','description':"Validité des dates",'type':'date'},
}


def _check_mandatory_fields(df: pd.DataFrame, calendar_df: pd.DataFrame) -> list[CheckResult]:
    checks = [
        check_id_presence(df, "service_id", weight=3.0),
        check_id_presence(df, "date", weight=3.0),
        check_id_unicity(df, ["service_id", "date"], weight=3.0),
    ]
    if calendar_df is not None:
        checks.append(check_orphan_ids(calendar_df, "service_id", df, "service_id", weight=3.0, category="mandatory"))
    else:
        checks.append(CheckResult(
            check_id = "calendar_dates.mandatory.service_id_consistency",
            label    = "Cohérence des service_id avec calendar.txt",
            category = "mandatory",
            status   = "skip",
            weight   = 3.0,
            message  = "calendar.txt absent, vérification non applicable",
        ))
    return checks


def _check_data_format(df: pd.DataFrame) -> list[CheckResult]:
    return [
        check_format_field(df, "date", format_config["date"], "service_id", weight=1.0),
        check_format_field(df, "exception_type", format_config["exception_type"], ["service_id", "date"], weight=1.0),
    ]


def _check_data_consistency(df: pd.DataFrame, calendar_df: pd.DataFrame | None) -> list[CheckResult]:
    return [
        _check_dates_in_calendar_period(df, calendar_df),
        _check_no_conflicting_exceptions(df),
    ]


def _check_dates_in_calendar_period(df: pd.DataFrame, calendar_df: pd.DataFrame | None) -> CheckResult:
    """
    Vérifie que les dates de calendar_dates.txt sont dans la période
    start_date/end_date de calendar.txt, service_id par service_id.
    """
    if calendar_df is None:
        return CheckResult(
            check_id = "calendar_dates.consistency.dates_in_period",
            label    = "Dates dans la période start_date/end_date du calendar.txt",
            category = "consistency",
            status   = "skip",
            weight   = 2.0,
            message  = "calendar.txt absent, vérification non applicable",
        )

    if "date" not in df.columns or "service_id" not in df.columns \
       or "start_date" not in calendar_df.columns or "end_date" not in calendar_df.columns:
        return CheckResult(
            check_id = "calendar_dates.consistency.dates_in_period",
            label    = "Dates dans la période start_date/end_date du calendar.txt",
            category = "consistency",
            status   = "skip",
            weight   = 2.0,
            message  = "Colonnes date, service_id, start_date ou end_date absentes",
        )

    # Construire un dict service_id → (start_date, end_date) depuis calendar.txt
    calendar_periods = calendar_df.set_index("service_id")[["start_date", "end_date"]].to_dict("index")

    affected_ids = []

    for _, row in df.iterrows():
        service_id = row["service_id"]
        date       = row["date"]

        # service_id absent de calendar.txt → on ignore (couvert par check_orphan_ids)
        if service_id not in calendar_periods:
            continue

        start_date = calendar_periods[service_id]["start_date"]
        end_date   = calendar_periods[service_id]["end_date"]

        if date < start_date or date > end_date:
            affected_ids.append(f"{service_id}:{date}")

    if affected_ids:
        return CheckResult(
            check_id       = "calendar_dates.consistency.dates_in_period",
            label          = "Dates dans la période start_date/end_date du calendar.txt",
            category       = "consistency",
            status         = "warning",
            weight         = 2.0,
            message        = f"{len(affected_ids)} date(s) hors de la période de leur service_id",
            affected_ids   = affected_ids,
            affected_count = len(affected_ids),
            total_count    = len(df),
        )

    return CheckResult(
        check_id    = "calendar_dates.consistency.dates_in_period",
        label       = "Dates dans la période start_date/end_date du calendar.txt",
        category    = "consistency",
        status      = "pass",
        weight      = 2.0,
        message     = "Toutes les dates sont dans la période de leur service_id",
        total_count = len(df),
    )


def _check_no_conflicting_exceptions(df: pd.DataFrame) -> CheckResult:
    """
    Vérifie l'absence de conflits : deux exceptions contraires le même jour
    pour un même service_id (exception_type 1 et 2 le même jour).
    """
    if "service_id" not in df.columns or "date" not in df.columns or "exception_type" not in df.columns:
        return CheckResult(
            check_id = "calendar_dates.consistency.no_conflicting_exceptions",
            label    = "Absence de conflits d'exceptions",
            category = "consistency",
            status   = "skip",
            weight   = 2.0,
            message  = "Colonnes service_id, date ou exception_type absentes",
        )

    # Grouper par (service_id, date) et chercher les groupes avec les deux types
    grouped = df.groupby(["service_id", "date"])["exception_type"].apply(lambda x: set(x.astype(str)))
    conflicts = grouped[grouped.apply(lambda x: {'1', '2'}.issubset(x))]

    if not conflicts.empty:
        affected_ids = [f"{sid}:{date}" for sid, date in conflicts.index]
        return CheckResult(
            check_id       = "calendar_dates.consistency.no_conflicting_exceptions",
            label          = "Absence de conflits d'exceptions",
            category       = "consistency",
            status         = "error",
            weight         = 2.0,
            message        = f"{len(conflicts)} couple(s) (service_id, date) avec des exceptions contradictoires",
            affected_ids   = affected_ids,
            affected_count = len(conflicts),
            total_count    = len(df["service_id"].unique()),
        )

    return CheckResult(
        check_id    = "calendar_dates.consistency.no_conflicting_exceptions",
        label       = "Absence de conflits d'exceptions",
        category    = "consistency",
        status      = "pass",
        weight      = 2.0,
        message     = "Aucun conflit d'exceptions détecté",
        total_count = len(df["service_id"].unique()),
    )