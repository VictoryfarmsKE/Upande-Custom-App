const CWIP = "Capital Work in Progress";

frappe.ui.form.on('Project', {
    refresh: function(frm) {
        manage_capex_buttons(frm);
    },

    project_type: function(frm) {
        manage_capex_buttons(frm);
    }
});

function manage_capex_buttons(frm) {

    // Remove existing buttons first to avoid duplicates
    frm.remove_custom_button(__('Create Asset'), __('Actions'));
    frm.remove_custom_button(__('Close Project'), __('Actions'));
    frm.remove_custom_button(__('Budget Variation'), __('Actions'));

    const budget_locked = frm.doc.project_type === CWIP && !frm.is_new()
        && ((frm.doc.workflow_state || '').startsWith('Approved') || !!frm.doc.custom_original_budget);
    frm.set_df_property('custom_budget', 'read_only', budget_locked ? 1 : 0);

    if (frm.is_new() || frm.doc.project_type !== CWIP)
        return;

    if (!frm.doc.custom_project_closure) {
        frm.add_custom_button(__('Budget Variation'), function() {
            frappe.new_doc('Capex Budget Variation', { project: frm.doc.name });
        }, __('Actions'));
        frm.add_custom_button(__('Close Project'), function() {
            frappe.new_doc('Project Closure', { project: frm.doc.name });
        }, __('Actions'));
        return;
    }

    frm.add_custom_button(__('Create Asset'), function() {
        create_asset(frm);
    }, __('Actions'));
}

function create_asset(frm) {

    frappe.prompt([
        {
            label: 'Item Code',
            fieldname: 'item_code',
            fieldtype: 'Link',
            options: 'Item',
            reqd: 1,
            description: 'Select an existing Item Code. Its Asset Category decides the accounts used.',
            get_query: () => ({ filters: { item_group: 'Fixed Assets', is_fixed_asset: 1, disabled: 0 } })
        },
        {
            label: 'Location',
            fieldname: 'location',
            fieldtype: 'Link',
            options: 'Location',
            reqd: 1,
            default: frm.doc.custom_location
        }
    ],
    function(values) {

        frappe.call({
            method: 'upande_vf_custom.capex.project.create_asset_from_project',
            args: {
                project: frm.doc.name,
                item_code: values.item_code,
                location: values.location
            },
            freeze: true,
            freeze_message: __('Creating asset...'),
            callback: function(r) {

                if (!r.message) return;

                frappe.msgprint(
                    __('Asset {0} and draft Journal Entry {1} created for {2}.', [
                        frappe.utils.get_form_link('Asset', r.message.asset, true),
                        frappe.utils.get_form_link('Journal Entry', r.message.journal_entry, true),
                        format_currency(r.message.amount)
                    ])
                );
            }
        });
    },
    __('Create Asset'),
    __('Create'));
}
