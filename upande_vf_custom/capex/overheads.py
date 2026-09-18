import frappe
from frappe import _
from frappe.utils import add_months, flt, fmt_money, get_first_day, get_last_day, getdate, now_datetime, today

from upande_vf_custom.capex import CWIP
from upande_vf_custom.capex.project import refresh_project_costs

ALLOCATION = "Capex Overhead Allocation"
ALLOCATORS = ("System Manager", "Accounts Manager", "GCFO - VF")


@frappe.whitelist()
def allocate_farm_overheads(month):
	frappe.only_for(ALLOCATORS)
	return allocate(getdate(month))


def allocate_previous_month():
	"""Scheduled monthly. Does nothing until Finance lists the farm cost accounts."""
	if not frappe.get_single("Capex Settings").farm_cost_accounts:
		return
	allocate(add_months(get_first_day(today()), -1))


def allocate(any_day_in_month):
	"""Share one month's farm costs across open capex projects in proportion to budget.

	Calculated for reporting only: no journal entries are posted. Re-running a month
	updates that month's lines in place.
	"""
	settings = frappe.get_single("Capex Settings")
	start, end = get_first_day(any_day_in_month), get_last_day(any_day_in_month)

	if end >= getdate(today()):
		frappe.throw(_("{0} has not finished yet. Allocate a month once it has ended.").format(start.strftime("%B %Y")))

	accounts = get_farm_cost_accounts(settings)
	if not accounts:
		return _("No farm cost accounts are set up in Capex Settings, so nothing was allocated.")

	pool = get_farm_cost_pool(settings.company, accounts, start, end)
	projects = frappe.get_all(
		"Project",
		filters={
			"project_type": CWIP,
			"company": settings.company,
			"status": "Open",
			"custom_budget": [">", 0],
			"creation": ["<=", f"{end} 23:59:59"],
		},
		fields=["name", "custom_budget"],
		order_by="custom_budget desc",
	)

	shares = split_pool(pool, projects)
	allocated_on = now_datetime()
	for project in projects:
		amount, share_percent = shares[project.name]
		save_allocation(project.name, start, pool, share_percent, amount, allocated_on)

	# Projects allocated on an earlier run that no longer qualify are zeroed, not removed.
	eligible = {p.name for p in projects}
	for name, parent in frappe.get_all(
		ALLOCATION, filters={"parenttype": "Project", "period": start}, fields=["name", "parent"], as_list=True
	):
		if parent not in eligible:
			frappe.db.set_value(ALLOCATION, name, {"amount": 0, "share_percent": 0, "pool_amount": pool})
			refresh_project_costs(parent)

	if not settings.last_allocated_period or getdate(settings.last_allocated_period) < start:
		settings.db_set("last_allocated_period", start)

	currency = frappe.get_cached_value("Company", settings.company, "default_currency")
	return _("Allocated {0} of farm costs for {1} across {2} open capex projects.").format(
		fmt_money(pool, currency=currency), start.strftime("%B %Y"), len(projects)
	)


def get_farm_cost_accounts(settings):
	"""Leaf accounts for the configured accounts, expanding any group accounts."""
	leaves = set()
	for row in settings.farm_cost_accounts:
		if row.is_labour and not settings.include_labour:
			continue

		account = frappe.get_cached_value("Account", row.account, ["lft", "rgt", "is_group", "company"], as_dict=True)
		if not account or account.company != settings.company:
			continue

		if account.is_group:
			leaves.update(
				frappe.get_all(
					"Account",
					filters={
						"company": settings.company,
						"is_group": 0,
						"lft": [">=", account.lft],
						"rgt": ["<=", account.rgt],
					},
					pluck="name",
				)
			)
		else:
			leaves.add(row.account)
	return sorted(leaves)


def get_farm_cost_pool(company, accounts, start, end):
	pool = frappe.db.sql(
		"""
		select sum(debit - credit)
		from `tabGL Entry`
		where company = %(company)s
			and is_cancelled = 0
			and voucher_type != 'Period Closing Voucher'
			and posting_date between %(start)s and %(end)s
			and account in %(accounts)s
		""",
		{"company": company, "start": start, "end": end, "accounts": tuple(accounts)},
	)[0][0]
	return flt(pool, 2)


def split_pool(pool, projects):
	"""Split pool pro rata by budget. Rounding difference goes to the largest budget so the
	lines always add up to the pool."""
	total_budget = sum(flt(p.custom_budget) for p in projects)
	if not projects or not total_budget:
		return {}

	shares = {}
	for p in projects:
		ratio = flt(p.custom_budget) / total_budget
		shares[p.name] = [flt(pool * ratio, 2), flt(ratio * 100, 4)]

	difference = flt(pool - sum(amount for amount, _pct in shares.values()), 2)
	shares[projects[0].name][0] = flt(shares[projects[0].name][0] + difference, 2)
	return shares


def save_allocation(project, period, pool, share_percent, amount, allocated_on):
	values = {
		"pool_amount": pool,
		"share_percent": share_percent,
		"amount": amount,
		"allocated_on": allocated_on,
	}
	existing = frappe.db.get_value(
		ALLOCATION,
		{"parent": project, "parenttype": "Project", "parentfield": "custom_overhead_allocations", "period": period},
		"name",
	)
	if existing:
		frappe.db.set_value(ALLOCATION, existing, values)
	else:
		row = frappe.new_doc(ALLOCATION)
		row.update(values)
		row.update(
			{
				"parent": project,
				"parenttype": "Project",
				"parentfield": "custom_overhead_allocations",
				"period": period,
				"idx": frappe.db.count(ALLOCATION, {"parent": project, "parenttype": "Project"}) + 1,
			}
		)
		row.db_insert()

	refresh_project_costs(project)
