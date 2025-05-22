import frappe
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


@frappe.whitelist(allow_guest=True)
def cal_webhook():
    try:
        data = frappe.form_dict.get("payload")
        trigger_event = frappe.form_dict.get("triggerEvent")

        event_type = data.get("eventTypeId")
        user_responses = data.get("responses")
        scheduled_with = user_responses.get("email").get("value")

        frappe.log_error(
            "GOt",
            {
                "data": data,
                "trigger_event": trigger_event,
                "event_type": event_type,
                "user_responses": user_responses,
                "scheduled_with": scheduled_with,
            },
        )
        if frappe.db.exists("Cal Event Type", event_type):
            schedule_doc = get_schedule_doc(event_type, scheduled_with)

            if schedule_doc.scheduled_with != scheduled_with:
                schedule_doc.booked_email = scheduled_with
            schedule_doc.update(
                {
                    location: data.get("location"),
                    additional_notes: data.get("additionalNotes"),
                    reschedule_reason: user_responses.get("rescheduleReason"),
                }
            )
            if data.get("attendees") and len(data.get("attendees")):
                schedule_doc.meeting_attendees = [
                    {
                        "attendee_name": attendee.get("name"),
                        "email": attendee.get("email"),
                        "phone_number": attendee.get("phoneNumber"),
                    }
                    for attendee in data.get("attendees")
                ]
            schedule_doc.append(
                "event_timeline",
                {
                    "booking_trigger_id": trigger_event,
                    "event_time": data.get("createdAt"),
                    "start_time": data.get("startTime"),
                    "end_time": data.get("endTime"),
                    "location": data.get("location"),
                    "additional_notes": data.get("additionalNotes"),
                    "reschedule_reason": user_responses.get("rescheduleReason"),
                },
            )
            schedule_doc.save(ignore_permission=True)
        else:
            frappe.log_error("else", event_type)
    except Exception as e:
        frappe.log_error("cal_webhook error", e)


def get_schedule_doc(event_type, scheduled_with):
    event_schedule_dt = frappe.qb.DocType("Cal Schedule")
    existing_schedules = (
        frappe.qb.from_(event_schedule_dt)
        .select("name")
        .where(
            (event_schedule_dt.event_type == event_type)
            & (
                (
                    event_schedule_dt.scheduled_with
                    == scheduled_with | event_schedule_dt.booked_email
                    == scheduled_with
                )
            )
        )
        .limit()
    ).run()

    if len(existing_schedules):
        return frappe.get_doc("Cal Schedule", existing_schedules[0])
    else:
        return frappe.new_doc("Cal Schedule")
