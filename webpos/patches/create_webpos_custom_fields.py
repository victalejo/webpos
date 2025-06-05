# webpos/patches/create_webpos_custom_fields.py
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    """Create custom fields for WebPos integration"""
    
    custom_fields = {
        "Sales Invoice": [
            {
                "fieldname": "webpos_cufe",
                "fieldtype": "Data",
                "label": "WebPos CUFE",
                "description": "Código Único de Factura Electrónica de WebPos",
                "insert_after": "tax_id",
                "read_only": 1,
                "no_copy": 1,
                "allow_on_submit": 1,
                "length": 100
            },
            {
                "fieldname": "webpos_status", 
                "fieldtype": "Select",
                "label": "WebPos Status",
                "description": "Estado de la factura en WebPos",
                "options": "Pendiente\nAutorizada\nRechazada\nCancelada",
                "insert_after": "webpos_cufe",
                "read_only": 1,
                "no_copy": 1,
                "allow_on_submit": 1,
                "in_list_view": 1,
                "in_standard_filter": 1
            },
            {
                "fieldname": "webpos_auth_number",
                "fieldtype": "Data", 
                "label": "WebPos Auth Number",
                "description": "Número de autorización de WebPos",
                "insert_after": "webpos_status",
                "read_only": 1,
                "no_copy": 1,
                "allow_on_submit": 1,
                "length": 50
            },
            {
                "fieldname": "webpos_auth_date",
                "fieldtype": "Datetime",
                "label": "WebPos Auth Date", 
                "description": "Fecha de autorización de WebPos",
                "insert_after": "webpos_auth_number",
                "read_only": 1,
                "no_copy": 1,
                "allow_on_submit": 1
            },
            {
                "fieldname": "webpos_qr_content",
                "fieldtype": "Small Text",
                "label": "WebPos QR Content",
                "description": "Contenido del código QR",
                "insert_after": "webpos_auth_date", 
                "read_only": 1,
                "no_copy": 1,
                "allow_on_submit": 1
            },
            {
                "fieldname": "webpos_xml_signed",
                "fieldtype": "Long Text",
                "label": "WebPos XML Signed",
                "description": "XML firmado de la factura electrónica",
                "insert_after": "webpos_qr_content",
                "read_only": 1,
                "no_copy": 1,
                "allow_on_submit": 1,
                "hidden": 1,
                "print_hide": 1,
                "report_hide": 1
            }
        ]
    }
    
    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()