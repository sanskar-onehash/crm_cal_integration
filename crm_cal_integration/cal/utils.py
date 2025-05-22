import requests

from frappe.utils import dateutils as dt
from frappe.utils.password import get_decrypted_password
from crm_cal_integration.cal.config import API_URL


def get_api_key():
    return get_decrypted_password("Cal Integration", "Cal Integration", "api_key")


def get_api_url(route="/"):
    return f"{API_URL}{route}"


def get_header():
    return {"Authorization": get_api_key()}


def get(route="/"):
    return requests.get(get_api_url(route), headers=get_header())


def normalize_datetime(datetime_str):
    return dt.get_datetime(datetime_str).replace(tzinfo=None)
