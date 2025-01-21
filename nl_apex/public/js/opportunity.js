
 
frappe.ui.form.on("Opportunity Item", "item_code", function(frm, cdt, cdn) {
    var row = locals[cdt][cdn];

    frappe.call({
        method: "frappe.client.get_value",
        args: {
            doctype: "Item Price",
            fieldname: "price_list_rate",
            filters: {
                "item_code": row.item_code,
                "price_list": "Standard Selling"
            }
        },
        callback: function(data) {

            if (data.message && data.message.price_list_rate) {
                var price_rate = data.message.price_list_rate;

                frappe.model.set_value(cdt, cdn, "base_rate", price_rate);
                frappe.model.set_value(cdt, cdn, "rate", price_rate);

                frappe.refresh_field("items");
            } else {
                console.log('No price found for the item.');
            }
        }
    });
});
