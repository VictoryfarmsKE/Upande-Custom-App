// Copyright (c) 2025, Upande Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Local Payments USD Bank Bulk Upload"] = {
	"filters": [
		{
			fieldname: 'parent',
			label: 'Parent',
			fieldtype: 'Data',
			read_only: 1,
		},
	]
};
