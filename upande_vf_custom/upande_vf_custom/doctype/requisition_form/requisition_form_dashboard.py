from frappe import _

def get_data():
    return {
        "fieldname": "custom_requisition_form",
        "non_standard_fieldnames": {
            "Purchase Order": "material_request",
            "Request for Quotation": "material_request",
            "Supplier Quotation": "material_request",
            "Purchase Receipt": "material_request",
            "Pick List": "material_request",
            "Work Order": "material_request",
            "Sales Order": "material_request",
        },
        "internal_links": {
            "Sales Order": ["items", "sales_order"],
            "Project": ["items", "project"],
            "Cost Center": ["items", "cost_center"],
        },
        "transactions": [
            {
                "label": _("Reference"),
                "items": ["Sales Order", "Request for Quotation", "Supplier Quotation", "Purchase Order"],
            },
            {"label": _("Stock"), "items": ["Stock Entry", "Purchase Receipt", "Pick List"]},
            {"label": _("Manufacturing"), "items": ["Work Order"]},
            {"label": _("Internal Transfer"), "items": ["Sales Order"]},
            {"label": _("Accounting Dimensions"), "items": ["Project", "Cost Center"]},
        ],
    }
