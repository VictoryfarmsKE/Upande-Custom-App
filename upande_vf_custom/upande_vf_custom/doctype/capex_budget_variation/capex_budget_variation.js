frappe.ui.form.on("Capex Budget Variation", {
	setup(frm) {
		frm.set_query("project", () => ({
			filters: {
				project_type: "Capital Work in Progress",
				custom_project_closure: ["is", "not set"],
			},
		}));
	},

	onload(frm) {
		if (frm.is_new() && frm.doc.project) {
			fill_budgets(frm);
		}
	},

	refresh(frm) {
		if (frm.doc.project) {
			frm.add_custom_button(__("View Project"), () => frappe.set_route("Form", "Project", frm.doc.project));
		}
	},

	project(frm) {
		if (frm.doc.docstatus === 0) {
			fill_budgets(frm);
		}
	},

	variation_amount(frm) {
		set_new_budget(frm);
	},
});

function fill_budgets(frm) {
	if (!frm.doc.project) {
		frm.set_value({ original_budget: 0, current_budget: 0, new_budget: 0 });
		return;
	}

	frappe.call({
		method: "upande_vf_custom.capex.variation.get_variation_defaults",
		args: { project: frm.doc.project },
		callback(r) {
			if (!r.message) return;

			frm.set_value(r.message).then(() => set_new_budget(frm));
		},
	});
}

function set_new_budget(frm) {
	frm.set_value("new_budget", flt(frm.doc.current_budget) + flt(frm.doc.variation_amount));
}
