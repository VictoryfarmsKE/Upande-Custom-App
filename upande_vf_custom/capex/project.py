import frappe
from frappe import _
from frappe.utils import flt

from upande_vf_custom.capex import CWIP

# Required on capex projects created from now on. Existing projects are left alone.
REQUIRED_ON_NEW_CAPEX = (
	("custom_project_owner", "Project Owner"),
	("custom_project_description", "Project Description"),
	("custom_location", "Location"),
)


def compute_project_costs(project):
	"""Return (allocated overhead, total project cost) for a capex project.

	Total project cost is purchase invoices + consumables + allocated farm overheads.
	"""
	overhead = sum(flt(row.amount) for row in project.get("custom_overhead_allocations") or [])
	total = flt(project.total_purchase_cost) + flt(project.total_consumed_material_cost) + overhead
	return overhead, total


def set_project_costs(project):
	project.custom_total_overhead_cost, project.custom_total_project_cost = compute_project_costs(project)


def refresh_project_costs(project_name):
	"""Recalculate and store the cost totals without saving the whole project."""
	project = frappe.get_doc("Project", project_name)
	overhead, total = compute_project_costs(project)
	frappe.db.set_value(
		"Project",
		project_name,
		{"custom_total_overhead_cost": overhead, "custom_total_project_cost": total},
		update_modified=False,
	)


def onload(doc, method=None):
	# Purchase invoices and stock entries update the project's cost fields directly in the
	# database, so recalculate on open to show a current total.
	if doc.project_type == CWIP:
		set_project_costs(doc)


def validate(doc, method=None):
	if doc.project_type != CWIP:
		return

	if doc.is_new():
		missing = [label for fieldname, label in REQUIRED_ON_NEW_CAPEX if not doc.get(fieldname)]
		if missing:
			frappe.throw(
				_("Please fill in {0} before saving this capex project.").format(", ".join(missing)),
				title=_("Missing capex details"),
			)

	set_project_costs(doc)
	warn_if_completed_without_closure(doc)


def warn_if_completed_without_closure(doc):
	if doc.status != "Completed" or doc.custom_project_closure:
		return

	before = doc.get_doc_before_save()
	if before and before.status == "Completed":
		return

	frappe.msgprint(
		_("Capex projects should be closed through a Project Closure so the closure is checked and approved."),
		indicator="orange",
		alert=True,
	)


def get_cwip_balance(project, account):
	balance = frappe.db.sql(
		"""
		select sum(debit - credit)
		from `tabGL Entry`
		where project = %s and account = %s and is_cancelled = 0
		""",
		(project, account),
	)[0][0]
	return flt(balance)


@frappe.whitelist()
def create_asset_from_project(project, item_code, location):
	"""Capitalise a closed capex project: create the Asset and the draft journal entry
	that moves its CWIP balance to the asset account, in one transaction."""
	project = frappe.get_doc("Project", project)
	project.check_permission("read")
	frappe.has_permission("Asset", "create", throw=True)
	frappe.has_permission("Journal Entry", "create", throw=True)

	if project.project_type != CWIP:
		frappe.throw(_("Only Capital Work in Progress projects can be capitalised."))

	closure = None
	if project.custom_project_closure:
		closure = frappe.db.get_value(
			"Project Closure",
			project.custom_project_closure,
			["docstatus", "closure_type", "closure_date"],
			as_dict=True,
		)
	if not closure or closure.docstatus != 1 or closure.closure_type != "Completed":
		frappe.throw(
			_("This project needs an approved Project Closure with closure type Completed before an asset can be created.")
		)

	existing_asset = frappe.db.get_value("Asset", {"custom_project_": project.name, "docstatus": ["<", 2]}, "name")
	if existing_asset:
		frappe.throw(_("Asset {0} has already been created for this project.").format(existing_asset))

	asset_category = frappe.db.get_value("Item", item_code, "asset_category")
	if not asset_category:
		frappe.throw(_("Item {0} has no Asset Category.").format(item_code))

	accounts = frappe.db.get_value(
		"Asset Category Account",
		{"parent": asset_category, "company_name": project.company},
		["fixed_asset_account", "capital_work_in_progress_account"],
		as_dict=True,
	)
	if not accounts or not accounts.fixed_asset_account or not accounts.capital_work_in_progress_account:
		frappe.throw(
			_("Asset Category {0} needs both a Fixed Asset Account and a Capital Work in Progress Account for {1}.").format(
				asset_category, project.company
			)
		)

	amount = get_cwip_balance(project.name, accounts.capital_work_in_progress_account)
	if amount <= 0:
		frappe.throw(
			_("There is no balance on {0} for this project, so there is nothing to capitalise.").format(
				accounts.capital_work_in_progress_account
			)
		)

	asset = frappe.get_doc(
		{
			"doctype": "Asset",
			"item_code": item_code,
			"asset_name": project.project_name,
			"company": project.company,
			"location": location,
			"purchase_date": closure.closure_date,
			"available_for_use_date": closure.closure_date,
			"gross_purchase_amount": amount,
			"is_existing_asset": 1,
			"cost_center": project.cost_center,
			"custom_project_": project.name,
		}
	).insert()

	journal_entry = frappe.get_doc(
		{
			"doctype": "Journal Entry",
			"voucher_type": "Journal Entry",
			"company": project.company,
			"posting_date": closure.closure_date,
			"user_remark": _("Capitalisation of capex project {0} into asset {1}").format(project.name, asset.name),
			"accounts": [
				{
					"account": accounts.capital_work_in_progress_account,
					"credit_in_account_currency": amount,
					"project": project.name,
				},
				{
					"account": accounts.fixed_asset_account,
					"debit_in_account_currency": amount,
					"project": project.name,
				},
			],
		}
	).insert()

	return {"asset": asset.name, "journal_entry": journal_entry.name, "amount": amount}
