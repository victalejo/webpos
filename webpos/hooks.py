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

# Fixtures para instalar automáticamente
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            [
                "dt", "=", "Sales Invoice"
            ],
            [
                "fieldname", "in", [
                    "webpos_cufe",
                    "webpos_status", 
                    "webpos_auth_number",
                    "webpos_auth_date",
                    "webpos_qr_content",
                    "webpos_xml_signed"
                ]
            ]
        ]
    }
]