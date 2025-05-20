import frappe
import crm_cal_integration.cal.integration as cal

API_UPDATE_THRESHOLD = 20


@frappe.whitelist()
def pull_cal_event_types():
    event_types_res = cal.fetch_event_types()
    status = event_types_res.get("status")
    message = "Cal Event Types updated successfully."

    if status == "success":
        for event_type_group in event_types_res.get("data").get("eventTypeGroups"):
            event_types_res = event_type_group.get("eventTypes")
            if len(event_types_res) > API_UPDATE_THRESHOLD:
                frappe.enqueue(add_update_cal_event_types, event_types=event_types_res)
                message = "Cal Event Types are updating in background."
            else:
                add_update_cal_event_types(event_types_res)
    else:
        message = f"Error occured while fetching Cal Event Types: {event_types_res.get('error').get('message')}"
        frappe.log_error("Cal: pull_cal_event_types", event_types_res)
    return {"status": status, "message": message}


@frappe.whitelist()
def fetch_cal_slots_available(event_type_id, start_time=None, end_time=None):
    slots_availble_res = cal.fetch_slots_available(event_type_id, start_time, end_time)
    status = slots_availble_res.get("status")
    if status == "success":
        data = slots_availble_res.get("slots")
        return {
            "status": status,
            "message": "Cal available slots fetched successfully.",
            "data": data,
        }
    else:
        frappe.log_error("Cal: fetch_cal_slots_available", slots_availble_res)
        return {
            "status": status,
            "message": f"Error occured while fetching available slots from Cal: {slots_availble_res.get('error').get('message')}",
        }


def add_update_cal_event_types(event_types):
    for event_type in event_types:
        updates = {
            "title": event_type.get("title"),
            "slug": event_type.get("slug"),
            "length": event_type.get("length"),
            "description": event_type.get("description"),
            "locations": [],
        }
        for location in event_type.get("locations"):
            updates["locations"].append(
                {
                    "type": location.get("type"),
                    "link": location.get("link"),
                    "address": location.get("address"),
                }
            )

        if frappe.db.exists("Cal Event Type", event_type.get("id")):
            doc = frappe.get_doc("Cal Event Type", event_type.get("id"))
            doc.update(updates)
        else:
            updates["id"] = event_type.get("id")
            doc = frappe.new_doc(doctype="Cal Event Type", **updates)
        doc.save()

        frappe.db.commit()
