
frappe.ui.form.on('BOM', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            update_custom_cost(frm);
        }
    },
    item: function(frm) {
        update_custom_cost(frm);
    }
});

frappe.ui.form.on('BOM Operation', {
    operations_add: function(frm, cdt, cdn) {
        update_custom_cost(frm, cdt, cdn);
    },
    operation: function(frm, cdt, cdn) {
        update_custom_cost(frm, cdt, cdn);
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
