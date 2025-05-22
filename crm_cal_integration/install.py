import frappe


def after_install():
    add_event_triggers()


def add_event_triggers():
    from crm_cal_integration.cal.doctype.cal_booking_trigger.triggers import (
        BOOKING_TRIGGERS,
    )

    for trigger in BOOKING_TRIGGERS:
        frappe.get_doc(
            {
                "doctype": "Cal Booking Trigger",
                "trigger_id": trigger,
                "trigger_name": BOOKING_TRIGGERS.get(trigger),
            }
        ).save()
    frappe.db.commit()
