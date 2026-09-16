"""Put the Asset column in front of people who arranged their own item columns.

The field is marked in_list_view, but anyone who has customised the columns of the items table
keeps their own layout, and that layout wins - so the Asset column would simply never appear for
them. This adds it to those saved layouts, borrowing the width back from their widest column
because the grid only has room for ten column units and silently drops whatever overflows.

Nothing is removed: a layout that already lists the asset is left untouched.
"""

import json

import frappe

ITEM_TABLES = {
	"Stock Entry": "Stock Entry Detail",
	"Requisition Form": "Requisition Form Item",
}
GRID_WIDTH = 10
ASSET_WIDTH = 2


def execute():
	for parent, child in ITEM_TABLES.items():
		for row in frappe.db.sql(
			"select user, data from __UserSettings where doctype = %s", parent, as_dict=True
		):
			settings = parse(row.data)
			view = (settings.get("GridView") or {}).get(child)

			if not view:
				continue

			before = json.dumps(settings)
			if not any(column.get("fieldname") == "asset" for column in view):
				view.append({"fieldname": "asset", "columns": ASSET_WIDTH})
			make_room(view)

			after = json.dumps(settings)
			if after == before:
				continue

			frappe.db.sql(
				"update __UserSettings set data = %s where user = %s and doctype = %s",
				(after, row.user, parent),
			)

	frappe.db.commit()


def parse(data):
	try:
		return json.loads(data or "{}") or {}
	except ValueError:
		return {}


def make_room(view):
	"""Narrow the widest column, one unit at a time, until the row fits again."""
	def width():
		return sum(column.get("columns") or 1 for column in view)

	while width() > GRID_WIDTH:
		widest = max(
			(c for c in view if c.get("fieldname") != "asset" and (c.get("columns") or 1) > 1),
			key=lambda c: c["columns"],
			default=None,
		)
		if not widest:
			break
		widest["columns"] -= 1

	# a layout packed with narrow columns leaves nothing to borrow from, so the asset column
	# gives up its own width rather than being dropped off the end of the row
	asset = next((c for c in view if c.get("fieldname") == "asset"), None)
	if asset and width() > GRID_WIDTH:
		asset["columns"] = 1
