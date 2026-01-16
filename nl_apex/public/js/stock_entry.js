frappe.ui.form.on('Stock Entry', {
	
	
	purpose: function(frm) {
		// Auto-tick custom_bypass_repack when purpose is set to Repack
		if (frm.doc.purpose === "Repack") {
			frm.set_value("custom_bypass_repack", 1);
		}
	},
	
	before_save: function(frm) {
		// This handles cases where Stock Entry is created directly from Work Order
		if (frm.doc.__islocal && frm.doc.purpose === "Repack" && !frm.doc.custom_bypass_repack) {
			frm.set_value("custom_bypass_repack", 1);
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
	
	
	
});
