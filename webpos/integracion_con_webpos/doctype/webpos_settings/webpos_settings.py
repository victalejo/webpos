# Copyright (c) 2025, Victalejo and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class WebPosSettings(Document):
	def validate(self):
		if self.enabled:
			if not self.company_lic_cod:
				frappe.throw("Company License Code es requerido")
			
			if not self.branch_cod or len(self.branch_cod) > 4:
				frappe.throw("Branch Code debe tener máximo 4 dígitos")
				
			if not self.pos_cod or len(self.pos_cod) > 3:
				frappe.throw("POS Code debe tener máximo 3 dígitos")
			
			if self.authentication_method == "OAuth":
				if not self.username or not self.password:
					frappe.throw("Username y Password son requeridos para OAuth")
			elif self.authentication_method == "API Key":
				if not self.api_key:
					frappe.throw("API Key es requerido")