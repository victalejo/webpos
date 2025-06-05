# webpos/hooks.py
app_name = "webpos"
app_title = "Integracion con WebPos"
app_publisher = "Victalejo"
app_description = "Modulo de facturacion electronica con webpos"
app_email = "victoralejocj@gmail.com"
app_license = "mit"

# Document Events - Interceptar facturas
doc_events = {
    "Sales Invoice": {
        "before_submit": "webpos.integracion_con_webpos.invoice_handler.before_sales_invoice_submit",
        "on_submit": "webpos.integracion_con_webpos.invoice_handler.on_sales_invoice_submit",
        "on_cancel": "webpos.integracion_con_webpos.invoice_handler.on_sales_invoice_cancel"
    }
}

# Campos personalizados para Sales Invoice
fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "name", "in", [
                    "Sales Invoice-webpos_cufe",
                    "Sales Invoice-webpos_status",
                    "Sales Invoice-webpos_auth_number",
                    "Sales Invoice-webpos_auth_date",
                    "Sales Invoice-webpos_pdf_url",
                    "Sales Invoice-webpos_xml_signed"
                ]
            ]
        ]
    }
]