# webpos/integracion_con_webpos/utils.py
import frappe
from frappe import _
from frappe.utils import flt, cstr, nowdate, now_datetime

def sales_invoice_to_webpos_json(sales_invoice):
    """Convertir Sales Invoice de ERPNext a formato JSON de WebPos"""
    
    # Obtener configuración
    settings = frappe.get_single("WebPos Settings")
    
    # Determinar tipo de documento
    doc_type = "F"  # Factura
    if sales_invoice.is_return:
        doc_type = "C"  # Nota de crédito
    
    # Construir JSON según especificaciones WebPos
    webpos_json = {
        "fiscalDoc": {
            "companyLicCod": settings.company_lic_cod,
            "branchCod": (settings.branch_cod or "0000").zfill(4),  # Asegurar 4 dígitos
            "posCod": (settings.pos_cod or "001").zfill(3),        # Asegurar 3 dígitos
            "docType": doc_type,
            "docNumber": sales_invoice.name,
            "customerName": sales_invoice.customer_name[:150],  # Máximo 150 caracteres
            "customerRUC": _get_customer_tax_id(sales_invoice.customer),
            "customerType": _get_customer_type(sales_invoice.customer),  # OBLIGATORIO
            "customerAddress": _get_customer_address(sales_invoice.customer),
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

def _get_customer_tax_id(customer_name):
    """Obtener RUC del cliente"""
    customer = frappe.get_doc("Customer", customer_name)
    return customer.tax_id or customer.name

def _get_customer_type(customer_name):
    """Determinar tipo de cliente - OBLIGATORIO según spec"""
    customer = frappe.get_doc("Customer", customer_name)
    
    # Mapeo según especificación WebPos
    type_mapping = {
        "Company": "04",      # Empresa
        "Individual": "05",   # Persona natural contribuyente
        "Government": "03",   # Gobierno
    }
    
    return type_mapping.get(customer.customer_type, "07")  # Default: Consumidor final

def _get_customer_address(customer_name):
    """Obtener dirección del cliente"""
    try:
        address = frappe.get_all("Dynamic Link", 
                                filters={"link_doctype": "Customer", "link_name": customer_name, "parenttype": "Address"},
                                fields=["parent"], limit=1)
        if address:
            addr_doc = frappe.get_doc("Address", address[0].parent)
            return f"{addr_doc.address_line1}, {addr_doc.city}"[:100]
    except:
        pass
    return "Sin dirección"

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
            "code": item.item_code[:14],  # Máximo 14 caracteres
            "desc": (item.description or item.item_name)[:500],  # Máximo 500 caracteres
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
    # Esto debe ser configurado según tus reglas de negocio
    # 0=Exento, 1=7% ITBMS, 2=10% ITBMS, 3=15% ITBMS
    
    # Por defecto, asumir 7% ITBMS
    return 1

def _get_invoice_payments(sales_invoice):
    """Convertir pagos de la factura al formato WebPos"""
    payments = []
    
    for idx, payment in enumerate(sales_invoice.payments, 1):
        payment_type_mapping = {
            "Cash": "01",           # Efectivo
            "Credit Card": "02",    # Tarjeta de crédito
            "Debit Card": "03",     # Tarjeta de débito
            "Check": "04",          # Cheque
            "Bank Transfer": "05",  # Transferencia
        }
        
        webpos_payment = {
            "id": idx,
            "type": payment_type_mapping.get(payment.mode_of_payment, "05"),
            "amt": flt(payment.amount),
            "desc1": payment.mode_of_payment
        }
        
        payments.append(webpos_payment)
    
    return payments