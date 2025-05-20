# Copyright (c) 2025, OneHash and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder import Field
from frappe.utils import dateutils as dt
from frappe.model.document import Document


class CalSchedule(Document):
    def before_insert(self):
        cal_schedule = frappe.qb.DocType("Cal Schedule")
        existing_schedules = (
            frappe.qb.from_(cal_schedule)
            .select(cal_schedule.name)
            .where(
                (cal_schedule.event_type == self.event_type)
                & (
                    (cal_schedule.event_time >= dt.get_datetime())
                    | (Field("event_time").isnull())
                )
                & (
                    (cal_schedule.scheduled_with == self.scheduled_with)
                    | (cal_schedule.booked_email == self.scheduled_with)
                )
            )
        ).run()
        if len(existing_schedules):
            raise Exception(
                f"{self.doctype} already exists for: `{self.scheduled_with}` for event type: {frappe.db.get_value('Cal Event Type', self.event_type, 'title')}."
            )
