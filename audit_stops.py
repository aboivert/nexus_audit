import pandas as pd
from audit_models import CheckResult
from audit_generic_functions import check_id_presence, check_id_unicity, check_field_presence, check_format_field
import pytz

format = {'stop_timezone':{'genre':'optional','description':"Validité des fuseaux horaires", 'type':'listing', 'valid_fields':set(pytz.all_timezones)},
          'stop_url':{'genre':'optional','description':"Validité des URL",'type':'url'},
          'stop_lat':{'genre':'required','description':"Validité des latitudes",'type':'coordinates'},
          'stop_lon':{'genre':'required','description':"Validité des longitudes",'type':'coordinates'},
          'wheelchair_boarding':{'genre':'optional','description':"Validité des embarquements UFR",'type':'listing', 'valid_fields':['0', '1','2']},
          'location_type':{'genre':'optional','description':"Validité des types de location",'type':'listing', 'valid_fields':['0','1','2', '3', '4']},
}


def _check_stop_id(df: pd.DataFrame) -> list[CheckResult]:

    return [
        check_id_presence(df, "stop_id", weight=3.0),
        check_id_unicity(df,  "stop_id", weight=3.0),
    ]

def _check_mandatory_fields(df: pd.DataFrame) -> list[CheckResult]:
    """
    Vérifie la présence des champs obligatoires agency_name, agency_url, agency_timezone.
    """
    return [
        check_field_presence(df, "stop_name", "stop_id", weight=1.0),
        check_field_presence(df, "stop_lat", "stop_id", weight=1.0),
        check_field_presence(df, "stop_lon", "stop_id", weight=1.0),
    ]


def _check_data_format(df: pd.DataFrame) -> list[CheckResult]:
    return [
        check_format_field(df, "stop_url", format["stop_url"], "stop_id", weight=1.0),
        check_format_field(df, "stop_timezone", format["stop_timezone"], "stop_id", weight=1.0),
        check_format_field(df, "stop_lat", format["stop_lat"], "stop_id", weight=1.0),
        check_format_field(df, "stop_lon", format["stop_lon"], "stop_id", weight=1.0),
    ]