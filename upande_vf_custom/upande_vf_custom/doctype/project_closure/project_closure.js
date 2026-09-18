// Copyright (c) 2026, Upande and contributors
// For license information, please see license.txt

frappe.ui.form.on("Project Closure", {
	setup(frm) {
		frm.set_query("project", () => {
			const filters = {
				project_type: "Capital Work in Progress",
				custom_project_closure: ["is", "not set"],
			};
			if (frm.capex_company) {
				filters.company = frm.capex_company;
			}
			return { filters };
		});
	},

	onload(frm) {
		frappe.db.get_single_value("Capex Settings", "company").then((company) => {
			frm.capex_company = company;
		});

		// Opened from a project's Close Project button: the project is already set.
		if (frm.is_new() && frm.doc.project) {
			fill_from_project(frm);
		}
	},

	refresh(frm) {
		// The checklist comes from Capex Settings; items can be ticked but not added or removed.
		frm.set_df_property("checklist", "cannot_add_rows", true);
		frm.set_df_property("checklist", "cannot_delete_rows", true);

		if (frm.doc.project) {
			frm.add_custom_button(__("View Project"), () => frappe.set_route("Form", "Project", frm.doc.project));
		}
	},

	project(frm) {
		if (frm.doc.docstatus === 0) {
			fill_from_project(frm);
		}
	},
});

function fill_from_project(frm) {
	if (!frm.doc.project) {
		frm.set_value({ approved_budget: 0, final_cost: 0, variance: 0, variance_percent: 0 });
		return;
	}

	frappe.call({
		method: "upande_vf_custom.capex.closure.get_closure_defaults",
		args: { project: frm.doc.project },
		callback(r) {
			if (!r.message) return;

			frm.set_value(r.message.financials);

			// Keep any ticks already made; only seed an empty checklist.
			if (!(frm.doc.checklist || []).length) {
				r.message.checklist.forEach((item) => frm.add_child("checklist", { item }));
				frm.refresh_field("checklist");
			}
		},
	});
}
