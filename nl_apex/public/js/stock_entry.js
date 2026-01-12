frappe.ui.form.on('Stock Entry', {
	refresh: function(frm) {
		// Clear set_basic_rate_manually for repack finished items when custom_bypass_repack is enabled
		if (frm.doc.purpose === "Repack" && frm.doc.custom_bypass_repack) {
			frm.doc.items.forEach(function(item) {
				if (item.is_finished_item && item.t_warehouse) {
					item.set_basic_rate_manually = 0;
				}
			});
			frm.refresh_field("items");
		}
	},
	
	after_save: function(frm) {
		// After save, recalculate basic_rate for repack finished items if bypass is enabled
		if (frm.doc.purpose === "Repack" && frm.doc.custom_bypass_repack && !frm.doc.__islocal) {
			frappe.call({
				method: "nl_apex.apex_piping.overrides.stock_entry.recalculate_repack_basic_rate",
				args: {
					stock_entry_name: frm.doc.name
				},
				callback: function(r) {
					if (r.message && r.message.success) {
						// Reload the form to show updated rates
						frm.reload_doc();
					}
				}
			});
		}
	},
	
	items_add: function(frm, cdt, cdn) {
		// When items are added, clear set_basic_rate_manually for repack finished items
		if (frm.doc.purpose === "Repack" && frm.doc.custom_bypass_repack) {
			let item = frappe.get_doc(cdt, cdn);
			if (item.is_finished_item && item.t_warehouse) {
				item.set_basic_rate_manually = 0;
				frm.refresh_field("items");
			}
		}
	},
	
	custom_bypass_repack: function(frm) {
		// When custom_bypass_repack is toggled, update set_basic_rate_manually for finished items
		if (frm.doc.purpose === "Repack" && frm.doc.custom_bypass_repack) {
			frm.doc.items.forEach(function(item) {
				if (item.is_finished_item && item.t_warehouse) {
					item.set_basic_rate_manually = 0;
				}
			});
			frm.refresh_field("items");
		}
	}
});

frappe.ui.form.on('Stock Entry Detail', {
	set_basic_rate_manually: function(frm, cdt, cdn) {
		// Prevent set_basic_rate_manually from being set to 1 for repack finished items
		// when custom_bypass_repack is enabled
		if (frm.doc.purpose === "Repack" && frm.doc.custom_bypass_repack) {
			let item = frappe.get_doc(cdt, cdn);
			if (item.is_finished_item && item.t_warehouse && item.set_basic_rate_manually) {
				item.set_basic_rate_manually = 0;
				frm.refresh_field("items");
			}
		}
	},
	
	basic_rate: function(frm, cdt, cdn) {
		// When basic_rate is manually changed, prevent set_basic_rate_manually from being set
		// for repack finished items when custom_bypass_repack is enabled
		if (frm.doc.purpose === "Repack" && frm.doc.custom_bypass_repack) {
			let item = frappe.get_doc(cdt, cdn);
			if (item.is_finished_item && item.t_warehouse) {
				item.set_basic_rate_manually = 0;
				frm.refresh_field("items");
			}
		}
	}
});
