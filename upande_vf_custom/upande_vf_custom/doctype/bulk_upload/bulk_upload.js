// Copyright (c) 2024, Upande Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bulk Upload', {
    refresh(frm) {
        setTimeout(() => calculate_total_amount(frm), 300);
    },
    
	get_draft_payments(frm) {
        frappe.call({
            method: 'get_pending_payments',
            doc: frm.doc,
            btn: $('.primary-action'),
            freeze: true,
            callback: (r) => {
                if (r.message) {
                    if(frm.doc.type=="EFT NCBA"){
                        processEFTNCBADraftPayments(frm, r.message.draft_payments, r.message.total_grand_total);
                    }
                     if(frm.doc.type=="EFT STANBIC BANK"){
                        processEFTStanbicDraftPayments(frm, r.message.draft_payments, r.message.total_grand_total);
                    }
                    // else if(frm.doc.type=="RTGS"){
                    //     processRTGSDraftPayments(frm, r.message.draft_payments, r.message.total_grand_total);
                    // }
                    // else if(frm.doc.type=="International Payments"){
                    //     processIPDraftPayments(frm, r.message.draft_payments, r.message.total_grand_total);
                    // }
                    else if(frm.doc.type=="RTGS NCBA"){
                        processRTGSNCBADraftPayments(frm, r.message.draft_payments, r.message.total_grand_total);
                    }
                    else if(frm.doc.type=="RTGS STANBIC BANK"){
                        processRTGSStanbicDraftPayments(frm, r.message.draft_payments, r.message.total_grand_total);
                    }
                    else if(frm.doc.type=="Local Payments USD"){
                        processLocalUSDDraftPayments(frm, r.message.draft_payments, r.message.total_grand_total);
                    }
                    else if(frm.doc.type=="International Payments USD"){
                        processIPUSDDraftPayments(frm, r.message.draft_payments, r.message.total_grand_total);
                    }
                    else if(frm.doc.type=="International Payments ZAR"){
                        processIPZARDraftPayments(frm, r.message.draft_payments, r.message.total_grand_total);
                    }
                    else if(frm.doc.type=="International Payments EUR"){
                        processIPEURDraftPayments(frm, r.message.draft_payments, r.message.total_grand_total);
                    }
                    else if(frm.doc.type=="International Payments GBP"){
                        processIPGBPDraftPayments(frm, r.message.draft_payments, r.message.total_grand_total);
                    }
                    else if(frm.doc.type=="International Payments RWF"){
                        processIPRWFDraftPayments(frm, r.message.draft_payments, r.message.total_grand_total);
                    }
                    else if(frm.doc.type=="Mpesa"){
                        processMpesaDraftPayments(frm, r.message.draft_payments, r.message.total_grand_total);
                    }
                    
                    
                } else {
                    console.log("No Draft Payments Match The Criteria.");
                }
            },
            error: (r) => {
                console.error("Error", r);
                // Handle the error here
            }
        })
    },
    
    download(frm) {
        frappe.call({
            method: 'download_report',
            doc: frm.doc,
            callback: function(r) {
                if(r.message) {
                    window.open(r.message);
                }
            }
        });
        
    },
    
    mpesa_bulk_upload_items_add: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    mpesa_bulk_upload_items_remove: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    eft_bulk_upload_items_add: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    eft_bulk_upload_items_remove: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    eft_ncba_bulk_upload_items_add: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    eft_ncba_bulk_upload_items_remove: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    eft_stanbic_bulk_upload_items_add: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    eft_stanbic_bulk_upload_items_remove: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    rtgs_bulk_upload_items_add: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    rtgs_bulk_upload_items_remove: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    rtgs_ncba_bulk_upload_items_add: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    rtgs_ncba_bulk_upload_items_remove: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    rtgs_stanbic_bulk_upload_items_add: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    rtgs_stanbic_bulk_upload_items_remove: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    international_payments_bulk_upload_items_add: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    international_payments_bulk_upload_items_remove: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    local_payments_usd_bulk_upload_items_add: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    local_payments_usd_bulk_upload_items_remove: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    international_payments_usd_bulk_upload_items_add: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    international_payments_usd_bulk_upload_items_remove: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    international_payments_zar_bulk_upload_items_add: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    international_payments_zar_bulk_upload_items_remove: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    international_payments_eur_bulk_upload_items_add: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    international_payments_eur_bulk_upload_items_remove: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    international_payments_gbp_bulk_upload_items_add: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    international_payments_gbp_bulk_upload_items_remove: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    international_payments_rwf_bulk_upload_items_add: function(frm, cdt, cdn) { calculate_total_amount(frm); },
    international_payments_rwf_bulk_upload_items_remove: function(frm, cdt, cdn) { calculate_total_amount(frm); }
});

