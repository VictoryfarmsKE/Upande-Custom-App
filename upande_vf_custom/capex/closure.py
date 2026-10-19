import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from upande_vf_custom.capex import CWIP
from upande_vf_custom.capex.approval import is_waiting_for_approval
from upande_vf_custom.capex.project import compute_project_costs

# What an approved closure does to the project's status. Deferred leaves it Open.
PROJECT_STATUS_ON_CLOSURE = {"Completed": "Completed", "Abandoned": "Cancelled"}

CLOSURE_TYPES_CHECKED_BY_SYSTEM = ("Completed", "Abandoned")
ATTACHMENTS_REQUIRED = {
	"Completed": (("final_boq", "Final BoQ"), ("completion_certificate", "Completion / Handover Certificate")),
	"Abandoned": (("final_boq", "Final BoQ"),),
}
DETAIL_LIMIT = 20


def project_documents(doctype, project, extra_conditions):
	item_doctype = f"{doctype} Item"
	header_match = "or d.project = %(project)s" if frappe.db.has_column(doctype, "project") else ""
	return frappe.db.sql_list(
		f"""
		select distinct d.name
		from `tab{doctype}` d
		join `tab{item_doctype}` i on i.parent = d.name
		where (i.project = %(project)s {header_match})
			and {extra_conditions}
		order by d.name
		""",
		{"project": project},
	)


def get_system_checks(project):
	open_orders = project_documents(
		"Purchase Order",
		project,
		"d.docstatus = 1 and d.status not in ('Closed', 'Completed', 'Delivered') and d.per_received < 100",
	)
	unbilled = (
		project_documents(
			"Purchase Order",
			project,
			"d.docstatus = 1 and d.status not in ('Closed', 'Completed') and d.per_billed < 100",
		)
		+ project_documents(
			"Purchase Receipt",
			project,
			"d.docstatus = 1 and d.status not in ('Closed', 'Completed', 'Return Issued') and d.per_billed < 100",
		)
		+ project_documents("Purchase Invoice", project, "d.docstatus = 0")
	)
	open_requests = project_documents(
		"Material Request",
		project,
		"d.docstatus = 1 and d.status != 'Stopped' and d.per_ordered < 100",
	)

	details = []
	for label, names in (
		(_("Purchase orders not received or closed"), open_orders),
		(_("Purchases without a booked invoice"), unbilled),
		(_("Open material requests"), open_requests),
	):
		if names:
			shown = ", ".join(names[:DETAIL_LIMIT])
			more = _(" and {0} more").format(len(names) - DETAIL_LIMIT) if len(names) > DETAIL_LIMIT else ""
			details.append(f"{label}: {shown}{more}")

	return {
		"open_purchase_orders": len(open_orders),
		"unbilled_purchases": len(unbilled),
		"open_material_requests": len(open_requests),
		"system_check_details": "\n".join(details),
	}


def get_financials(project):
	_overhead, total = compute_project_costs(project)
	budget = flt(project.custom_budget)
	variance = total - budget
	return {
		"approved_budget": budget,
		"final_cost": total,
		"variance": variance,
		"variance_percent": (variance / budget * 100) if budget else 0,
	}


def get_default_checklist():
	return [row.item for row in frappe.get_single("Capex Settings").closure_checklist]


@frappe.whitelist()
def get_closure_defaults(project):
	"""Figures and checklist for a new closure, so the form shows them as soon as a project is picked."""
	project = frappe.get_doc("Project", project)
	project.check_permission("read")
	return {
		"financials": get_financials(project),
		"checklist": get_default_checklist(),
		"system_checks": get_system_checks(project.name),
	}


