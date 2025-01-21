frappe.ui.form.on('Delivery Note', {
    after_save: function(frm) {
        if (!frm.doc.custom_delivery_note_no) { 
            frappe.call({
                method: "nl_apex.apex_piping.overrides.delivery_note.get_series",
                args: {
                    doc_name: frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('custom_delivery_note_no', r.message); 
                        frm.save();
                    }
                }
            });
        }
    }
});
