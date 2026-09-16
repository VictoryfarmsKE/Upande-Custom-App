"""Fuel issued must be charged to an asset.

Finance tracks fuel consumption per asset. A fuel line is any row whose item sits in the
Fuel item group or one of its child groups; on a Material Issue requisition or stock entry
it has to name a submitted asset of the same company that could plausibly burn fuel - so
laptops, furniture, cages, nets and buildings are kept out of the picker.
"""

import frappe
from frappe import _
from frappe.utils.nestedset import get_descendants_of

FUEL_ITEM_GROUP = "Fuel"
NON_FUEL_ASSET_CATEGORIES = (
	"Computer Equipment",
	"Furniture and Fixtures",
	"Cages",
	"Nets",
	"Buildings and Leasehold Improvements",
	"Fixed Asset WIP",
)


def fuel_item_groups():
	"""The Fuel group and anything filed under it, so new sub-groups need no code change."""
	if not frappe.db.exists("Item Group", FUEL_ITEM_GROUP):
		return [FUEL_ITEM_GROUP]

	return [
		FUEL_ITEM_GROUP,
		*get_descendants_of("Item Group", FUEL_ITEM_GROUP, ignore_permissions=True),
	]


@frappe.whitelist()
def get_fuel_item_groups():
	"""Same list for the browser, so the form and the server agree on what fuel is."""
	return fuel_item_groups()


def is_fuel_row(row):
	item_group = row.get("item_group")
	if not item_group and row.get("item_code"):
		item_group = frappe.get_cached_value("Item", row.item_code, "item_group")
	return item_group in fuel_item_groups()


def validate_fuel_asset(row, document, company):
	if not row.get("asset"):
		frappe.throw(
			_("Row {0}: select the Asset this {1} is for.").format(row.idx, frappe.bold(row.item_code)),
			title=_("Asset required on {0}").format(document),
		)

	asset = frappe.db.get_value("Asset", row.asset, ["docstatus", "asset_category", "company"], as_dict=True)
	eligible = (
		asset
		and asset.docstatus == 1
		and asset.company == company
		and asset.asset_category not in NON_FUEL_ASSET_CATEGORIES
	)
	if not eligible:
		frappe.throw(
			_("Row {0}: {1} can't take fuel. Pick a submitted {2} asset that runs on fuel.").format(
				row.idx, frappe.bold(row.asset), company
			),
			title=_("Asset not eligible for fuel"),
		)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def fuel_asset_query(doctype, txt, searchfield, start, page_len, filters):
	if isinstance(filters, str):
		filters = frappe.parse_json(filters)

	filters = filters or {}
	conditions = {"docstatus": 1, "asset_category": ["not in", NON_FUEL_ASSET_CATEGORIES]}
	if filters.get("company"):
		conditions["company"] = filters["company"]

	return frappe.get_all(
		"Asset",
		filters=conditions,
		or_filters={"name": ["like", f"%{txt}%"], "asset_name": ["like", f"%{txt}%"]},
		fields=["name", "asset_name", "asset_category"],
		order_by="asset_name",
		start=start,
		page_length=page_len,
		as_list=True,
	)
