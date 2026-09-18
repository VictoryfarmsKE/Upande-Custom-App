// Copyright (c) 2024, Upande Ltd and contributors
// For license information, please see license.txt


frappe.provide("erpnext.accounts.dimensions");
// erpnext.buying.setup_buying_controller();
// {% include 'erpnext/public/js/controllers/buying.js' %};

frappe.ui.form.on('Requisition Form', {
	setup: function(frm) {
		frm.custom_make_buttons = {
			'Stock Entry': 'Issue Material',
			'Pick List': 'Pick List',
			'Purchase Order': 'Purchase Order',
			'Request for Quotation': 'Request for Quotation',
			'Supplier Quotation': 'Supplier Quotation',
			'Work Order': 'Work Order',
			'Purchase Receipt': 'Purchase Receipt',
			"Purchase Request": "Requisition Form"
		};

		// formatter for material request item - red flags a fuel line still missing its asset,
		// since the grid cannot show an asterisk on a field only some rows must fill
		frm.set_indicator_formatter('item_code', function(doc) {
			if (upande_is_fuel_group(doc.item_group) && !doc.asset
				&& frm.doc.material_request_type === "Material Issue") {
				return "red";
			}
			return (doc.stock_qty<=doc.ordered_qty) ? "green" : "orange";
		});

		frm.set_query("item_code", "items", function() {
			return {
				query: "erpnext.controllers.queries.item_query"
			};
		});

		frm.set_query("from_warehouse", "items", function(doc) {
			return {
				filters: {'company': doc.company}
			};
		});

		frm.set_query("bom_no", "items", function(doc, cdt, cdn) {
			var row = locals[cdt][cdn];
			return {
				filters: {
					"item": row.item_code
				}
			}
		});

		// Fuel lines may only be charged to fuel-consuming assets; other lines keep the default search.
		frm.set_query("asset", "items", function(doc, cdt, cdn) {
			const row = locals[cdt][cdn];
			if (upande_is_fuel_group(row.item_group)) {
				return {
					query: "upande_vf_custom.custom_scripts.fuel_asset.fuel_asset_query",
					filters: { company: doc.company }
				};
			}
		});
		// same condition as the field's mandatory_depends_on
		frm.upande_asset_required = row => upande_is_fuel_group(row.item_group)
			&& frm.doc.material_request_type === "Material Issue" && !!row.__islocal;
		upande_load_fuel_item_groups();
		upande_mark_required_asset_cells();
		upande_route_fuel_asset_dimension_query();
	},

	onload: function(frm) {
		// add item, if previous view was item
		erpnext.utils.add_item(frm);

		// set schedule_date
		set_schedule_date(frm);

		frm.set_query("warehouse", "items", function(doc) {
			return {
				filters: {'company': doc.company}
			};
		});

		frm.set_query("set_warehouse", function(doc){
			return {
				filters: {'company': doc.company}
			};
		});

		frm.set_query("set_from_warehouse", function(doc){
			return {
				filters: {'company': doc.company}
			};
		});

		erpnext.accounts.dimensions.setup_dimension_filters(frm, frm.doctype);
	},

	company: function(frm) {
		erpnext.accounts.dimensions.update_dimension(frm, frm.doctype);
	},

	onload_post_render: function(frm) {
		frm.get_field("items").grid.set_multiple_add("item_code", "qty");
	},

	refresh: function(frm) {
		frm.events.make_custom_buttons(frm);
		frm.toggle_reqd('customer', frm.doc.material_request_type=="Customer Provided");
		label_fuel_asset_cells(frm);
	},

	set_from_warehouse: function(frm) {
		if (frm.doc.material_request_type == "Material Transfer"
			&& frm.doc.set_from_warehouse) {
			frm.doc.items.forEach(d => {
				frappe.model.set_value(d.doctype, d.name,
					"from_warehouse", frm.doc.set_from_warehouse);
			})
		}
	},

	make_custom_buttons: function(frm) {
		if (frm.doc.docstatus==0) {
			frm.add_custom_button(__("Bill of Materials"),
				() => frm.events.get_items_from_bom(frm), __("Get Items From"));
		}

		if (frm.doc.docstatus == 1 && frm.doc.status != 'Stopped') {
			let precision = frappe.defaults.get_default("float_precision");

			if (flt(frm.doc.per_received, precision) < 100) {
				frm.add_custom_button(__('Stop'),
					() => frm.events.update_status(frm, 'Stopped'));
			}

			if (flt(frm.doc.per_ordered, precision) < 100) {
				let add_create_pick_list_button = () => {
					frm.add_custom_button(__('Pick List'),
						() => frm.events.create_pick_list(frm), __('Create'));
				}

				if (frm.doc.material_request_type === "Material Transfer") {
					add_create_pick_list_button();
					frm.add_custom_button(__("Material Transfer"),
						() => frm.events.make_stock_entry(frm), __('Create'));

					frm.add_custom_button(__("Material Transfer (In Transit)"),
						() => frm.events.make_in_transit_stock_entry(frm), __('Create'));
				}

				if (frm.doc.material_request_type === "Material Issue") {
					frm.add_custom_button(__("Issue Material"),
						() => frm.events.make_stock_entry(frm), __('Create'));

					// Add Purchase Request button under Create for Material Issue
					frm.add_custom_button(__("Purchase Request"),() => frm.events.make_purchase_request_from_material_issue(frm), __('Create'));
				}

				if (frm.doc.material_request_type === "Customer Provided") {
					frm.add_custom_button(__("Material Receipt"),
						() => frm.events.make_stock_entry(frm), __('Create'));
				}

				if (frm.doc.material_request_type === "Purchase") {
					frm.add_custom_button(__('Purchase Order'),
						() => frm.events.make_purchase_order(frm), __('Create'));
				}

				if (frm.doc.material_request_type === "Purchase") {
					frm.add_custom_button(__("Request for Quotation"),
						() => frm.events.make_request_for_quotation(frm), __('Create'));
				}

				if (frm.doc.material_request_type === "Purchase") {
					frm.add_custom_button(__("Supplier Quotation"),
						() => frm.events.make_supplier_quotation(frm), __('Create'));
				}

				if (frm.doc.material_request_type === "Manufacture") {
					frm.add_custom_button(__("Work Order"),
						() => frm.events.raise_work_orders(frm), __('Create'));
				}

				frm.page.set_inner_btn_group_as_primary(__('Create'));
			}
		}

		if (frm.doc.docstatus===0) {
			frm.add_custom_button(__('Sales Order'), () => frm.events.get_items_from_sales_order(frm),
				__("Get Items From"));
		}

		if (frm.doc.docstatus == 1 && frm.doc.status == 'Stopped') {
			frm.add_custom_button(__('Re-open'), () => frm.events.update_status(frm, 'Submitted'));
		}
	},

	update_status: function(frm, stop_status) {
		frappe.call({
			method: 'erpnext.stock.doctype.requisition_form.requisition_form.update_status',
			args: { name: frm.doc.name, status: stop_status },
			callback(r) {
				if (!r.exc) {
					frm.reload_doc();
				}
			}
		});
	},

	get_items_from_sales_order: function(frm) {
		erpnext.utils.map_current_doc({
			method: "erpnext.selling.doctype.sales_order.sales_order.make_material_request",
			source_doctype: "Sales Order",
			target: frm,
			setters: {
				customer: frm.doc.customer || undefined,
				delivery_date: undefined,
			},
			get_query_filters: {
				docstatus: 1,
				status: ["not in", ["Closed", "On Hold"]],
				per_delivered: ["<", 99.99],
				company: frm.doc.company
			}
		});
	},

	get_item_data: function(frm, item, overwrite_warehouse=false) {
		if (item && !item.item_code) { return; }
		frm.call({
			method: "erpnext.stock.get_item_details.get_item_details",
			child: item,
			args: {
				args: {
					item_code: item.item_code,
					from_warehouse: item.from_warehouse,
					warehouse: item.warehouse,
					doctype: frm.doc.doctype,
					buying_price_list: frappe.defaults.get_default('buying_price_list'),
					currency: frappe.defaults.get_default('Currency'),
					name: frm.doc.name,
					qty: item.qty || 1,
					stock_qty: item.stock_qty,
					company: frm.doc.company,
					conversion_rate: 1,
					material_request_type: frm.doc.material_request_type,
					plc_conversion_rate: 1,
					rate: item.rate,
					uom: item.uom,
					conversion_factor: item.conversion_factor,
					project: item.project,
				},
				overwrite_warehouse: overwrite_warehouse
			},
			callback: function(r) {
				const d = item;
				const qty_fields = ['actual_qty', 'projected_qty', 'min_order_qty'];

				if(!r.exc) {
					$.each(r.message, function(k, v) {
						if(!d[k] || in_list(qty_fields, k)) d[k] = v;
					});
				}

				label_fuel_asset_cells(frm);
			}
		});
	},

	get_items_from_bom: function(frm) {
		var d = new frappe.ui.Dialog({
			title: __("Get Items from BOM"),
			fields: [
				{"fieldname":"bom", "fieldtype":"Link", "label":__("BOM"),
					options:"BOM", reqd: 1, get_query: function() {
						return {filters: { docstatus:1 }};
					}},
				{"fieldname":"warehouse", "fieldtype":"Link", "label":__("For Warehouse"),
					options:"Warehouse", reqd: 1},
				{"fieldname":"qty", "fieldtype":"Float", "label":__("Quantity"),
					reqd: 1, "default": 1},
				{"fieldname":"fetch_exploded", "fieldtype":"Check",
					"label":__("Fetch exploded BOM (including sub-assemblies)"), "default":1}
			],
			primary_action_label: 'Get Items',
			primary_action(values) {
				if(!values) return;
				values["company"] = frm.doc.company;
				if(!frm.doc.company) frappe.throw(__("Company field is required"));
				frappe.call({
					method: "erpnext.manufacturing.doctype.bom.bom.get_bom_items",
					args: values,
					callback: function(r) {
						if (!r.message) {
							frappe.throw(__("BOM does not contain any stock item"));
						} else {
							erpnext.utils.remove_empty_first_row(frm, "items");
							$.each(r.message, function(i, item) {
								var d = frappe.model.add_child(cur_frm.doc, "Requisition Form Item", "items");
								d.item_code = item.item_code;
								d.item_name = item.item_name;
								d.description = item.description;
								d.warehouse = values.warehouse;
								d.uom = item.stock_uom;
								d.stock_uom = item.stock_uom;
								d.conversion_factor = 1;
								d.qty = item.qty;
								d.project = item.project;
							});
						}
						d.hide();
						refresh_field("items");
					}
				});
			}
		});

		d.show();
	},

	make_purchase_order: function(frm) {
		frappe.prompt(
			{
				label: __('For Default Supplier (Optional)'),
				fieldname:'default_supplier',
				fieldtype: 'Link',
				options: 'Supplier',
				description: __('Select a Supplier from the Default Suppliers of the items below. On selection, a Purchase Order will be made against items belonging to the selected Supplier only.'),
				get_query: () => {
					return{
						query: "upande_vf_custom.upande_vf_custom.doctype.requisition_form.requisition_form.get_default_supplier_query",
						filters: {'doc': frm.doc.name}
					}
				}
			},
			(values) => {
				frappe.model.open_mapped_doc({
					method: "upande_vf_custom.upande_vf_custom.doctype.requisition_form.requisition_form.make_purchase_order",
					frm: frm,
					args: { default_supplier: values.default_supplier },
					run_link_triggers: true
				});
			},
			__('Enter Supplier'),
			__('Create')
		)
	},

	make_request_for_quotation: function(frm) {
		frappe.model.open_mapped_doc({
			method: "upande_vf_custom.upande_vf_custom.doctype.requisition_form.requisition_form.make_request_for_quotation",
			frm: frm,
			run_link_triggers: true
		});
	},

	make_supplier_quotation: function(frm) {
		frappe.model.open_mapped_doc({
			method: "upande_vf_custom.upande_vf_custom.doctype.requisition_form.requisition_form.make_supplier_quotation",
			frm: frm
		});
	},

	make_stock_entry: function(frm) {
		frappe.model.open_mapped_doc({
			method: "upande_vf_custom.upande_vf_custom.doctype.requisition_form.requisition_form.make_stock_entry",
			frm: frm
		});
	},

	make_purchase_request_from_material_issue: function(frm) {
		frappe.model.open_mapped_doc({
            method: "upande_vf_custom.upande_vf_custom.doctype.requisition_form.requisition_form.make_purchase_request_from_material_issue",
            frm: frm
        });
	},	

	make_in_transit_stock_entry(frm) {
		frappe.prompt(
			[
				{
					label: __('In Transit Warehouse'),
					fieldname: 'in_transit_warehouse',
					fieldtype: 'Link',
					options: 'Warehouse',
					reqd: 1,
					get_query: () => {
						return{
							filters: {
								'company': frm.doc.company,
								'is_group': 0,
								'warehouse_type': 'Transit'
							}
						}
					}
				}
			],
			(values) => {
				frappe.call({
					method: "upande_vf_custom.upande_vf_custom.doctype.requisition_form.requisition_form.make_in_transit_stock_entry",
					args: {
						source_name: frm.doc.name,
						in_transit_warehouse: values.in_transit_warehouse
					},
					callback: function(r) {
						if (r.message) {
							let doc = frappe.model.sync(r.message);
							frappe.set_route('Form', doc[0].doctype, doc[0].name);
						}
					}
				})
			},
			__('In Transit Transfer'),
			__("Create Stock Entry")
		)
	},

	create_pick_list: (frm) => {
		frappe.model.open_mapped_doc({
			method: "upande_vf_custom.upande_vf_custom.doctype.requisition_form.requisition_form.create_pick_list",
			frm: frm
		});
	},

	raise_work_orders: function(frm) {
		frappe.call({
			method:"upande_vf_custom.upande_vf_custom.doctype.requisition_form.requisition_form.raise_work_orders",
			args: {
				"material_request": frm.doc.name
			},
			freeze: true,
			callback: function(r) {
				if(r.message.length) {
					frm.reload_doc();
				}
			}
		});
	},
	material_request_type: function(frm) {
		frm.toggle_reqd('customer', frm.doc.material_request_type=="Customer Provided");

		if (frm.doc.material_request_type !== 'Material Transfer' && frm.doc.set_from_warehouse) {
			frm.set_value('set_from_warehouse', '');
		}
	},

});

