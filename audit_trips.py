import pandas as pd
from audit_models import CheckResult
from audit_generic_functions import check_id_presence, check_id_unicity, check_field_presence, check_format_field
import pytz

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

def _check_mandatory_fields(df: pd.DataFrame) -> list[CheckResult]:
    """
    Vérifie la présence des champs obligatoires route_id, trip_id.
    """
    return [
        check_field_presence(df, "route_id", "trip_id", weight=1.0),
        check_field_presence(df, "service_id", "trip_id", weight=1.0),
    ]


def _check_data_format(df: pd.DataFrame) -> list[CheckResult]:
    return [
        check_format_field(df, "direction_id", format["direction_id"], "trip_id", weight=1.0),
        check_format_field(df, "bikes_allowed", format["bikes_allowed"], "trip_id", weight=1.0),
    ]