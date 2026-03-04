import pandas as pd
from audit_models import CheckResult
from audit_generic_functions import check_id_presence, check_id_unicity, check_field_presence, check_format_field, check_orphan_ids, check_unused_ids, check_at_least_one_field_presence


format = {'pickup_type':{'genre':'optional','description':"Validité du champ pickup_type",'type':'listing', 'valid_fields':{0, 1, 2 ,3}},
          'drop_off_type':{'genre':'optional','description':"Validité du champ drop_off_type",'type':'listing', 'valid_fields':{0, 1, 2, 3}},
          'departure_time':{'genre':'required','description':"Validité des horaires de départ d\'un arrêt",'type':'time'},
          'arrival_time':{'genre':'required','description':"Validité des horaires d\'arrivée à un arrêt",'type':'time'},
}


def _check_trip_id(df: pd.DataFrame) -> list[CheckResult]:

    return [
        check_id_presence(df, "trip_id", weight=3.0),
        check_id_presence(df, "stop_sequence", weight=3.0),
        check_id_unicity(df,  ["trip_id", "stop_sequence"], weight=3.0),
    ]

def _check_mandatory_fields(df: pd.DataFrame, trips_df: pd.DataFrame, stops_df: pd.DataFrame) -> list[CheckResult]:
    """
    Vérifie la présence des champs obligatoires route_id, trip_id.
    """
    return [
        check_orphan_ids(trips_df, "trip_id", df, "trip_id", weight=3.0, category="mandatory"),
        check_field_presence(df, "stop_id", ["trip_id", "stop_sequence"], weight=1.0),
        check_field_presence(df, "departure_time", ["trip_id", "stop_sequence"], weight=1.0),
        check_field_presence(df, "arrival_time", ["trip_id", "stop_sequence"], weight=1.0),
        check_orphan_ids(stops_df, "stop_id", df, "stop_id", weight=3.0, category = "mandatory"),
    ]


def _check_data_format(df: pd.DataFrame) -> list[CheckResult]:
    return [
        check_format_field(df, "arrival_time", format["arrival_time"], ["trip_id", "stop_sequence"], weight=1.0),
        check_format_field(df, "departure_time", format["departure_time"], ["trip_id", "stop_sequence"], weight=1.0),
        check_format_field(df, "pickup_type", format["pickup_type"], ["trip_id", "stop_sequence"], weight=1.0),
        check_format_field(df, "drop_off_type", format["drop_off_type"], ["trip_id", "stop_sequence"], weight=1.0),
    ]

