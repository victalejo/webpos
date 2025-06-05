# webpos/integracion_con_webpos/utils.py
import frappe
from frappe import _
from frappe.utils import flt, cstr, nowdate, now_datetime
import re

def sales_invoice_to_webpos_json(sales_invoice):
    """Convertir Sales Invoice de ERPNext a formato JSON de WebPos"""
    
    # Obtener configuración
    settings = frappe.get_single("WebPos Settings")
    
    # Determinar tipo de documento
    doc_type = "F"  # Factura
    if sales_invoice.is_return:
        doc_type = "C"  # Nota de crédito
    
    # Obtener RUC del cliente según configuración
    customer_ruc = _get_customer_ruc(sales_invoice.customer, settings)
    
    # Construir JSON según especificaciones WebPos
    webpos_json = {
        "fiscalDoc": {
            "companyLicCod": settings.company_lic_cod,
            "branchCod": (settings.branch_cod or "0000").zfill(4),
            "posCod": (settings.pos_cod or "001").zfill(3),
            "docType": doc_type,
            "docNumber": sales_invoice.name,
            "customerName": sales_invoice.customer_name[:150],
            "customerRUC": customer_ruc,
            "customerType": _get_customer_type(sales_invoice.customer),
            "customerAddress": _get_customer_address(sales_invoice.customer, settings),
            "email": _get_customer_email(sales_invoice.customer),
            "items": _get_invoice_items(sales_invoice)
        }
    }
    
    # Agregar pagos si existen
    if sales_invoice.payments:
        webpos_json["fiscalDoc"]["payments"] = _get_invoice_payments(sales_invoice)
    
    # Para notas de crédito/débito
    if sales_invoice.is_return and sales_invoice.return_against:
        webpos_json["fiscalDoc"]["invoiceNumber"] = sales_invoice.return_against
    
    return webpos_json

def _get_customer_ruc(customer_name, settings):
    """Obtener RUC del cliente según configuración"""
    customer = frappe.get_doc("Customer", customer_name)
    
    # Obtener el campo configurado para el RUC
    ruc_field = settings.customer_ruc_field or "tax_id"
    ruc_value = None
    
    # Intentar obtener el RUC del campo configurado
    if hasattr(customer, ruc_field) and getattr(customer, ruc_field):
        ruc_value = str(getattr(customer, ruc_field)).strip()
    
    # Si no hay RUC y es requerido, lanzar error
    if not ruc_value and settings.require_customer_ruc:
        frappe.throw(_(f"Cliente {customer_name} no tiene RUC configurado en el campo {ruc_field}"))
    
    # Si no hay RUC, usar el por defecto de configuración
    if not ruc_value:
        ruc_value = settings.default_ruc_for_testing or "123456-1-123456"
        frappe.log_error(
            f"Cliente {customer_name} sin RUC, usando RUC por defecto: {ruc_value}", 
            "WebPos Default RUC Used"
        )
    
    # Validar y limpiar formato
    return _clean_and_validate_ruc(ruc_value)

def _clean_and_validate_ruc(ruc_value):
    """Limpiar y validar formato del RUC panameño"""
    if not ruc_value:
        return "123456-1-123456"
    
    # Limpiar espacios
    ruc_clean = str(ruc_value).strip()
    
    # Validar formato básico del RUC panameño: NNNNNN-N-NNNNNN
    ruc_pattern = r'^\d{4,8}-\d{1}-\d{4,6}$'
    
    if re.match(ruc_pattern, ruc_clean):
        return ruc_clean
    
    # Si no coincide, intentar construir uno válido
    digits_only = re.sub(r'[^\d]', '', ruc_clean)
    
    if len(digits_only) >= 8:
        return f"{digits_only[:6]}-1-{digits_only[6:12].ljust(6, '0')}"
    else:
        frappe.log_error(f"RUC inválido: {ruc_value}", "WebPos RUC Invalid")
        return "123456-1-123456"

def _get_customer_address(customer_name, settings):
    """Obtener dirección del cliente"""
    try:
        address = frappe.get_all("Dynamic Link", 
                                filters={"link_doctype": "Customer", "link_name": customer_name, "parenttype": "Address"},
                                fields=["parent"], limit=1)
        if address:
            addr_doc = frappe.get_doc("Address", address[0].parent)
            address_line = f"{addr_doc.address_line1 or ''}"
            if addr_doc.city:
                address_line += f", {addr_doc.city}"
            if address_line.strip():
                return address_line[:100]
    except:
        pass
    
    # Usar dirección por defecto de configuración
    return settings.default_customer_address or "Panamá, Panamá"

def _get_customer_type(customer_name):
    """Determinar tipo de cliente"""
    customer = frappe.get_doc("Customer", customer_name)
    
    type_mapping = {
        "Company": "04",      # Empresa
        "Individual": "05",   # Persona natural contribuyente
        "Government": "03",   # Gobierno
    }
    
    return type_mapping.get(customer.customer_type, "07")  # Default: Consumidor final

def _get_customer_email(customer_name):
    """Obtener email del cliente"""
    customer = frappe.get_doc("Customer", customer_name)
    return customer.email_id or ""

def _get_invoice_items(sales_invoice):
    """Convertir items según especificación WebPos"""
    items = []
    
    for idx, item in enumerate(sales_invoice.items, 1):
        webpos_item = {
            "id": idx,
            "qty": flt(item.qty),
            "code": item.item_code[:14],
            "desc": (item.description or item.item_name)[:500],
            "price": flt(item.rate),
            "tax": _get_tax_type(item),
            "comments": item.item_name[:250] if item.item_name != item.description else ""
        }
        
        # Manejar descuentos
        if item.discount_percentage:
            webpos_item["dperc"] = f"{flt(item.discount_percentage)}%"
        elif item.discount_amount:
            webpos_item["damt"] = flt(item.discount_amount)
        
        items.append(webpos_item)
    
    return items

def _get_tax_type(item):
    """Determinar tipo de impuesto según las reglas de Panamá"""
    return 1  # Por defecto 7% ITBMS

def _get_invoice_payments(sales_invoice):
    """Convertir pagos de la factura al formato WebPos"""
    payments = []
    
    for idx, payment in enumerate(sales_invoice.payments, 1):
        payment_type_mapping = {
            "Cash": "01",
            "Credit Card": "02",
            "Debit Card": "03", 
            "Check": "04",
            "Bank Transfer": "05",
        }
        
        webpos_payment = {
            "id": idx,
            "type": payment_type_mapping.get(payment.mode_of_payment, "05"),
            "amt": flt(payment.amount),
            "desc1": payment.mode_of_payment
        }
        
        payments.append(webpos_payment)
    
    return payments