function calculate_total_amount(frm) {
    if (!frm.doc.type) return;
    
    let child_table_field = '';
    let amount_field = 'amount';
    
    switch(frm.doc.type) {
        case 'Mpesa':
            child_table_field = 'mpesa_bulk_upload_items';
            break;
        case 'EFT':
            child_table_field = 'eft_bulk_upload_items';
            break;
        case 'EFT NCBA':
            child_table_field = 'eft_ncba_bulk_upload_items';
            break;
        case 'EFT STANBIC BANK':
            child_table_field = 'eft_stanbic_bulk_upload_items';
            break;
        case 'RTGS':
            child_table_field = 'rtgs_bulk_upload_items';
            break;
        case 'RTGS NCBA':
            child_table_field = 'rtgs_ncba_bulk_upload_items';
            break;
        case 'RTGS STANBIC BANK':
            child_table_field = 'rtgs_stanbic_bulk_upload_items';
            break;
        case 'International Payments':
            child_table_field = 'international_payments_bulk_upload_items';
            amount_field = 'debit_amount';
            break;
        case 'Local Payments USD':
            child_table_field = 'local_payments_usd_bulk_upload_items';
            amount_field = 'debit_amount';
            break;
        case 'International Payments USD':
            child_table_field = 'international_payments_usd_bulk_upload_items';
            amount_field = 'debit_amount';
            break;
        case 'International Payments ZAR':
            child_table_field = 'international_payments_zar_bulk_upload_items';
            amount_field = 'debit_amount';
            break;
        case 'International Payments EUR':
            child_table_field = 'international_payments_eur_bulk_upload_items';
            amount_field = 'debit_amount';
            break;
        case 'International Payments GBP':
            child_table_field = 'international_payments_gbp_bulk_upload_items';
            amount_field = 'debit_amount';
            break;
        case 'International Payments RWF':
            child_table_field = 'international_payments_rwf_bulk_upload_items';
            amount_field = 'debit_amount';
            break;
    }
    
    if (!child_table_field) return;
    
    let total = 0;
    const rows = frm.doc[child_table_field] || [];
    rows.forEach(row => {
        total += flt(row[amount_field]);
    });
    
    frm.doc.custom_total_amount = total;
    frm.refresh_field('custom_total_amount');
}


// Rebuilds a child table so it mirrors exactly the draft Payment Entries the
// server returned. Rows whose Payment Entry is no longer draft (submitted or
// cancelled) are removed on every "Get Draft Payments" click.
function syncDraftPayments(frm, childTableField, draftPymnts, mapRow) {
    frm.clear_table(childTableField);
    (draftPymnts || []).forEach(dp => {
        let newRow = frm.add_child(childTableField);
        mapRow(newRow, dp);
    });
    frm.refresh_field(childTableField);
    calculate_total_amount(frm);
    frm.save();
}

function mapBankDraftRow(newRow, dp) {
    newRow.payment_reference = dp.name;
    newRow.beneficiary_name = dp.custom_account_name;
    newRow.bank_account = dp.party_bank_account;
    newRow.reference = dp.reference_no;
    newRow.bank = dp.bank_name;
    newRow.amount = dp.paid_amount;
}

function mapInternationalDraftRow(newRow, dp) {
    newRow.payment_reference = dp.name;
    newRow.beneficiary_name = dp.custom_account_name;
    newRow.beneficiary_account = dp.bank_account;
    newRow.reference = dp.name;
    newRow.beneficiary_email_id = dp.contact_email;
    newRow.debit_amount = dp.paid_amount;
    newRow.swift_code = dp.swift_code;
    newRow.payment_type = dp.custom_upload_type;
}

function processEFTNCBADraftPayments(frm, draftPymnts, total_grand_total) {
    syncDraftPayments(frm, 'eft_ncba_bulk_upload_items', draftPymnts, mapBankDraftRow);
}

function processEFTStanbicDraftPayments(frm, draftPymnts, total_grand_total) {
    syncDraftPayments(frm, 'eft_stanbic_bulk_upload_items', draftPymnts, mapBankDraftRow);
}

// function processRTGSDraftPayments(frm, draftPymnts) {
//     const childTableField = 'rtgs_bulk_upload_items'; 

