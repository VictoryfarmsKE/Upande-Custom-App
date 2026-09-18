import frappe

DEFAULT_COMPANY = "Victory Farms Ltd"

DEFAULT_CHECKLIST = (
	"Final BoQ attached",
	"All purchase orders received or closed",
	"All supplier invoices booked",
	"No open material requests",
	"Final cost reconciled against budget, with any variance explained",
	"Completion or handover certificate attached",
	"Asset registered or capitalised",
	"Lessons learned recorded",
)

WORKFLOW = "Project Closure Approval"
MAINTENANCE_USER = "Maintenance User - VF"
CONSTRUCTION_HOD = "Construction/Maintenance HOD - VF"
GCFO = "GCFO - VF"

PENDING_HOD = "Pending Approval (Construction/Maintenance HOD)"
PENDING_FINANCE = "Pending Approval (Finance HOD)"


def execute():
	"""Additive only: fills blanks in Capex Settings and creates the closure workflow if it
	does not exist. Never overwrites anything already configured."""
	seed_capex_settings()
	create_closure_workflow()


def seed_capex_settings():
	settings = frappe.get_single("Capex Settings")
	changed = False

	if not settings.company and frappe.db.exists("Company", DEFAULT_COMPANY):
		settings.company = DEFAULT_COMPANY
		changed = True

	if not settings.closure_checklist:
		for item in DEFAULT_CHECKLIST:
			settings.append("closure_checklist", {"item": item})
		changed = True

	if changed and settings.company:
		settings.flags.ignore_permissions = True
		settings.save()


def create_closure_workflow():
	if frappe.db.exists("Workflow", WORKFLOW):
		return

	roles = (MAINTENANCE_USER, CONSTRUCTION_HOD, GCFO)
	if not all(frappe.db.exists("Role", role) for role in roles):
		# Site without the VF approval roles (e.g. a fresh install): skip rather than guess.
		return

	for state, style in (
		("Draft", ""),
		(PENDING_HOD, "Warning"),
		(PENDING_FINANCE, "Warning"),
		("Approved", "Success"),
		("Rejected", "Danger"),
		("Cancelled", "Danger"),
	):
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": state, "style": style}).insert(
				ignore_permissions=True
			)

	for action in ("Send for Approval", "Approve", "Reject", "Cancel"):
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(
				ignore_permissions=True
			)

	frappe.get_doc(
		{
			"doctype": "Workflow",
			"workflow_name": WORKFLOW,
			"document_type": "Project Closure",
			"workflow_state_field": "workflow_state",
			"is_active": 1,
			"send_email_alert": 0,
			"states": [
				{"state": "Draft", "doc_status": "0", "allow_edit": MAINTENANCE_USER},
				{"state": PENDING_HOD, "doc_status": "0", "allow_edit": CONSTRUCTION_HOD},
				{"state": PENDING_FINANCE, "doc_status": "0", "allow_edit": GCFO},
				{"state": "Approved", "doc_status": "1", "allow_edit": GCFO},
				{"state": "Rejected", "doc_status": "0", "allow_edit": MAINTENANCE_USER},
				{"state": "Cancelled", "doc_status": "2", "allow_edit": GCFO},
			],
			"transitions": [
				{"state": "Draft", "action": "Send for Approval", "next_state": PENDING_HOD, "allowed": MAINTENANCE_USER},
				{"state": PENDING_HOD, "action": "Approve", "next_state": PENDING_FINANCE, "allowed": CONSTRUCTION_HOD},
				{"state": PENDING_HOD, "action": "Reject", "next_state": "Rejected", "allowed": CONSTRUCTION_HOD},
				{"state": PENDING_FINANCE, "action": "Approve", "next_state": "Approved", "allowed": GCFO},
				{"state": PENDING_FINANCE, "action": "Reject", "next_state": "Rejected", "allowed": GCFO},
				{"state": "Rejected", "action": "Send for Approval", "next_state": PENDING_HOD, "allowed": MAINTENANCE_USER},
				{"state": "Approved", "action": "Cancel", "next_state": "Cancelled", "allowed": GCFO},
			],
		}
	).insert(ignore_permissions=True)
