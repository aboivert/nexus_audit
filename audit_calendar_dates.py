import pandas as pd
from audit_models import CheckResult
from audit_generic_functions import check_id_presence, check_id_unicity, check_field_presence, check_format_field, check_orphan_ids


format = {'exception_type':{'genre':'required','description':"Validité du champ exception_type",'type':'listing', 'valid_fields':[1, 2]},
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
        check_format_field(df, "date", format["date"], "service_id", weight=1.0),
        check_format_field(df, "exception_type", format["exception_type"], ["service_id", "date"], weight=1.0),
    ]