import pandas as pd
from audit_models import CheckResult
from audit_generic_functions import check_id_presence, check_id_unicity, check_field_presence, check_format_field, check_orphan_ids, check_unused_ids, check_at_least_one_field_presence


format = {'cars_allowed':{'genre':'optional','description':"Validité de l'autorisation de prendre une voiture à bord",'type':'listing', 'valid_fields':['0', '1','2']},
          'bikes_allowed':{'genre':'optional','description':"Validité de l'autorisation de prendre un vélo à bord",'type':'listing', 'valid_fields':['0', '1','2']},
          'wheelchair_accessible':{'genre':'optional','description':"Validité des embarquements UFR",'type':'listing', 'valid_fields':['0', '1','2']},
          'direction_id':{'genre':'optional','description':"Validité des sens de direction",'type':'listing', 'valid_fields':['0','1']},
}


def _check_trip_id(df: pd.DataFrame) -> list[CheckResult]:

    return [
        check_id_presence(df, "trip_id", weight=3.0),
        check_id_unicity(df,  "trip_id", weight=3.0),
    ]

def _check_mandatory_fields(df: pd.DataFrame, routes_df: pd.DataFrame, calendar_df: pd.DataFrame, calendar_dates_df: pd.DataFrame) -> list[CheckResult]:
    """
    Vérifie la présence des champs obligatoires route_id, trip_id.
    """
    return [
        check_field_presence(df, "route_id", "trip_id", weight=1.0),
        check_field_presence(df, "service_id", "trip_id", weight=1.0),
        check_orphan_ids(routes_df, "route_id", df, "route_id", weight=3.0, category = "mandatory"),
        _check_service_id_existence(df, calendar_df, calendar_dates_df, weight=3.0),
        check_at_least_one_field_presence(df, ["trip_short_name","trip_headsign"], "trip_id", weight=3.0),
    ]


def _check_data_format(df: pd.DataFrame) -> list[CheckResult]:
    return [
        check_format_field(df, "direction_id", format["direction_id"], "trip_id", weight=1.0),
        check_format_field(df, "bikes_allowed", format["bikes_allowed"], "trip_id", weight=1.0),
    ]


def _check_data_consistency(df: pd.DataFrame, shapes_df: pd.DataFrame, stop_times_df: pd.DataFrame) -> list[CheckResult]:
    checks = [
        check_unused_ids(df, "trip_id", stop_times_df, "trip_id", weight=2.0),
    ]

    if shapes_df is not None:
        checks.append(check_orphan_ids(shapes_df, "shape_id", df, "shape_id", weight=2.0))
    else:
        checks.append(CheckResult(
            check_id = "trips.consistency.shape_id_existence",
            label    = "Existence des shape_id dans shapes.txt",
            category = "consistency",
            status   = "skip",
            weight   = 2.0,
            message  = "shapes.txt absent, vérification non applicable",
        ))
    return checks


def _check_service_id_existence(df: pd.DataFrame, calendar_df: pd.DataFrame | None, calendar_dates_df: pd.DataFrame | None, weight: float = 3.0) -> CheckResult:

    # Aucun des deux fichiers disponible → skip
    if calendar_df is None and calendar_dates_df is None:
        return CheckResult(
            check_id = "trips.mandatory.service_id_existence",
            label    = "Existence des service_id dans calendar.txt et/ou calendar_dates.txt",
            category = "mandatory",
            status   = "skip",
            weight   = weight,
            message  = "Ni calendar.txt ni calendar_dates.txt disponibles",
        )

    # Construction d'un DataFrame union des service_id valides
    frames = []
    if calendar_df is not None:
        frames.append(calendar_df[["service_id"]])
    if calendar_dates_df is not None:
        frames.append(calendar_dates_df[["service_id"]])
    
    combined_df = pd.concat(frames).drop_duplicates()

    # On délègue à check_orphan_ids
    return check_orphan_ids(
        df         = combined_df,
        id_field   = "service_id",
        ref_df     = df,
        ref_field  = "service_id",
        weight     = weight,
        category   = "mandatory",
    )