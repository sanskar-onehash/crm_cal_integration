import frappe


def after_install():
    add_event_triggers()


def add_event_triggers():
    from crm_cal_integration.cal.doctype.cal_booking_trigger.triggers import triggers

    for trigger in triggers:
        frappe.get_doc(
            {
                "doctype": "Cal Booking Trigger",
                "trigger_id": trigger.upper().replace(" ", "_"),
                "trigger_name": trigger,
            }
        ).save()
    frappe.db.commit()