class ProjectClosureController(Document):
	def validate(self):
		project = frappe.get_doc("Project", self.project)
		self.validate_project(project)
		self.validate_one_closure_per_project()
		self.set_financials(project)
		self.set_default_checklist()
		self.set_system_checks()
		if is_waiting_for_approval(self):
			self.validate_ready_for_approval()

	def before_submit(self):
		self.update(get_system_checks(self.project))
		self.validate_ready_for_approval()

	def validate_ready_for_approval(self):
		self.validate_variance_reason()
		self.validate_checklist_complete()
		self.validate_attachments()
		self.validate_system_checks()

	def on_submit(self):
		values = {"custom_project_closure": self.name, "custom_closure_date": self.closure_date}
		if self.closure_type in PROJECT_STATUS_ON_CLOSURE:
			values["status"] = PROJECT_STATUS_ON_CLOSURE[self.closure_type]
		frappe.db.set_value("Project", self.project, values)

	def before_cancel(self):
		asset = frappe.db.get_value("Asset", {"custom_project_": self.project, "docstatus": ["<", 2]}, "name")
		if asset:
			frappe.throw(
				_("Asset {0} was created from this project. Cancel or scrap the asset before cancelling the closure.").format(
					asset
				)
			)

	def on_cancel(self):
		values = {"custom_project_closure": None, "custom_closure_date": None}
		if self.closure_type in PROJECT_STATUS_ON_CLOSURE:
			values["status"] = "Open"
		frappe.db.set_value("Project", self.project, values)

	def validate_project(self, project):
		if project.project_type != CWIP:
			frappe.throw(_("Project {0} is not a Capital Work in Progress project.").format(project.name))

		company = frappe.db.get_single_value("Capex Settings", "company")
		if company and project.company != company:
			frappe.throw(
				_("Project closure is only set up for {0}. Project {1} belongs to {2}.").format(
					company, project.name, project.company
				)
			)

	def validate_one_closure_per_project(self):
		other = frappe.db.get_value(
			"Project Closure",
			{"project": self.project, "docstatus": ["<", 2], "name": ["!=", self.name]},
			"name",
		)
		if other:
			frappe.throw(_("Project {0} already has closure {1}.").format(self.project, other))

	def set_financials(self, project):
		if self.docstatus != 0:
			return

		self.update(get_financials(project))

	def set_system_checks(self):
		if self.docstatus != 0:
			return

		self.update(get_system_checks(self.project))

	def validate_attachments(self):
		missing = [label for fieldname, label in ATTACHMENTS_REQUIRED.get(self.closure_type, ()) if not self.get(fieldname)]
		if missing:
			frappe.throw(
				_("Attach these before sending the closure for approval:") + "<br><br>" + "<br>".join(missing),
				title=_("Supporting documents missing"),
			)

	def validate_system_checks(self):
		if self.closure_type not in CLOSURE_TYPES_CHECKED_BY_SYSTEM:
			return

		if self.open_purchase_orders or self.unbilled_purchases or self.open_material_requests:
			frappe.throw(
				_("Close out these documents before the project can be closed:")
				+ "<br><br>"
				+ (self.system_check_details or "").replace("\n", "<br>"),
				title=_("Project has open documents"),
			)

	def set_default_checklist(self):
		if self.checklist:
			return

		for item in get_default_checklist():
			self.append("checklist", {"item": item})

	def validate_variance_reason(self):
		if flt(self.variance, self.precision("variance")) and not (self.variance_reason or "").strip():
			frappe.throw(_("Please explain why the final cost differs from the approved budget."))

	def validate_checklist_complete(self):
		present = {row.item for row in self.checklist}
		missing = [item for item in get_default_checklist() if item not in present]
		if missing:
			frappe.throw(
				_("These checklist items are missing from the closure:") + "<br><br>" + "<br>".join(missing),
				title=_("Closure checklist incomplete"),
			)

		outstanding = [row.item for row in self.checklist if not row.completed]
		if outstanding:
			frappe.throw(
				_("Complete every checklist item before sending the closure for approval:") + "<br><br>" + "<br>".join(outstanding),
				title=_("Closure checklist incomplete"),
			)
