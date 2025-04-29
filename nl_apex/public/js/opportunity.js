
 
// frappe.ui.form.on("Opportunity Item", "item_code", function(frm, cdt, cdn) {
//     var row = locals[cdt][cdn];

//     frappe.call({
//         method: "frappe.client.get_value",
//         args: {
//             doctype: "Item Price",
//             fieldname: "price_list_rate",
//             filters: {
//                 "item_code": row.item_code,
//                 "price_list": "Standard Selling"
//             }
//         },
//         callback: function(data) {

//             if (data.message && data.message.price_list_rate) {
//                 var price_rate = data.message.price_list_rate;

//                 frappe.model.set_value(cdt, cdn, "base_rate", price_rate);
//                 frappe.model.set_value(cdt, cdn, "rate", price_rate);

//                 frappe.refresh_field("items");
//             } else {
//                 console.log('No price found for the item.');
//             }
//         }
//     });
// });
frappe.ui.form.on("Opportunity Item", {
    item_code: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        if (!row.item_code) return;

        // 1️⃣ Fetch the Item Price
        frappe.call({
            method: "frappe.client.get_value",
            args: {
                doctype: "Item Price",
                fieldname: "price_list_rate",
                filters: {
                    item_code: row.item_code,
                    price_list: "Standard Selling"
                }
            },
            callback: function(data) {
                if (data.message && data.message.price_list_rate) {
                    const price_rate = data.message.price_list_rate;

                    frappe.model.set_value(cdt, cdn, "base_rate", price_rate);
                    frappe.model.set_value(cdt, cdn, "rate", price_rate);

                    frappe.refresh_field("items");
                } else {
                    console.log('No price found for the item.');
                }
            }
        });

        // 2️⃣ Fetch the Free Items (via your custom server method)
        frappe.call({
            method: "nl_apex.apex_piping.overrides.opportunity.get_pricing_rule_for_item",
            args: {
                item_code: row.item_code,
                customer: frm.doc.customer_name,
                transaction_date: frm.doc.transaction_date,
                selling_price_list: frm.doc.custom_selling_price,
                price_list_currency: frm.doc.currency,
                plc_conversion_rate: 1.0,
                conversion_rate: 1.0,
                doctype: frm.doc.doctype,
                name: frm.doc.name,
                company: frm.doc.company,
                qty: row.qty,
                uom: row.uom || row.stock_uom,  // Use row.uom if available, otherwise fall back to stock_uom
                stock_uom: row.stock_uom,
                conversion_factor: 1,
                is_pos: 0,
                is_subcontracted: 0,
                ignore_pricing_rule: 0,
                transaction_type: "selling",
                parent: frm.doc.name,
                parenttype: frm.doc.doctype,
                transaction_type: "selling",
            },
            callback: function(r) {
                if (r.message && r.message.free_item_data) {
                    add_free_items_to_opportunity(frm, r.message.free_item_data);
                }
            }
        });
    }
});

// Enhanced function to add free items
function add_free_items_to_opportunity(frm, free_items, parent_item_code) {
    // Get existing item codes to avoid duplicates
    const existing_items = frm.doc.items || [];
    const existing_item_codes = existing_items.map(item => item.item_code);
    
    free_items.forEach(free_item => {
        // Skip if free item already exists in the opportunity
        if (existing_item_codes.includes(free_item.item_code)) {
            return;
        }
        // console.log("Adding free item:", free_item.item_code);
        // Add new row for free item
        const new_row = frm.add_child('items', {
            item_code: free_item.item_code,
            item_name: free_item.item_name,
            description: free_item.description,
            qty: free_item.qty,
            uom: free_item.uom,
            stock_uom: free_item.stock_uom,
            conversion_factor: free_item.conversion_factor,
            rate: free_item.rate,
            base_rate: free_item.rate,
            base_amount: free_item.rate * free_item.qty,
            amount: free_item.rate * free_item.qty,
            base_net_rate: free_item.rate,
            net_rate: free_item.rate,
            base_net_amount: free_item.rate * free_item.qty,
            net_amount: free_item.rate * free_item.qty,
            is_free_item: 1,
            pricing_rules: free_item.pricing_rules,
            against_opportunity_item: parent_item_code, // Link to parent item
            custom_is_free_item: 1 // Custom field to mark as free item
        });
        
        // Set readonly fields
        // new_row.$wrapper.find('input[data-fieldname="rate"]').prop('readonly', true);
        // new_row.$wrapper.find('input[data-fieldname="discount_percentage"]').prop('readonly', true);
    });

    // Refresh and recalculate
    frm.refresh_field('items');
    // frm.cscript.calculate_taxes_and_totals();
}

// Make free items read-only
frappe.ui.form.on("Opportunity Item", "refresh", function(frm) {
    (frm.doc.items || []).forEach(item => {
        if (item.is_free_item || item.custom_is_free_item) {
            const grid_row = frm.fields_dict.items.grid.grid_rows_by_docname[item.name];
            if (grid_row) {
                grid_row.toggle_enable("rate", false);
                grid_row.toggle_enable("discount_percentage", false);
                grid_row.toggle_enable("qty", false);
            }
        }
    });
});