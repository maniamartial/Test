

frappe.ui.form.on('Opportunity Item', {

    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        
        if (row.item_code && frm.doc.custom_price_list) {
            frappe.call({
                method: "nl_apex.apex_piping.overrides.opportunity.get_price_list_rate",
                args: {
                    item_code: row.item_code,
                    price_list: frm.doc.custom_price_list,
                    customer: frm.doc.party_name,
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'price_list_rate', r.message);
                        frappe.model.set_value(cdt, cdn, 'base_rate', r.message);
                        frappe.model.set_value(cdt, cdn, 'rate', r.message);
                        frm.refresh_fields();
                    }
                }
            });
        }
    }
});
