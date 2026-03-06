"""Audit functions for agency.txt: mandatory fields, format validation and cross-file consistency."""
import pandas as pd
from audit_models import CheckResult
from audit_generic_functions import check_id_presence, check_id_unicity, check_field_presence, check_format_field, check_orphan_ids, check_unused_ids
import pytz
import re


format_config = {'agency_timezone':{'genre':'required','description':"Validité des fuseaux horaires", 'type':'listing', 'valid_fields':set(pytz.all_timezones)},
          'agency_lang':{'genre':'optional','description':"Validité des langues", 'type':'listing','valid_fields':{'en', 'fr', 'es', 'de', 'it', 'pt', 'nl', 'sv', 'da', 'no', 'fi', 'ru', 'zh', 'ja', 'ko', 'ar','EN', 'FR', 'ES', 'DE', 'IT', 'PT', 'NL', 'SV', 'DA', 'NO', 'FI', 'RU', 'ZH', 'JA', 'KO', 'AR'}},
          'agency_url':{'genre':'required','description':"Validité des URL",'type':'url'},
          'agency_fare_url':{'genre':'optional','description':"Validité des URL de tarif",'type':'url'},
          'agency_phone':{'genre':'optional','description':"Validité des numéros de téléphone",'type':'regex','pattern':re.compile(r'^[\+]?[\s\-\(\)0-9]{8,}$')},
          'agency_email':{'genre':'optional','description':"Validity des mails",'type':'regex','pattern':re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')}
}


def _check_mandatory_fields(df: pd.DataFrame) -> list[CheckResult]:
    """
    Checks presence and unicity of mandatory agency fields.
    agency_id checks are skipped if the file contains a single agency.

    :param df: agency.txt DataFrame.
    """
    checks = [
        check_field_presence(df, "agency_name",     "agency_id", weight=1.0),
        check_field_presence(df, "agency_url",      "agency_id", weight=1.0),
        check_field_presence(df, "agency_timezone", "agency_id", weight=1.0),
    ]
    if len(df) <= 1:
        checks.append(CheckResult(check_id = "agency.mandatory.agency_id_presence", label = "Présence du champ agency_id", category = "mandatory", status = "skip", weight = 3.0, message  = "agency_id optionnel (une seule agence)"))
        checks.append(CheckResult(check_id = "agency.mandatory.agency_id_unicity", label = "Unicité des agency_id", category = "mandatory", status = "skip", weight = 3.0, message = "agency_id optionnel (une seule agence)"))
    else:
        checks.append(check_id_presence(df, "agency_id", weight=3.0))
        checks.append(check_id_unicity(df,  "agency_id", weight=3.0))
    return checks
 

def _check_data_format(df: pd.DataFrame) -> list[CheckResult]:
    """
    Checks format validity of all agency fields against format_config.

    :param df: agency.txt DataFrame.
    """
    return [
        check_format_field(df, "agency_lang",     format_config["agency_lang"],     "agency_id", weight=1.0),
        check_format_field(df, "agency_phone",    format_config["agency_phone"],    "agency_id", weight=1.0),
        check_format_field(df, "agency_fare_url", format_config["agency_fare_url"], "agency_id", weight=1.0),
        check_format_field(df, "agency_email",    format_config["agency_email"],    "agency_id", weight=1.0),
        check_format_field(df, "agency_timezone", format_config["agency_timezone"], "agency_id", weight=1.0),
        check_format_field(df, "agency_url",      format_config["agency_url"],      "agency_id", weight=1.0),
    ]


def _check_data_consistency(df: pd.DataFrame, routes_df: pd.DataFrame) -> list[CheckResult]:
    """
    Checks agency_id cross-file consistency: orphan and unused IDs against routes.txt.

    :param df: agency.txt DataFrame.
    :param routes_df: routes.txt DataFrame.
    """
    return [
        check_orphan_ids(df, "agency_id", routes_df, "agency_id", weight=2.0),
        check_unused_ids(df, "agency_id", routes_df, "agency_id", weight=2.0),
    ]