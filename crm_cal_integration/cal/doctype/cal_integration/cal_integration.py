# Copyright (c) 2025, OneHash and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CalIntegration(Document):

    def before_save(self):
        if self.has_value_changed("api_key") and self.api_key and not self.secret_key:
            self.secret_key = frappe.generate_hash(length=56)
        elif not self.api_key:
            self.secret_key = ""
