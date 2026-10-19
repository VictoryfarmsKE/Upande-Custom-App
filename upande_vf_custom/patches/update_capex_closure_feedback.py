import frappe

OVERHEAD_PERCENT = 10

CHECKED_BY_SYSTEM_OR_DROPPED = (
	"All purchase orders received or closed",
	"All supplier invoices booked",
	"No open material requests",
	"Asset registered or capitalised",
)

WORKFLOW = "Capex Budget Variation Approval"
MAINTENANCE_USER = "Maintenance User - VF"
CONSTRUCTION_HOD = "Construction/Maintenance HOD - VF"
GCFO = "GCFO - VF"
PENDING_HOD = "Pending Approval (Construction/Maintenance HOD)"
PENDING_FINANCE = "Pending Approval (Finance HOD)"


def execute():
	update_capex_settings()
	create_variation_workflow()


def update_capex_settings():
	settings = frappe.get_single("Capex Settings")
	if not settings.company:
		return

	if not settings.overhead_percent:
		settings.overhead_percent = OVERHEAD_PERCENT

	kept = [row for row in settings.closure_checklist if row.item not in CHECKED_BY_SYSTEM_OR_DROPPED]
	if len(kept) != len(settings.closure_checklist):
		settings.set("closure_checklist", [{"item": row.item} for row in kept])

	settings.flags.ignore_permissions = True
	settings.save()


def create_variation_workflow():
	if frappe.db.exists("Workflow", WORKFLOW):
		return

	roles = (MAINTENANCE_USER, CONSTRUCTION_HOD, GCFO)
	if not all(frappe.db.exists("Role", role) for role in roles):
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
			"document_type": "Capex Budget Variation",
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
