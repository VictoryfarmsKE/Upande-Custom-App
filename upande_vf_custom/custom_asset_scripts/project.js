frappe.ui.form.on('Project', {
    refresh: function(frm) {
        manage_create_asset_button(frm);
        calculate_and_set_custom_total_project_cost(frm);
    },

    project_type: function(frm) {
        manage_create_asset_button(frm);
        calculate_and_set_custom_total_project_cost(frm);
    }
});

function manage_create_asset_button(frm) {

    // Remove existing button first to avoid duplicates
    frm.remove_custom_button(__('Create Asset'));

    // Only show button for saved CWIP Projects
    if (!frm.is_new() &&
        frm.doc.project_type === "Capital Work in Progress") {

        frm.add_custom_button(__('Create Asset'), function() {

            if (frm.doc.status !== "Completed") {
                frappe.msgprint(__('The project must be marked as completed before creating an asset.'));
                return;
            }

            frappe.confirm(
                __('Are you sure you want to create an asset?'),
                function() {

                    frappe.prompt([
                        {
                            label: 'Item Code',
                            fieldname: 'item_code',
                            fieldtype: 'Link',
                            options: 'Item',
                            reqd: 1,
                            description: 'Select an existing Item Code.',
                            filters: {
                                item_group: 'Fixed Assets'
                            }
                        },
                        {
                            label: 'Location',
                            fieldname: 'location',
                            fieldtype: 'Link',
                            options: 'Location',
                            reqd: 1
                        }
                    ],
                    function(values) {

                        let gross_purchase_amount = frm.doc.custom_total_project_cost || 0;

                        if (gross_purchase_amount <= 0) {
                            frappe.msgprint(__('Total Project Cost cannot be zero.'));
                            return;
                        }

                        // Check if Asset already exists
                        frappe.call({
                            method: "frappe.client.get_list",
                            args: {
                                doctype: "Asset",
                                filters: {
                                    asset_name: frm.doc.project_name,
                                    item_code: values.item_code,
                                    company: frm.doc.company
                                },
                                fields: ["name"]
                            },
                            callback: function(r) {

                                if (r.message && r.message.length) {
                                    frappe.msgprint(__('An Asset already exists.'));
                                    return;
                                }

                                // Create Asset
                                frappe.call({
                                    method: "frappe.client.insert",
                                    args: {
                                        doc: {
                                            doctype: "Asset",
                                            item_code: values.item_code,
                                            asset_name: frm.doc.project_name,
                                            purchase_date: frm.doc.expected_end_date || frappe.datetime.get_today(),
                                            gross_purchase_amount: gross_purchase_amount,
                                            custom_project_: frm.doc.name,
                                            cost_center: frm.doc.cost_center,
                                            company: frm.doc.company,
                                            is_existing_asset: 1,
                                            location: values.location
                                        }
                                    },
                                    callback: function(asset) {

                                        if (!asset.message) return;

                                        let asset_name = asset.message.name;

                                        frappe.msgprint(
                                            __('Asset {0} created successfully.', [asset_name])
                                        );

                                        // Create Journal Entry
                                        frappe.call({
                                            method: "frappe.client.insert",
                                            args: {
                                                doc: {
                                                    doctype: "Journal Entry",
                                                    posting_date: frappe.datetime.get_today(),
                                                    company: frm.doc.company,
                                                    project: frm.doc.name,
                                                    accounts: [
                                                        {
                                                            account: "CWIP Account - VF",
                                                            credit_in_account_currency: gross_purchase_amount
                                                        },
                                                        {
                                                            account: "Buildings - VF",
                                                            debit_in_account_currency: gross_purchase_amount,
                                                            reference_type: "Asset",
                                                            reference_name: asset_name,
                                                            project: frm.doc.name
                                                        }
                                                    ]
                                                }
                                            },
                                            callback: function(je) {

                                                if (je.message) {
                                                    frappe.msgprint(
                                                        __('Journal Entry {0} created successfully.', [je.message.name])
                                                    );
                                                }
                                            }
                                        });

                                    }
                                });

                            }
                        });

                    },
                    __('Create Asset'),
                    __('Create'));

                }
            );

        }, __('Actions'));
    }
}

function calculate_and_set_custom_total_project_cost(frm) {

    if (frm.doc.project_type !== "Capital Work in Progress")
        return;

    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "GL Entry",
            filters: {
                project: frm.doc.name,
                account: "410010 - Capital Work in Progress - VFL"
            },
            fields: [
                "debit_in_account_currency",
                "credit_in_account_currency"
            ]
        },
        callback: function(r) {

            let total = 0;

            if (r.message) {
                r.message.forEach(function(entry) {
                    total +=
                        (entry.debit_in_account_currency || 0) -
                        (entry.credit_in_account_currency || 0);
                });
            }

            frm.set_value("custom_total_project_cost", total);
        }
    });
}