frappe.ui.form.on("Requisition Form Item", {
	asset: function(frm, doctype, name) {
		upande_sync_asset_prompt(frm, locals[doctype][name]);
	},

	qty: function (frm, doctype, name) {
		const item = locals[doctype][name];
		if (flt(item.qty) < flt(item.min_order_qty)) {
			frappe.msgprint(__("Warning: Material Requested Qty is less than Minimum Order Qty"));
		}
		frm.events.get_item_data(frm, item, false);
	},

	from_warehouse: function(frm, doctype, name) {
		const item = locals[doctype][name];
		frm.events.get_item_data(frm, item, false);
	},

	warehouse: function(frm, doctype, name) {
		const item = locals[doctype][name];
		frm.events.get_item_data(frm, item, false);
	},

	rate: function(frm, doctype, name) {
		const item = locals[doctype][name];
		frm.events.get_item_data(frm, item, false);
	},

	item_code: function(frm, doctype, name) {
		const item = locals[doctype][name];
		item.rate = 0;
		item.uom = '';
		set_schedule_date(frm);
		frm.events.get_item_data(frm, item, true);
	},

	schedule_date: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.schedule_date) {
			if(!frm.doc.schedule_date) {
				erpnext.utils.copy_value_in_all_rows(frm.doc, cdt, cdn, "items", "schedule_date");
			} else {
				set_schedule_date(frm);
			}
		}
	}
});

