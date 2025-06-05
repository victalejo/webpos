# webpos/integracion_con_webpos/webpos_client.py
import frappe
import requests
import json
from datetime import datetime
from frappe import _

class WebPosClient:
    def __init__(self):
        self.settings = frappe.get_single("WebPos Settings")
        self.base_url = self.settings.production_url if self.settings.environment == "Production" else self.settings.test_url
        self.company_lic_cod = self.settings.company_lic_cod
        self.api_key = self.settings.api_key
        self.username = self.settings.username
        self.password = self.settings.get_password("password")
        self.token = None
        
    def get_token(self):
        """Obtener token OAuth 2.0"""
        if not self.username or not self.password:
            return self._get_api_key_headers()
            
        url = f"{self.base_url}/token"
        data = {
            "username": self.username,
            "password": self.password,
            "grant_type": "password"
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        try:
            response = requests.post(url, data=data, headers=headers)
            response.raise_for_status()
            
            token_data = response.json()
            self.token = token_data.get("access_token")
            
            return {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
        except requests.exceptions.RequestException as e:
            frappe.throw(_("Error obteniendo token: {0}").format(str(e)))
    
    def _get_api_key_headers(self):
        """Headers para autenticación con API Key"""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def send_invoice(self, invoice_json):
        """Enviar factura a WebPos"""
        headers = self.get_token()
        
        # Determinar URL según método de autenticación
        if self.token:
            # OAuth
            url = f"{self.base_url}/api/fepa/v1/{'prod' if self.settings.environment == 'Production' else 'test'}/sendFileToProcess/{self.company_lic_cod}"
        else:
            # API Key
            url = f"{self.base_url}/api/fepa/ak/v1/{'prod' if self.settings.environment == 'Production' else 'test'}/sendFileToProcess/{self.company_lic_cod}/{self.api_key}"
        
        try:
            response = requests.post(url, json=invoice_json, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            frappe.throw(_("Error enviando factura a WebPos: {0}").format(str(e)))
    
    def get_invoice_result(self, cufe):
        """Obtener resultado de factura procesada"""
        headers = self.get_token()
        
        if self.token:
            url = f"{self.base_url}/api/fepa/v1/{'prod' if self.settings.environment == 'Production' else 'test'}/GetResultFe/{self.company_lic_cod}/{cufe}"
        else:
            url = f"{self.base_url}/api/fepa/ak/v1/{'prod' if self.settings.environment == 'Production' else 'test'}/GetResultFe/{self.company_lic_cod}/{self.api_key}/{cufe}"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            frappe.throw(_("Error obteniendo resultado: {0}").format(str(e)))