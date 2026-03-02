import pandas as pd
from audit_models import CheckResult
from audit_generic_functions import check_id_presence, check_id_unicity, check_field_presence, check_format_field


format = {'monday':{'genre':'required','description':"Validité du champ monday",'type':'listing', 'valid_fields':['0', '1',]},
          'tuesday':{'genre':'required','description':"Validité du champ tuesday",'type':'listing', 'valid_fields':['0', '1',]},
          'wednesday':{'genre':'required','description':"Validité du champ wednesday",'type':'listing', 'valid_fields':['0', '1',]},
          'thursday':{'genre':'required','description':"Validité du champ thursday",'type':'listing', 'valid_fields':['0', '1',]},
          'friday':{'genre':'required','description':"Validité du champ friday",'type':'listing', 'valid_fields':['0', '1',]},
          'saturday':{'genre':'required','description':"Validité du champ saturday",'type':'listing', 'valid_fields':['0', '1',]},
          'sunday':{'genre':'required','description':"Validité du champ sunday",'type':'listing', 'valid_fields':['0', '1',]},
          'start_date':{'genre':'required','description':"Validité des dates de début de calendrier",'type':'date'},
          'end_date':{'genre':'required','description':"Validité des dates de fin de calendrier",'type':'date'},
}


def _check_calendar_id(df: pd.DataFrame) -> list[CheckResult]:
    """
    Vérification de la présence et de l'unicité des service_id
    """
   
    return [
        check_id_presence(df, "service_id", weight=3.0),
        check_id_unicity(df,  "service_id", weight=3.0),
    ]

def _check_mandatory_fields(df: pd.DataFrame) -> list[CheckResult]:
    """
    Vérifie la présence des champs obligatoires de dates et de jours
    """
    return [
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
        check_format_field(df, "monday", format["monday"], "service_id", weight=1.0),
        check_format_field(df, "tuesday", format["tuesday"], "service_id", weight=1.0),
        check_format_field(df, "wednesday", format["wednesday"], "service_id", weight=1.0),
        check_format_field(df, "thursday", format["thursday"], "service_id", weight=1.0),
        check_format_field(df, "friday", format["friday"], "service_id", weight=1.0),
        check_format_field(df, "saturday", format["saturday"], "service_id", weight=1.0),
        check_format_field(df, "sunday", format["sunday"], "service_id", weight=1.0),
        check_format_field(df, "start_date", format["start_date"], "service_id", weight=1.0),
        check_format_field(df, "end_date", format["end_date"], "service_id", weight=1.0),
    ]