// erpnext.buying.RequisitionFormController = class RequisitionFormController extends erpnext.buying.BuyingController {
// 	tc_name() {
// 		this.get_terms();
// 	}

// 	item_code() {
// 		// to override item code trigger from transaction.js
// 	}

// 	validate_company_and_party() {
// 		return true;
// 	}

// 	calculate_taxes_and_totals() {
// 		return;
// 	}

// 	validate() {
// 		set_schedule_date(this.frm);
// 	}

// 	onload() {
// 		this.frm.set_query("item_code", "items", function(doc, cdt, cdn) {
// 			if (doc.material_request_type == "Customer Provided") {
// 				return{
// 					query: "erpnext.controllers.queries.item_query",
// 					filters:{
// 						'customer': doc.customer,
// 						'is_stock_item':1
// 					}
// 				}
// 			} else if (doc.material_request_type == "Purchase") {
// 				return{
// 					query: "erpnext.controllers.queries.item_query",
// 					filters: {'is_purchase_item': 1}
// 				}
// 			} else {
// 				return{
// 					query: "erpnext.controllers.queries.item_query",
// 					filters: {'is_stock_item': 1}
// 				}
// 			}
// 		});
// 	}

// 	items_add(doc, cdt, cdn) {
// 		var row = frappe.get_doc(cdt, cdn);
// 		if(doc.schedule_date) {
// 			row.schedule_date = doc.schedule_date;
// 			refresh_field("schedule_date", cdn, "items");
// 		} else {
// 			this.frm.script_manager.copy_from_first_row("items", row, ["schedule_date"]);
// 		}
// 	}

