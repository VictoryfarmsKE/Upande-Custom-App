// frappe.ui.form.on('Stock Entry', {
//     stock_entry_type(frm){
//         frappe.call({
//             method: 'upande_vf_custom.custom_scripts.server_scripts.stock_entry.add_hcf',
//             args: {
//                 message: {
//                     doc: frm.doc
//                 }
//             },
//             btn: $('.primary-action'),
//             freeze: true,
//             callback: (r) => {
//                 if(r.message){
//                     data = r.message

//                     frm.refresh_field("items")

//                 }
                               
//             }
//         })
//     }
// })

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
// its own `asset` query asynchronously, replacing the one set below, and that query resolves
// through erpnext.queries.get_filtered_dimensions when the picker opens - so fuel lines are
// routed to the fuel asset search there. Twin of doctype/requisition_form/requisition_form.js.
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

// Each grid row keeps its own copy of the docfield, so fuel rows can ask for the asset by name
// while other rows keep the plain label.
function label_fuel_asset_cells(frm) {
	(frm.doc.items || []).forEach(row => {
		const df = frappe.meta.get_docfield("Stock Entry Detail", "asset", row.name);
		if (df) {
			df.placeholder = upande_is_fuel_group(row.item_group) ? __("Asset required") : "";
		}
		upande_sync_asset_prompt(frm, row);
	});
}

frappe.ui.form.on("Stock Entry", {
	setup(frm) {
		// Fuel lines may only be charged to fuel-consuming assets; other lines keep the default search.
		frm.set_query("asset", "items", function(doc, cdt, cdn) {
			const row = locals[cdt][cdn];
			if (upande_is_fuel_group(row.item_group)) {
				return {
					query: "upande_vf_custom.custom_scripts.fuel_asset.fuel_asset_query",
					filters: { company: doc.company },
				};
			}
		});
		// same condition as the field's mandatory_depends_on
		frm.upande_asset_required = row => upande_is_fuel_group(row.item_group)
			&& frm.doc.purpose === "Material Issue";
		upande_load_fuel_item_groups();
		upande_mark_required_asset_cells();
		upande_route_fuel_asset_dimension_query();
	},

	refresh(frm) {
		label_fuel_asset_cells(frm);
	},
});

frappe.ui.form.on("Stock Entry Detail", {
	// item_group is fetched from the item, so the prompt is decided once it lands
	item_group(frm) {
		label_fuel_asset_cells(frm);
	},

	asset(frm, cdt, cdn) {
		upande_sync_asset_prompt(frm, locals[cdt][cdn]);
	},
});
