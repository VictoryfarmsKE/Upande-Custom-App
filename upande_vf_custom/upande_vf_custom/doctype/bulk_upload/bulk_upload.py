# Copyright (c) 2024, Upande Ltd and contributors
# For license information, please see license.txt
import json

import frappe
from frappe.model.document import Document


class BulkUpload(Document):
    def before_submit(self):
        if self.type == "EFT NCBA":
            if self.eft_ncba_bulk_upload_items:
                for item in self.eft_ncba_bulk_upload_items:
                    p_entry = frappe.get_doc("Payment Entry", item.payment_reference)
                    if p_entry.docstatus==0:
                        p_entry.custom_cash_flow_period = self.cash_flow_period

                        p_entry.save()
                        p_entry.submit()
                        
        elif self.type == "EFT STANBIC BANK":
            if self.eft_stanbic_bulk_upload_items:
                for item in self.eft_stanbic_bulk_upload_items:
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

        elif self.type == "Mpesa":
            if self.mpesa_bulk_upload_items:
                for item in self.mpesa_bulk_upload_items:
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
        elif self.type == 'Local Payments USD':
            if self.local_payments_usd_bulk_upload_items:
                for item in self.local_payments_usd_bulk_upload_items:
                    p_entry = frappe.get_doc("Payment Entry", item.reference)
                    if p_entry.docstatus==0:
                        p_entry.custom_cash_flow_period = self.cash_flow_period

                        p_entry.save()
                        p_entry.submit()
                        
        elif self.type == 'International Payments USD':
            if self.international_payments_usd_bulk_upload_items:
                for item in self.international_payments_usd_bulk_upload_items:
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

        # Query the database directly for existing child table rows
        # so we always get the latest saved state
        existing_refs = set()
        if self.type == "Mpesa":
            existing_rows = frappe.get_all(
                "Mpesa Bulk Upload Item",
                filters={"parent": self.name, "parenttype": "Bulk Upload"},
                fields=["payment_reference"]
            )
            existing_refs = set(r.payment_reference for r in existing_rows if r.payment_reference)
        elif self.type == "EFT NCBA":
            existing_rows = frappe.get_all(
                "EFT NCBA Bulk Upload Item",
                filters={"parent": self.name, "parenttype": "Bulk Upload"},
                fields=["payment_reference"]
            )
            existing_refs = set(r.payment_reference for r in existing_rows if r.payment_reference)
        elif self.type == "EFT STANBIC BANK":
            existing_rows = frappe.get_all(
                "EFT STANBIC BANK Bulk Upload Item",
                filters={"parent": self.name, "parenttype": "Bulk Upload"},
                fields=["payment_reference"]
            )
            existing_refs = set(r.payment_reference for r in existing_rows if r.payment_reference)
        elif self.type == "RTGS NCBA":
            existing_rows = frappe.get_all(
                "RTGS NCBA Bulk Upload Item",
                filters={"parent": self.name, "parenttype": "Bulk Upload"},
                fields=["payment_reference"]
            )
            existing_refs = set(r.payment_reference for r in existing_rows if r.payment_reference)
        elif self.type == "RTGS STANBIC BANK":
            existing_rows = frappe.get_all(
                "RTGS Stanbic Bank Bulk Upload Item",
                filters={"parent": self.name, "parenttype": "Bulk Upload"},
                fields=["payment_reference"]
            )
            existing_refs = set(r.payment_reference for r in existing_rows if r.payment_reference)
        elif self.type == "Local Payments USD":
            existing_rows = frappe.get_all(
                "Local USD Bulk Upload Item",
                filters={"parent": self.name, "parenttype": "Bulk Upload"},
                fields=["reference"]
            )
            existing_refs = set(r.reference for r in existing_rows if r.reference)
        elif self.type == "International Payments USD":
            existing_rows = frappe.get_all(
                "International Payments USD Bulk Upload Item",
                filters={"parent": self.name, "parenttype": "Bulk Upload"},
                fields=["reference"]
            )
            existing_refs = set(r.reference for r in existing_rows if r.reference)
        elif self.type == "International Payments ZAR":
            existing_rows = frappe.get_all(
                "International Payments ZAR Bulk Upload Item",
                filters={"parent": self.name, "parenttype": "Bulk Upload"},
                fields=["reference"]
            )
            existing_refs = set(r.reference for r in existing_rows if r.reference)
        elif self.type == "International Payments EUR":
            existing_rows = frappe.get_all(
                "International Payments EUR Bulk Upload Item",
                filters={"parent": self.name, "parenttype": "Bulk Upload"},
                fields=["reference"]
            )
            existing_refs = set(r.reference for r in existing_rows if r.reference)
        elif self.type == "International Payments GBP":
            existing_rows = frappe.get_all(
                "International Payments GBP Bulk Upload Item",
                filters={"parent": self.name, "parenttype": "Bulk Upload"},
                fields=["reference"]
            )
            existing_refs = set(r.reference for r in existing_rows if r.reference)
        elif self.type == "International Payments RWF":
            existing_rows = frappe.get_all(
                "International Payments RWF Bulk Upload Item",
                filters={"parent": self.name, "parenttype": "Bulk Upload"},
                fields=["reference"]
            )
            existing_refs = set(r.reference for r in existing_rows if r.reference)

        draft_payments = frappe.db.get_all('Payment Entry', filters={
            'status': ['in', 'Draft'],
            'payment_type': 'Pay',
            'custom_upload_type': self.type,
            'name': ['not in', list(existing_refs)] if existing_refs else ['!=', '']
        }, fields=['name', 'party', 'paid_amount', 'custom_account_name', 'party_bank_account', 'custom_upload_type', 'reference_no'])

        total_grand_total = 0
        
        if draft_payments:
            for pymnt in draft_payments:
                # if pymnt.get("custom_upload_type") in ["EFT", "RTGS", "International Payments"]:
                if pymnt.get("custom_upload_type") in ["EFT NCBA","EFT STANBIC BANK","RTGS", "RTGS NCBA", "RTGS STANBIC BANK", "International Payments", "Local Payments USD", "International Payments USD", "International Payments ZAR", "International Payments EUR", "International Payments GBP", "International Payments RWF"]:
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
                    # Mpesa — fetch ALL beneficiaries so each gets its own row
                    beneficiaries = frappe.get_all(
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
                        for idx, b in enumerate(beneficiaries):
                            entry = pymnt.copy()
                            entry["name"] = f"{pymnt['name']}_{idx}"
                            entry["pe_name"] = pymnt["name"]
                            entry["mobilenumber"] = b.get("mobile_number") or ""
                            entry["documenttype"] = b.get("document_type") or ""
                            entry["supplier_invoice"] = b.get("document_number") or ""
                            entry["purposeofpayment"] = b.get("purpose_of_payment") or ""
                            entry["paid_amount"] = b.get("amount") or pymnt.get("paid_amount", 0)
                            pymnts_list.append(entry)
                            total_grand_total += entry["paid_amount"]
                    else:
                        # No beneficiaries — fall back to PE-level data
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







                        