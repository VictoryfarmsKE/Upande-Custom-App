import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, fmt_money

from upande_vf_custom.capex import CWIP
from upande_vf_custom.capex.approval import is_waiting_for_approval


def get_budget_figures(project):
	current = flt(project.custom_budget)
	return {
		"current_budget": current,
		"original_budget": flt(project.custom_original_budget) or current,
	}


@frappe.whitelist()
def get_variation_defaults(project):
	project = frappe.get_doc("Project", project)
	project.check_permission("read")
	return get_budget_figures(project)


class CapexBudgetVariationController(Document):
	def validate(self):
		project = frappe.get_doc("Project", self.project)
		self.validate_project(project)
		self.validate_one_open_variation()
		if self.docstatus == 0:
			self.update(get_budget_figures(project))
		self.set_new_budget()
		if is_waiting_for_approval(self):
			self.validate_ready_for_approval()

	def before_submit(self):
		self.validate_ready_for_approval()
		current = flt(frappe.db.get_value("Project", self.project, "custom_budget"))
		if flt(current - flt(self.current_budget), 2):
			frappe.throw(
				_("The budget on {0} has changed to {1} since this variation was raised. Send it back to draft and save it again.").format(
					self.project, fmt_money(current)
				)
			)

	def on_submit(self):
		self.apply_budget(self.new_budget, self.current_budget)
		frappe.get_doc("Project", self.project).add_comment(
			"Info",
			_("Budget changed from {0} to {1} by {2}").format(
				fmt_money(self.current_budget), fmt_money(self.new_budget), self.name
			),
		)

	def before_cancel(self):
		current = flt(frappe.db.get_value("Project", self.project, "custom_budget"))
		if flt(current - flt(self.new_budget), 2):
			frappe.throw(
				_("The budget on {0} has been changed again since this variation. Cancel the later variations first.").format(
					self.project
				)
			)

	def on_cancel(self):
		self.apply_budget(self.current_budget, None)
		frappe.get_doc("Project", self.project).add_comment(
			"Info",
			_("Budget changed back to {0} because {1} was cancelled").format(fmt_money(self.current_budget), self.name),
		)

	def apply_budget(self, budget, original_if_missing):
		values = {"custom_budget": budget}
		if original_if_missing is not None and not frappe.db.get_value("Project", self.project, "custom_original_budget"):
			values["custom_original_budget"] = original_if_missing
		frappe.db.set_value("Project", self.project, values)

	def validate_project(self, project):
		if project.project_type != CWIP:
			frappe.throw(_("Project {0} is not a Capital Work in Progress project.").format(project.name))

		if self.docstatus == 0 and project.custom_project_closure:
			frappe.throw(_("Project {0} has been closed, so its budget can no longer change.").format(project.name))

	def validate_one_open_variation(self):
		other = frappe.db.get_value(
			"Capex Budget Variation",
			{"project": self.project, "docstatus": 0, "name": ["!=", self.name]},
			"name",
		)
		if other and self.docstatus == 0:
			frappe.throw(_("Project {0} already has variation {1} in progress.").format(self.project, other))

	def set_new_budget(self):
		if not flt(self.variation_amount, 2):
			frappe.throw(_("Enter the change in budget."))

		self.new_budget = flt(self.current_budget) + flt(self.variation_amount)
		if self.new_budget <= 0:
			frappe.throw(_("The new budget must be more than zero."))

	def validate_ready_for_approval(self):
		if not self.revised_boq:
			frappe.throw(_("Attach the revised BoQ before sending this variation for approval."))