//     const existingPymnts = new Set(frm.doc[childTableField].map(row => row.payment_reference));
//     draftPymnts.forEach(dp => {
//          if (!existingPymnts.has(dp.name)) {
//             let newRow = frm.add_child(childTableField);
//             newRow.payment_reference = dp.name; 
//             newRow.beneficiary_name = dp.custom_account_name;
//             newRow.bank_account = dp.party_bank_account;
//             newRow.reference = dp.reference_no
//             newRow.bank = dp.bank_name
//             newRow.amount = dp.paid_amount;
//             existingPymnts.add(dp.name);
//         }
//     });
    
    
//     frm.refresh_field(childTableField); 
//     frm.save()
// }

function processRTGSNCBADraftPayments(frm, draftPymnts, total_grand_total) {
    syncDraftPayments(frm, 'rtgs_ncba_bulk_upload_items', draftPymnts, function(newRow, dp) {
        mapBankDraftRow(newRow, dp);
        newRow.swift_code = dp.swift_code;
    });
}
function processRTGSStanbicDraftPayments(frm, draftPymnts, total_grand_total) {
    syncDraftPayments(frm, 'rtgs_stanbic_bulk_upload_items', draftPymnts, function(newRow, dp) {
        mapBankDraftRow(newRow, dp);
        newRow.swift_code = dp.swift_code;
    });
}

// function processIPDraftPayments(frm, draftPymnts, total_grand_total) {
//     const childTableField = 'international_payments_bulk_upload_items'; // Update this with the actual field name of your child table

//     // Create a set of existing entries to check for duplicates
//     const existingPymnts = new Set(frm.doc[childTableField].map(row => row.payment_reference)); // Assuming 'payment_reference' is a field in the child table
//     draftPymnts.forEach(dp => {
//          if (!existingPymnts.has(dp.name)) {
//             let newRow = frm.add_child(childTableField);
//             newRow.payment_reference = dp.name;
//             newRow.beneficiary_name = dp.custom_account_name; 
//             newRow.beneficiary_account = dp.bank_account;
//             newRow.reference = dp.name;
//             newRow.beneficiary_email_id = dp.contact_email;
//             newRow.debit_amount = dp.paid_amount;
//             newRow.swift_code = dp.swift_code;
//             newRow.payment_type = dp.custom_upload_type;
//             existingPymnts.add(dp.name); // Add the new purchase order to the set of existing orders
//         }
//     });
    
//     frm.doc.custom_total_amount = total_grand_total
    
//     frm.refresh_field(childTableField); // Refresh the child table field to display the added rows
//     frm.refresh_field('custom_total_amount')
//     frm.save()
// }

function processLocalUSDDraftPayments(frm, draftPymnts, total_grand_total) {
    syncDraftPayments(frm, 'local_payments_usd_bulk_upload_items', draftPymnts, mapInternationalDraftRow);
}

function processIPUSDDraftPayments(frm, draftPymnts, total_grand_total) {
    syncDraftPayments(frm, 'international_payments_usd_bulk_upload_items', draftPymnts, mapInternationalDraftRow);
}

function processIPZARDraftPayments(frm, draftPymnts, total_grand_total) {
    syncDraftPayments(frm, 'international_payments_zar_bulk_upload_items', draftPymnts, mapInternationalDraftRow);
}

function processIPEURDraftPayments(frm, draftPymnts, total_grand_total) {
    syncDraftPayments(frm, 'international_payments_eur_bulk_upload_items', draftPymnts, mapInternationalDraftRow);
}

function processIPGBPDraftPayments(frm, draftPymnts, total_grand_total) {
    syncDraftPayments(frm, 'international_payments_gbp_bulk_upload_items', draftPymnts, mapInternationalDraftRow);
}

function processIPRWFDraftPayments(frm, draftPymnts, total_grand_total) {
    syncDraftPayments(frm, 'international_payments_rwf_bulk_upload_items', draftPymnts, mapInternationalDraftRow);
}

function processMpesaDraftPayments(frm, draftPymnts, total_grand_total) {
    syncDraftPayments(frm, 'mpesa_bulk_upload_items', draftPymnts, function(newRow, dp) {
        newRow.payment_reference = dp.pe_name || dp.name;   // actual PE name for submission
        newRow.beneficiary_name = dp.party;
        newRow.reference = dp.reference_no;
        newRow.amount = dp.paid_amount;
        // Populate beneficiary details from Payment Entry's child table
        newRow.mobilenumber = dp.mobilenumber || '';
        newRow.documenttype = dp.documenttype || '';
        newRow.supplier_invoice = dp.supplier_invoice || '';
        newRow.purposeofpayment = dp.purposeofpayment || '';
    });
}