"""Repoint DocType Links left behind by the maintenance schedule rename.

`custom/asset.json` ships its DocType Links with a hardcoded `name`, while
`sync_customizations` looks an existing row up by content - parent, link_doctype,
link_fieldname. The rename changed the content but not the name, so on any site still
holding the old row the lookup misses, the sync tries to insert using the fixture's own
name, and the primary key collides:

    DuplicateEntryError: ('DocType Link', 'ujfn8h9u34', Duplicate entry for key 'PRIMARY')

That aborts the whole migrate. This has to be a patch rather than an `after_migrate` hook,
because `after_migrate` runs after `sync_customizations` - by which point the migrate is
already dead.
"""

import frappe

RENAMED_DOCTYPES = {
	"VF Asset Maintenance Schedule": "Preventative Maintenance Schedule",
	"VF Asset Maintenance Schedule Tasks": "Preventative Maintenance Schedule Tasks",
}


def execute():
	for old, new in RENAMED_DOCTYPES.items():
		# If the old doctype is still around the rename has not happened here - leave it be.
		if frappe.db.exists("DocType", old):
			continue

		if not frappe.db.exists("DocType", new):
			continue

		rows = frappe.db.sql(
			"select name, parent from `tabDocType Link` where link_doctype = %s",
			(old,),
			as_dict=True,
		)

		if not rows:
			continue

		frappe.db.sql(
			"update `tabDocType Link` set link_doctype = %s where link_doctype = %s",
			(new, old),
		)

		for parent in {row.parent for row in rows}:
			frappe.clear_cache(doctype=parent)

		print(f"repointed {len(rows)} DocType Link row(s) from {old} to {new}")
