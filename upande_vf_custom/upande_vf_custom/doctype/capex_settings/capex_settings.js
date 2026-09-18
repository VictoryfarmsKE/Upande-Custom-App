// Copyright (c) 2026, Upande and contributors
// For license information, please see license.txt

frappe.ui.form.on("Capex Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Allocate Farm Overheads"), () => {
			frappe.prompt(
				{
					label: __("Any date in the month to allocate"),
					fieldname: "month",
					fieldtype: "Date",
					reqd: 1,
					default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
				},
				(values) => {
					frappe.call({
						method: "upande_vf_custom.capex.overheads.allocate_farm_overheads",
						args: { month: values.month },
						freeze: true,
						freeze_message: __("Allocating farm overheads..."),
						callback(r) {
							if (r.message) {
								frappe.msgprint(r.message);
								frm.reload_doc();
							}
						},
					});
				},
				__("Allocate Farm Overheads"),
				__("Allocate")
			);
		});
	},
});
