# webpos/integracion_con_webpos/invoice_handler.py
import frappe
from frappe import _
from .webpos_client import WebPosClient
from .utils import sales_invoice_to_webpos_json

def before_sales_invoice_submit(doc, method):
    """Validaciones antes de enviar factura"""
    settings = frappe.get_single("WebPos Settings")
    
    if not settings.enabled:
        return
    
    # Validar que la configuración esté completa  
    if not settings.company_lic_cod:
        frappe.throw(_("WebPos no está configurado correctamente. Falta Company License Code."))

def on_sales_invoice_submit(doc, method):
    """Enviar factura a WebPos cuando se confirma"""
    settings = frappe.get_single("WebPos Settings")
    
    if not settings.enabled:
        return
    
    try:
        # Convertir factura a formato WebPos
        webpos_json = sales_invoice_to_webpos_json(doc)
        
        # Enviar a WebPos
        client = WebPosClient()
        response = client.send_invoice(webpos_json)
        
        # Procesar respuesta
        if response.get("accepted"):
            # Actualizar campos de la factura
            doc.db_set("webpos_cufe", response.get("cufe"))
            doc.db_set("webpos_status", "Autorizada")
            doc.db_set("webpos_auth_number", response.get("confirmationNbr"))
            doc.db_set("webpos_auth_date", response.get("dateSentToDgi"))
            
            # Crear log de transacción
            _create_transaction_log(doc.name, "Success", response)
            
            frappe.msgprint(_("Factura enviada exitosamente a WebPos. CUFE: {0}").format(response.get("cufe")))
            
        else:
            # Error en el procesamiento
            error_msg = response.get("msg", "Error desconocido")
            doc.db_set("webpos_status", "Rechazada")
            
            _create_transaction_log(doc.name, "Error", response)
            
            frappe.throw(_("Error procesando factura en WebPos: {0}").format(error_msg))
            
    except Exception as e:
        # Log del error
        _create_transaction_log(doc.name, "Error", {"error": str(e)})
        
        # Si está en modo strict, cancelar la operación
        if settings.strict_mode:
            frappe.throw(_("Error enviando factura a WebPos: {0}").format(str(e)))
        else:
            frappe.log_error(f"Error WebPos: {str(e)}", "WebPos Integration")
            frappe.msgprint(_("Error enviando factura a WebPos, pero la factura fue guardada. Revisar logs."))

def on_sales_invoice_cancel(doc, method):
    """Manejar cancelación de facturas"""
    settings = frappe.get_single("WebPos Settings")
    
    if not settings.enabled or not doc.webpos_cufe:
        return
    
    # Actualizar estado
    doc.db_set("webpos_status", "Cancelada")
    
    # Crear log
    _create_transaction_log(doc.name, "Cancelled", {"cufe": doc.webpos_cufe})

def _create_transaction_log(invoice_name, status, response_data):
    """Crear log de transacción"""
    log = frappe.get_doc({
        "doctype": "WebPos Transaction Log",
        "invoice": invoice_name,
        "status": status,
        "response_data": frappe.as_json(response_data),
        "timestamp": frappe.utils.now()
    })
    log.insert(ignore_permissions=True)