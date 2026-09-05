# Copyright (c) 2024, Upande Ltd and contributors
# For license information, please see license.txt
import json

import frappe
from frappe.model.document import Document


# Payment types that use the EFT child table
EFT_TYPES = ["EFT", "EFT STANBIC", "EFT NCBA"]
# Payment types that use the RTGS child table
RTGS_TYPES = ["RTGS", "RTGS NCBA", "RTGS STANBIC"]
# Payment types that use the International Payments child table
INTERNATIONAL_TYPES = [
    "International Payments",
    "International Payments USD NCBA",
    "International Payments USD STANBIC",
    "International Payments EUR",
    "International Payments RWF",
    "International Payments GBP",
    "International Payments ZAR",
    "International Payments TZS",
]
# Payment types that need bank details (EFT, RTGS, International, Local USD)
BANK_DETAIL_TYPES = EFT_TYPES + RTGS_TYPES + INTERNATIONAL_TYPES + [
    "LOCAL USD NCBA",
    "LOCAL USD STANBIC",
]


class BulkUpload(Document):
    def before_submit(self):
        if self.type in EFT_TYPES:
            if self.eft_bulk_upload_items:
                for item in self.eft_bulk_upload_items:
                    p_entry = frappe.get_doc("Payment Entry", item.payment_reference)
                    if p_entry.docstatus == 0:
                        p_entry.custom_cash_flow_period = self.cash_flow_period
                        p_entry.save()
                        p_entry.submit()

        elif self.type in RTGS_TYPES:
            if self.rtgs_bulk_upload_items:
                for item in self.rtgs_bulk_upload_items:
                    p_entry = frappe.get_doc("Payment Entry", item.payment_reference)
                    if p_entry.docstatus == 0:
                        p_entry.custom_cash_flow_period = self.cash_flow_period
                        p_entry.save()
                        p_entry.submit()

        elif self.type in INTERNATIONAL_TYPES:
            if self.international_payments_bulk_upload_items:
                for item in self.international_payments_bulk_upload_items:
                    p_entry = frappe.get_doc("Payment Entry", item.reference)
                    if p_entry.docstatus == 0:
                        p_entry.custom_cash_flow_period = self.cash_flow_period
                        p_entry.save()
                        p_entry.submit()
    
    @frappe.whitelist()        
    def get_pending_payments(self):
        pymnts_list = []
        self.mpesa_bulk_upload_items = []
        self.eft_bulk_upload_items = []
        self.rtgs_bulk_upload_items = []
        self.international_payments_bulk_upload_items = []

        # Get Payment Entry names already used in submitted Bulk Uploads
        already_used = frappe.get_all(
            "Mpesa Bulk Upload Item",
            filters={"parenttype": "Bulk Upload"},
            fields=["payment_reference"],
        )
        used_names = [item.payment_reference for item in already_used if item.payment_reference]

        draft_payments = frappe.db.get_all('Payment Entry', filters={
            'status': ['in', ['Draft']],
            'payment_type': 'Pay',
            "custom_upload_type": self.type,
            "name": ["not in", used_names] if used_names else ["like", "%%"]
        }, fields=['name', 'party', 'paid_amount', 'party_bank_account', 'custom_upload_type', 'reference_no'])
        
        if draft_payments:
            for pymnt in draft_payments:
                if pymnt.get("custom_upload_type") in BANK_DETAIL_TYPES:
                    if pymnt.get("party_bank_account"):
                        
                        bank = frappe.db.get_value("Bank Account", {"name": pymnt.get("party_bank_account")}, 'bank')
                        bank_account = frappe.db.get_value("Bank Account", {"name": pymnt.get("party_bank_account")}, 'bank_account_no')
                        swift_code = frappe.db.get_value("Bank Account", {"name": pymnt.get("party_bank_account")}, 'custom_swift_code')
                        pymnt["bank_name"] = bank
                        pymnt["bank_account"] = bank_account
                        pymnt["swift_code"] = swift_code
                        
                        if not pymnt in pymnts_list:
                            pymnts_list.append(pymnt)
                else:
                    # For Mpesa payments, create one row per beneficiary
                    beneficiaries = frappe.db.get_all(
                        "Payment Entry Beneficiary",
                        filters={
                            "parent": pymnt["name"],
                            "parenttype": "Payment Entry",
                        },
                        fields=[
                            "mobile_number",
                            "document_type",
                            "document_number",
                            "purpose_of_payment",
                            "amount",
                        ],
                    )
                    if beneficiaries:
                        for ben in beneficiaries:
                            entry = dict(pymnt)
                            entry["mobilenumber"] = ben.get("mobile_number") or ""
                            entry["documenttype"] = ben.get("document_type") or ""
                            entry["supplier_invoice"] = ben.get("document_number") or ""
                            entry["purposeofpayment"] = ben.get("purpose_of_payment") or ""
                            entry["paid_amount"] = ben.get("amount") or pymnt.get("paid_amount")
                            pymnts_list.append(entry)
                    else:
                        if not pymnt in pymnts_list:
                            pymnts_list.append(pymnt)
                        
        response_data = {
            'draft_payments': pymnts_list
        }
     
        frappe.response['message'] = response_data
        
    @frappe.whitelist()
    def download_report(self):   
        site_url = frappe.utils.get_url()      
        report_url = f"{site_url}/app/query-report/{self.get('type')} Bank Bulk Upload?parent={self.get('name')}"
        
        frappe.response['message'] = report_url
