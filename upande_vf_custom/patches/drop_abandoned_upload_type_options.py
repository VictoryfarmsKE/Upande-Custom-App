"""Drop the Customize Form override that offers upload types the app cannot process.

On 2026-08-20 the Bulk Upload `type` options were replaced through Customize Form with an
18-option scheme that split each channel by bank (EFT STANBIC, RTGS STANBIC, LOCAL USD NCBA,
LOCAL USD STANBIC, International Payments USD NCBA/STANBIC, International Payments TZS). The
code half of that work was written but never survived - the merge of Newton_Customizations on
2026-09-08 restored the older `bulk_upload.py`, which only branches on the original names.

A Property Setter overrides whatever the app ships and is never removed by a deploy, so the
form kept offering names nothing could process: picking one gives a document where Get Draft
Payments silently does nothing, and older documents holding a retired name fail validation.

Removing the Property Setter lets the field fall back to the options the app actually ships.
Existing documents keep their stored values - this changes what can be chosen, not any data.
"""

import frappe

ABANDONED_OPTIONS = {
	"EFT STANBIC",
	"RTGS STANBIC",
	"LOCAL USD NCBA",
	"LOCAL USD STANBIC",
	"International Payments USD NCBA",
	"International Payments USD STANBIC",
	"International Payments TZS",
}

OVERRIDES = [
	("Bulk Upload", "type"),
	("Payment Entry", "custom_upload_type"),
]


def execute():
	for doctype, fieldname in OVERRIDES:
		name = frappe.db.get_value(
			"Property Setter",
			{"doc_type": doctype, "field_name": fieldname, "property": "options"},
			"name",
		)

		if not name:
			continue

		value = frappe.db.get_value("Property Setter", name, "value") or ""
		options = {line.strip() for line in value.split("\n") if line.strip()}

		# Only touch the override if it is the abandoned scheme - compare whole options,
		# never substrings, or "RTGS STANBIC" would match "RTGS STANBIC BANK".
		if not options & ABANDONED_OPTIONS:
			continue

		frappe.delete_doc("Property Setter", name, ignore_permissions=True)
		frappe.clear_cache(doctype=doctype)
		print(
			f"removed {name}: {doctype}.{fieldname} now follows the options the app ships "
			f"(dropped {sorted(options & ABANDONED_OPTIONS)})"
		)

	frappe.db.commit()