// 	items_on_form_rendered() {
// 		set_schedule_date(this.frm);
// 	}

// 	schedule_date() {
// 		set_schedule_date(this.frm);
// 	}
// };

// // // for backward compatibility: combine new and previous states
// extend_cscript(cur_frm.cscript, new erpnext.buying.RequisitionFormController({frm: cur_frm}));

// Each grid row keeps its own copy of the docfield, so fuel rows can ask for the asset by name
// while other rows keep the plain label.
function label_fuel_asset_cells(frm) {
	(frm.doc.items || []).forEach(row => {
		const df = frappe.meta.get_docfield("Requisition Form Item", "asset", row.name);
		if (df) {
			df.placeholder = upande_is_fuel_group(row.item_group) ? __("Asset required") : "";
		}
		upande_sync_asset_prompt(frm, row);
	});
}

function set_schedule_date(frm) {
	if(frm.doc.schedule_date){
		erpnext.utils.copy_value_in_all_rows(frm.doc, frm.doc.doctype, frm.doc.name, "items", "schedule_date");
	}
}

// Frappe only paints the red asterisk in a grid's heading row, and Asset cannot carry one there -
// it is required on fuel lines only. Draw it on the rows that actually need it.
window.upande_mark_required_asset_cells = window.upande_mark_required_asset_cells || function () {
	if (document.getElementById("upande-asset-reqd-asterisk")) return;
	const style = document.createElement("style");
	style.id = "upande-asset-reqd-asterisk";
	// Frappe marks a cell .error only while it is required and still empty, so the asterisk goes
	// away the moment an asset is picked.
	style.textContent = `.grid-body .grid-static-col[data-fieldname="asset"].error .static-area:after {
		content: " *";
		color: var(--red-400);
	}
	/* A native placeholder takes a single colour, so on a row being edited the prompt is drawn
	   as real text behind the (transparent) input - grey words, red asterisk. */
	.grid-static-col[data-fieldname="asset"] .field-area {
		position: relative;
	}
	.grid-static-col[data-fieldname="asset"] .upande-asset-prompt {
		position: absolute;
		left: 8px;
		top: 50%;
		transform: translateY(-50%);
		color: var(--text-muted);
		pointer-events: none;
		white-space: nowrap;
	}
	.grid-static-col[data-fieldname="asset"] .upande-asset-prompt .reqd-star {
		color: var(--red-400);
	}`;
	document.head.appendChild(style);

	// The inline editor builds its input when a row is opened, so decorate on the way in too.
	$(document).on("focusin click", '.grid-static-col[data-fieldname="asset"]', function () {
		const docname = $(this).closest(".grid-row").attr("data-name");
		const frm = window.cur_frm;
		const row = frm && (frm.doc.items || []).find(item => item.name === docname);
		if (row) setTimeout(() => upande_sync_asset_prompt(frm, row), 0);
	});
};

