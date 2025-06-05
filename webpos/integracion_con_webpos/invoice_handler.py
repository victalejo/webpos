# webpos/integracion_con_webpos/invoice_handler.py
import frappe
from frappe import _
from .webpos_client import WebPosClient
from .utils import sales_invoice_to_webpos_json
import json

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
        
        # Log del JSON que vamos a enviar (para debug)
        frappe.log_error(f"JSON enviado a WebPos: {json.dumps(webpos_json, indent=2)}", "WebPos JSON Debug")
        
        # Enviar a WebPos
        client = WebPosClient()
        response = client.send_invoice(webpos_json)
        
        # Log de la respuesta completa (para debug)
        frappe.log_error(f"Respuesta completa de WebPos: {json.dumps(response, indent=2)}", "WebPos Response Debug")
        
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
            # Error en el procesamiento - Obtener información detallada
            error_msg = response.get("msg", "Error desconocido")
            dgi_response = response.get("dgiResp", "")
            
            # Crear mensaje de error detallado
            error_details = [f"Error: {error_msg}"]
            
            if dgi_response:
                try:
                    # Si dgiResp es un JSON string, parsearlo
                    if isinstance(dgi_response, str):
                        dgi_data = json.loads(dgi_response)
                    else:
                        dgi_data = dgi_response
                    
                    # Extraer mensajes de error específicos
                    if "gInfProt" in dgi_data and "gResProc" in dgi_data["gInfProt"]:
                        for res in dgi_data["gInfProt"]["gResProc"]:
                            if "dMsgRes" in res:
                                error_details.append(f"DGI: {res['dMsgRes']}")
                    
                except:
                    error_details.append(f"DGI Response: {dgi_response}")
            
            # Agregar información adicional de la respuesta
            if response.get("received") == False:
                error_details.append("La factura no fue recibida por WebPos")
            
            if response.get("sentToDgi") == False:
                error_details.append("La factura no fue enviada a DGI")
            
            detailed_error = "\n".join(error_details)
            
            doc.db_set("webpos_status", "Rechazada")
            
            _create_transaction_log(doc.name, "Error", response)
            
            frappe.throw(_("Error procesando factura en WebPos:\n{0}").format(detailed_error))
            
    except Exception as e:
        # Log del error completo
        frappe.log_error(f"Error completo en WebPos: {frappe.get_traceback()}", "WebPos Integration Error")
        
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
    try:
        log = frappe.get_doc({
            "doctype": "WebPos Transaction Log",
            "invoice": invoice_name,
            "status": status,
            "response_data": frappe.as_json(response_data),
            "timestamp": frappe.utils.now(),
            "cufe": response_data.get("cufe", "") if isinstance(response_data, dict) else ""
        })
        log.insert(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(f"Error creating transaction log: {str(e)}", "WebPos Transaction Log Error")