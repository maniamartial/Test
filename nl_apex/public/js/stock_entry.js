frappe.ui.form.on('Stock Entry', {

	
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