// Bring one row's Asset cell in line with what the row needs right now - called whenever the item,
// its group or the asset changes, so an already-open row updates without being redrawn.
window.upande_sync_asset_prompt = window.upande_sync_asset_prompt || function (frm, row) {
	const grid = frm.fields_dict.items && frm.fields_dict.items.grid;
	const grid_row = grid && grid.grid_rows_by_docname && grid.grid_rows_by_docname[row.name];
	const cell = grid_row && grid_row.columns && grid_row.columns.asset;
	if (!cell) return;

	const needed = !!(frm.upande_asset_required && frm.upande_asset_required(row)) && !row.asset;
	cell.toggleClass("error", needed);

	const area = cell[0].querySelector(".field-area");
	const input = area && area.querySelector("input");
	if (!input) return;

	let prompt = area.querySelector(".upande-asset-prompt");
	if (needed && !prompt) {
		prompt = document.createElement("span");
		prompt.className = "upande-asset-prompt";
		prompt.innerHTML = `${frappe.utils.escape_html(__("Asset required"))} <span class="reqd-star">*</span>`;
		area.appendChild(prompt);
		$(input).on("input blur", () => { prompt.hidden = !!input.value; });
	}
	if (prompt) prompt.hidden = !needed || !!input.value;
	input.placeholder = needed ? "" : __("Asset");
};

