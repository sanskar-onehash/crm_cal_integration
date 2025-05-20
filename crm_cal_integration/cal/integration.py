import json

from crm_cal_integration.cal import utils


def fetch_event_types():
    return json.loads(utils.get("/event-types").text)


def fetch_slots_available(event_type_id, start_time=None, end_time=None):
    return json.loads(
        utils.get(
            f"/slots/available?eventTypeId={event_type_id}&startTime={start_time}&endTime={end_time}"
        ).text
    )
