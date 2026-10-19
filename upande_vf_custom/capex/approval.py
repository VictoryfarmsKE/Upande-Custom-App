NOT_YET_SENT = ("", "Draft", "Rejected")


def is_waiting_for_approval(doc):
	if doc.docstatus != 0 or not doc.meta.has_field("workflow_state"):
		return False
	return (doc.get("workflow_state") or "") not in NOT_YET_SENT
