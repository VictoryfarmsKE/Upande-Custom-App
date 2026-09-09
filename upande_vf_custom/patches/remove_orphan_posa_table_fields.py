"""Drop the POS Awesome child-table fields left on Sales Order after the app went away.

`posawesome` is no longer installed, so `POS Offer Detail` and `POS Coupon Detail` do not
exist - but the Custom Fields pointing at them are still in the database. The desk resolves
every child table when it loads a doctype, so opening anything that touches Sales Order dies
with "DocType POS Offer Detail not found". `sync_customizations` only inserts and updates,
never deletes, so the rows have to be removed here.
"""

import frappe

ORPHAN_FIELDS = [
	("Sales Order", "posa_offers"),
	("Sales Order", "posa_coupons"),
]

TABLE_FIELDTYPES = ("Table", "Table MultiSelect")


def execute():
	removed = []

	for doctype, fieldname in ORPHAN_FIELDS:
		field = frappe.db.get_value(
			"Custom Field",
			{"dt": doctype, "fieldname": fieldname},
			["name", "fieldtype", "options"],
			as_dict=True,
		)

		if not field:
			continue

		# A child table owns no column on the parent, so dropping it cannot lose data.
		if field.fieldtype not in TABLE_FIELDTYPES:
			continue

		# If posawesome is ever reinstalled the field is legitimate again - leave it alone.
		if field.options and frappe.db.exists("DocType", field.options):
			continue

		frappe.delete_doc("Custom Field", field.name)
		removed.append((doctype, fieldname))

	if not removed:
		return

	frappe.db.commit()

	for doctype in {doctype for doctype, _ in removed}:
		frappe.clear_cache(doctype=doctype)

	for doctype, fieldname in removed:
		print(f"removed orphan custom field {doctype}-{fieldname}")
