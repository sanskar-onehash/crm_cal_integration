import frappe
import json

from crm_cal_integration.cal import utils as cal_utils
from crm_cal_integration.cal.doctype.cal_booking_trigger.triggers import (
    BOOKING_TRIGGERS,
)
from crm_cal_integration.utils import verify_hmac


def fetch_event_types():
    return json.loads(cal_utils.get("/event-types").text)


def fetch_event_type(event_type_id):
    return json.loads(cal_utils.get(f"/event-types/{event_type_id}").text)


def fetch_slots_available(event_type_id, start_time=None, end_time=None):
    return json.loads(
        cal_utils.get(
            f"/slots/available?eventTypeId={event_type_id}&startTime={start_time}&endTime={end_time}"
        ).text
    )


@frappe.whitelist(allow_guest=True)
def cal_webhook():
    if not verify_hmac(
        frappe.request.get_data(),
        frappe.request.headers.get("X-Cal-Signature-256"),
        frappe.db.get_value("Cal Integration", "Cal Integration", "secret_key"),
        "sha256",
    ):
        raise frappe.AuthenticationError("Invalid or tempered payload.")

    try:
        frappe.log_error("cal webhook data", frappe.form_dict)
        data = frappe.form_dict.get("payload") or frappe.form_dict
        event_type = data.get("eventTypeId")
        trigger_id = frappe.form_dict.get("triggerEvent")

        if trigger_id not in BOOKING_TRIGGERS:
            frappe.log_error("Booking Trigger Not Found", trigger_id)
            return

        if frappe.db.exists("Cal Event Type", event_type):
            update_schedule(data, trigger_id, event_type)
        else:
            # Workaround while we don't have 'EVENT_TYPE_CREATED' webhook
            from crm_cal_integration.api import add_update_cal_event_types

            event_type_details = fetch_event_type(event_type)
            if event_type_details.get("status") == "success":
                add_update_cal_event_types(
                    [event_type_details.get("data").get("eventType")]
                )
                if frappe.db.exists("Cal Event Type", event_type):
                    update_schedule(data, trigger_id, event_type)
    except Exception as e:
        frappe.log_error("cal_webhook error", e)


def update_schedule(data, trigger_id, event_type):

    user_responses = data.get("responses")
    is_recurring = True if data.get("recurringEvent") else False

    scheduled_email = parse_response_value(user_responses.get("email"))
    scheduled_phone = parse_response_value(user_responses.get("phone"))
    schedule_doc = get_schedule_doc(event_type, scheduled_email)

    reschedule_reason = (
        parse_response_value(user_responses.get("rescheduleReason"))
        if user_responses.get("rescheduleReason")
        else None
    )

    # We don't need repetitive event calls
    if is_recurring and schedule_doc.booking_status == trigger_id:
        return

    if data.get("userFieldsResponses"):
        user_responses = json.loads(schedule_doc.user_responses or "[]")
        user_responses.append(data.get("userFieldsResponses"))
        schedule_doc.user_responses = json.dumps(user_responses)
    if schedule_doc.scheduled_with != scheduled_email:
        schedule_doc.booking_email = scheduled_email

    schedule_doc.update(
        {
            "is_recurring": is_recurring,
            "booking_status": trigger_id,
            "booking_id": data.get("bookingId"),
            "booking_uid": data.get("uid"),
            "booking_phone": scheduled_phone,
            "location": data.get("location"),
            "additional_notes": data.get("additionalNotes"),
            "reschedule_reason": reschedule_reason,
            "cancellation_reason": data.get("cancellationReason"),
        }
    )
    if data.get("attendees") and len(data.get("attendees")):
        schedule_doc.meeting_attendees = []
        for attendee in data.get("attendees"):
            schedule_doc.append(
                "meeting_attendees",
                {
                    "attendee_name": attendee.get("name"),
                    "email": attendee.get("email"),
                    "phone_number": attendee.get("phoneNumber"),
                },
            )
    schedule_doc.append(
        "event_timeline",
        {
            "booking_id": data.get("bookingId"),
            "booking_trigger_id": trigger_id,
            "booking_email": scheduled_email,
            "booking_phone": scheduled_phone,
            "event_time": cal_utils.normalize_datetime(data.get("createdAt")),
            "start_time": cal_utils.normalize_datetime(data.get("startTime")),
            "end_time": cal_utils.normalize_datetime(data.get("endTime")),
            "location": data.get("location"),
            "additional_notes": data.get("additionalNotes"),
            "reschedule_reason": reschedule_reason,
            "cancellation_reason": data.get("cancellationReason"),
        },
    )
    schedule_doc = schedule_doc.save(ignore_permissions=True)
    frappe.db.commit()


def parse_response_value(field):
    if isinstance(field, dict):
        return field.get("value")
    else:
        return field


def get_schedule_doc(event_type, scheduled_with):
    event_schedule_dt = frappe.qb.DocType("Cal Schedule")
    existing_schedules = (
        frappe.qb.from_(event_schedule_dt)
        .select("name")
        .where(
            (event_schedule_dt.event_type == event_type)
            & (
                (event_schedule_dt.scheduled_with == scheduled_with)
                | (event_schedule_dt.booking_email == scheduled_with)
            )
        )
        .limit(1)
    ).run()

    if len(existing_schedules):
        return frappe.get_doc("Cal Schedule", existing_schedules[0][0])
    else:
        doc = frappe.new_doc("Cal Schedule")
        doc.update({"scheduled_with": scheduled_with, "event_type": event_type})
        return doc
