# webpos/integracion_con_webpos/test_connection.py
import frappe
from .webpos_client import WebPosClient
import json

@frappe.whitelist()
def test_webpos_connection():
    """Función para probar la conexión con WebPos"""
    try:
        settings = frappe.get_single("WebPos Settings")
        
        if not settings.enabled:
            return {"success": False, "message": "WebPos no está habilitado"}
        
        client = WebPosClient()
        
        # Intentar obtener token
        headers = client.get_token()
        
        return {
            "success": True, 
            "message": "Conexión exitosa",
            "environment": settings.environment,
            "company_lic_cod": settings.company_lic_cod,
            "auth_method": settings.authentication_method
        }
        
    except Exception as e:
        return {
            "success": False, 
            "message": f"Error de conexión: {str(e)}"
        }

@frappe.whitelist()
def get_last_webpos_logs():
    """Obtener los últimos logs de WebPos"""
    logs = frappe.get_all("Error Log", 
        filters={"error": ("like", "%WebPos%")},
        fields=["name", "creation", "error"],
        order_by="creation desc",
        limit=5
    )
    
    return logs