// The Fuel item group and anything under it, fetched once so the form agrees with the server.
window.upande_is_fuel_group = window.upande_is_fuel_group || function (item_group) {
	return (window.upande_fuel_item_groups || ["Fuel"]).includes(item_group);
};

window.upande_load_fuel_item_groups = window.upande_load_fuel_item_groups || function () {
	if (window.upande_fuel_item_groups) return;
	frappe.xcall("upande_vf_custom.custom_scripts.fuel_asset.get_fuel_item_groups")
		.then(groups => { window.upande_fuel_item_groups = groups; });
};

// Asset is an Accounting Dimension on Victory Farms sites. ERPNext's dimension setup registers
// its own `asset` query asynchronously after onload, replacing the one set above, and that
// query resolves through erpnext.queries.get_filtered_dimensions when the picker opens - so
// fuel lines are routed to the fuel asset search there. Twin of client_scripts/stock_entry.js.
window.upande_route_fuel_asset_dimension_query = window.upande_route_fuel_asset_dimension_query || function () {
	if (!window.erpnext || !erpnext.queries || erpnext.queries.__fuel_asset_routed) return;
	const original = erpnext.queries.get_filtered_dimensions;
	erpnext.queries.get_filtered_dimensions = function (doc, child_fields, dimension, company) {
		if (
			dimension === "asset" &&
			doc && upande_is_fuel_group(doc.item_group) &&
			["Requisition Form Item", "Stock Entry Detail"].includes(doc.doctype)
		) {
			return {
				query: "upande_vf_custom.custom_scripts.fuel_asset.fuel_asset_query",
				filters: { company: company },
			};
		}
		return original.apply(this, arguments);
	};
	erpnext.queries.__fuel_asset_routed = true;
};
