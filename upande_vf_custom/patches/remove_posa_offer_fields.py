import frappe

# POS Awesome is no longer installed, so these Table fields point at child
# DocTypes that do not exist. Loading Sales Order meta in the desk walks the
# table fields and blows up, which breaks the Sales Order list, every Sales
# Order form, and any workspace that links to Sales Order.
ORPHAN_FIELDS = [
	("Sales Order", "posa_offers"),
	("Sales Order", "posa_coupons"),
]

TABLE_FIELDTYPES = ("Table", "Table MultiSelect")


def execute():
	removed = []

	for dt, fieldname in ORPHAN_FIELDS:
		field = frappe.db.get_value(
			"Custom Field",
			{"dt": dt, "fieldname": fieldname},
			["name", "fieldtype", "options"],
			as_dict=True,
		)

		if not field:
			continue

		# Only table fields are safe to drop blindly - they own no column.
		if field.fieldtype not in TABLE_FIELDTYPES:
			continue

		# If the target doctype is back, the field is legitimate again.
		if field.options and frappe.db.exists("DocType", field.options):
			continue

		frappe.db.delete("Custom Field", {"name": field.name})
		removed.append((dt, fieldname))

	if not removed:
		return

	frappe.db.commit()

	for dt in {dt for dt, _ in removed}:
		frappe.clear_cache(doctype=dt)

	print(
		"upande_vf_custom: removed orphan custom field(s) {0}".format(
			", ".join("{0}.{1}".format(dt, fn) for dt, fn in removed)
		)
	)
