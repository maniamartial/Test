
frappe.ui.form.on('BOM', {
    refresh: function(frm) {
        if(frm.doc.custom_set_cost_per_unit===1){
            if (!frm.is_new()) {
                update_custom_cost(frm);
            }
        }
        
    },
    item: function(frm) {
        if(frm.doc.custom_set_cost_per_unit===1){
        update_custom_cost(frm);
        }
    }
});

frappe.ui.form.on('BOM Operation', {
    operations_add: function(frm, cdt, cdn) {
        if (frm.doc.custom_set_cost_per_unit) {
            update_custom_cost(frm, cdt, cdn);
        }
    },
    operation: function(frm, cdt, cdn) {
        if (frm.doc.custom_set_cost_per_unit) {
            update_custom_cost(frm, cdt, cdn);
        }
    }
});

function update_custom_cost(frm, cdt = null, cdn = null) {
    if (!frm.doc.item) return;

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Item',
            filters: { name: frm.doc.item },
            fieldname: 'custom_cost_per_unit'
        },
        callback: function(response) {
            if(response.message.custom_cost_per_unit == 0){
                frappe.throw(__('Cost per Unit is not set for this item {0}', [frm.doc.item]));
            }
            if (response.message && response.message.custom_cost_per_unit) {
                let cost_per_unit = response.message.custom_cost_per_unit;

                if (cdn) {
                    frappe.model.set_value(cdt, cdn, 'custom_cost_per_kg', cost_per_unit);
                } else {
                    frm.doc.operations.forEach(operation => {
                        frappe.model.set_value(operation.doctype, operation.name, 'custom_cost_per_kg', cost_per_unit);
                    });
                    frm.refresh_field('operations');
                }
            }
        }
    });
}
