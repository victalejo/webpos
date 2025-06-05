# Copyright (c) 2025, Victalejo and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class WebPosSettings(Document):
	def validate(self):
		if self.enabled:
			if not self.company_lic_cod:
				frappe.throw("Company License Code is required when WebPos is enabled")
			
			if self.authentication_method == "OAuth":
				if not self.username or not self.password:
					frappe.throw("Username and Password are required for OAuth authentication")
			elif self.authentication_method == "API Key":
				if not self.api_key:
					frappe.throw("API Key is required for API Key authentication")