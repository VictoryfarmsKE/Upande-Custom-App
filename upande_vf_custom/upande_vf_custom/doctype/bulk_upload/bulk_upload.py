# Copyright (c) 2024, Upande Ltd and contributors
# For license information, please see license.txt
import json

import frappe
from frappe.model.document import Document


class BulkUpload(Document):
    def before_submit(self):
        if self.type == "EFT":
            if self.eft_bulk_upload_items:
                for item in self.eft_bulk_upload_items:
                    p_entry = frappe.get_doc("Payment Entry", item.payment_reference)
                    if p_entry.docstatus==0:
                        p_entry.custom_cash_flow_period = self.cash_flow_period

                        p_entry.save()
                        p_entry.submit()
                        
        elif self.type == "RTGS NCBA":
            if self.rtgs_ncba_bulk_upload_items:
                for item in self.rtgs_ncba_bulk_upload_items:
                    p_entry = frappe.get_doc("Payment Entry", item.payment_reference)
                    if p_entry.docstatus==0:
                        p_entry.custom_cash_flow_period = self.cash_flow_period

                        p_entry.save()
                        p_entry.submit()
                        
        elif self.type == "RTGS STANBIC BANK":
            if self.rtgs_stanbic_bulk_upload_items:
                for item in self.rtgs_stanbic_bulk_upload_items:
                    p_entry = frappe.get_doc("Payment Entry", item.payment_reference)
                    if p_entry.docstatus==0:
                        p_entry.custom_cash_flow_period = self.cash_flow_period

                        p_entry.save()
                        p_entry.submit()
                        
        # elif self.type == "RTGS":
        #     if self.rtgs_bulk_upload_items:
        #         for item in self.rtgs_bulk_upload_items:
        #             p_entry = frappe.get_doc("Payment Entry", item.payment_reference)
        #             if p_entry.docstatus==0:
        #                 p_entry.custom_cash_flow_period = self.cash_flow_period

        #                 p_entry.save()
        #                 p_entry.submit()
        
        # elif self.type == 'International Payments':
        #     if self.international_payments_bulk_upload_items:
        #         for item in self.international_payments_bulk_upload_items:
        #             p_entry = frappe.get_doc("Payment Entry", item.reference)
        #             if p_entry.docstatus==0:
        #                 p_entry.custom_cash_flow_period = self.cash_flow_period

        #                 p_entry.save()
        #                 p_entry.submit()
                        
        elif self.type == 'International Payments USD':
            if self.international_payments_bulk_upload_items:
                for item in self.international_payments_bulk_upload_items:
                    p_entry = frappe.get_doc("Payment Entry", item.reference)
                    if p_entry.docstatus==0:
                        p_entry.custom_cash_flow_period = self.cash_flow_period

                        p_entry.save()
                        p_entry.submit()
                        
        elif self.type == 'International Payments ZAR':
            if self.international_payments_zar_bulk_upload_items:
                for item in self.international_payments_zar_bulk_upload_items:
                    p_entry = frappe.get_doc("Payment Entry", item.reference)
                    if p_entry.docstatus==0:
                        p_entry.custom_cash_flow_period = self.cash_flow_period

                        p_entry.save()
                        p_entry.submit()
                        
        elif self.type == 'International Payments EUR':
            if self.international_payments_eur_bulk_upload_items:
                for item in self.international_payments_eur_bulk_upload_items:
                    p_entry = frappe.get_doc("Payment Entry", item.reference)
                    if p_entry.docstatus==0:
                        p_entry.custom_cash_flow_period = self.cash_flow_period

                        p_entry.save()
                        p_entry.submit()
                        
        elif self.type == 'International Payments GBP':
            if self.international_payments_gbp_bulk_upload_items:
                for item in self.international_payments_gbp_bulk_upload_items:
                    p_entry = frappe.get_doc("Payment Entry", item.reference)
                    if p_entry.docstatus==0:
                        p_entry.custom_cash_flow_period = self.cash_flow_period

                        p_entry.save()
                        p_entry.submit()
                        
        elif self.type == 'International Payments RWF':
            if self.international_payments_rwf_bulk_upload_items:
                for item in self.international_payments_rwf_bulk_upload_items:
                    p_entry = frappe.get_doc("Payment Entry", item.reference)
                    if p_entry.docstatus==0:
                        p_entry.custom_cash_flow_period = self.cash_flow_period

                        p_entry.save()
                        p_entry.submit()
    
    @frappe.whitelist()        
    def get_pending_payments(self):
        pymnts_list = []
        self.mpesa_bulk_upload_items = []
        self.eft_bulk_upload_items = []
        # self.rtgs_bulk_upload_items = []
        self.rtgs_ncba_bulk_upload_items = []
        self.rtgs_stanbic_bulk_upload_items = []
        # self.international_payments_usd_bulk_upload_items = []
        self.international_payments_zar_bulk_upload_items = []
        self.international_payments_eur_bulk_upload_items = []
        self.international_payments_gbp_bulk_upload_items = []
        self.international_payments_rwf_bulk_upload_items = []
        self.international_payments_bulk_upload_items = []

        draft_payments = frappe.db.get_all('Payment Entry', filters={
            'status': ['in', 'Draft'],
            'payment_type': 'Pay',
            "custom_upload_type": self.type
        }, fields=['name', 'party', 'paid_amount', 'party_bank_account', 'custom_upload_type', 'reference_no'])
        
        total_grand_total = 0
        
        if draft_payments:
            for pymnt in draft_payments:
                # if pymnt.get("custom_upload_type") in ["EFT", "RTGS", "International Payments"]:
                if pymnt.get("custom_upload_type") in ["EFT", "RTGS NCBA", "RTGS STANBIC BANK", "International Payments USD", "International Payments ZAR", "International Payments EUR", "International Payments GBP", "International Payments RWF"]:
                    if pymnt.get("party_bank_account"):
                        
                        bank = frappe.db.get_value("Bank Account", {"name": pymnt.get("party_bank_account")}, 'bank')
                        bank_account = frappe.db.get_value("Bank Account", {"name": pymnt.get("party_bank_account")}, 'bank_account_no')
                        swift_code = frappe.db.get_value("Bank Account", {"name": pymnt.get("party_bank_account")}, 'custom_swift_code')
                        pymnt["bank_name"] = bank
                        pymnt["bank_account"] = bank_account
                        pymnt["swift_code"] = swift_code
                        
                        if not pymnt in pymnts_list:
                            pymnts_list.append(pymnt)
                            total_grand_total += pymnt.get("paid_amount", 0)
                else:
                   if not pymnt in pymnts_list:
                        pymnts_list.append(pymnt) 
                        total_grand_total += pymnt.get("paid_amount", 0)
                        
        response_data = {
            'draft_payments': pymnts_list,
            'total_grand_total': total_grand_total,
        }
     
        frappe.response['message'] = response_data
        
    @frappe.whitelist()
    def download_report(self):   
        site_url = frappe.utils.get_url()      
        report_url = f"{site_url}/app/query-report/{self.get('type')} Bank Bulk Upload?parent={self.get('name')}"
        
        frappe.response['message'] = report_url







                        