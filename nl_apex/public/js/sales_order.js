
frappe.ui.form.on('Sales Invoice Payment', {
    amount: function(frm, cdt, cdn) {
        update_custom_amount(frm);
    },
    custom_order_payment_remove: function(frm, cdt, cdn) {
        update_custom_amount(frm);
    }
});

function update_custom_amount(frm) {
    let total_amount = 0;

    frm.doc.custom_order_payment.forEach(function(payment) {
        total_amount += payment.amount;
    });

    frm.set_value('custom_amount_paid', total_amount);
}

frappe.ui.form.on('Sales Order', {
    before_save: function(frm) {
        frm.doc.items.forEach((item) => {
            calculate_valuation_amount(item);
            calculate_gross_profit_percentage(item);
        });
       
        // Calculate total gross profit and average gross profit
        calculate_total_gross_profit(frm);
        calculate_average_gross_profit(frm);
        
        // Validate cost status across all items
        validate_cost_status(frm);
    },

    validate: function(frm) {
        const deliveryDate = frm.doc.delivery_date;
        const profitsArray = [];
        const valuationsArray = [];

        frm.doc.items.forEach((item) => {
            // Push gross profit and valuation rates for calculations
            profitsArray.push(item.gross_profit);
            valuationsArray.push(item.valuation_rate);

            // Update delivery date in line items if not selected
            if (deliveryDate) {
                item.delivery_date = deliveryDate;
            }

            // Set delivery status based on quantity
            item.custom_delivery_status = item.qty > item.actual_qty ? "Sourcing" : "Awaiting Delivery";

            // Fetch item margin from database and validate costs
            frappe.db.get_value(
                "Item",
                { item_code: item.item_code },
                ["custom_margin_"],
                (res) => {
                    const marginRate = parseFloat(res.custom_margin_);
                    const valuationRate = parseFloat(item.valuation_rate) * ((100.0 + marginRate) / 100);
                    const itemRate = frm.doc.currency === "KES"
                        ? parseFloat(item.rate)
                        : parseFloat(frm.doc.conversion_rate) * parseFloat(item.rate);

                    // Validate cost based on item rate and valuation rate
                    item.custom_cost_validation = itemRate <= valuationRate ? "FAIL" : "PASS";
                }
            );
        });

    },

    customer: function(frm) {
        frappe.call({
            method: "nl_apex.apex_piping.overrides.sales_order.invoices_payment_due_validation",
            args: {
                customer: frm.doc.customer,
            },
            callback: (response) => {
                frm.set_value("custom_payment_due_validation", response.status);
            },
        });
    }
});

frappe.ui.form.on('Sales Order Item', {
    amount: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        // Calculate valuation and gross profit when amount changes
        calculate_valuation_amount(row);
        calculate_gross_profit_percentage(row);
        frm.refresh_field('items');
    },

    qty: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        calculate_valuation_amount(row);
        calculate_gross_profit_percentage(row);
        frm.refresh_field('items');
    },

    gross_profit: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        calculate_gross_profit_percentage(row);
        frm.refresh_field('items');
    },

    form_render: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        row.custom_qty_remaining_to_deliver = row.qty - row.delivered_qty;
        frm.refresh_field("items");
    }
});

// Utility function to calculate total gross profit
function calculate_total_gross_profit(frm) {
    let total_gross_profit = 0;

    frm.doc.items.forEach(function(item) {
        total_gross_profit += item.gross_profit;
    });

    frm.set_value('custom_gross_proft', total_gross_profit);

    frm.refresh_field('custom_gross_proft');

}


// Utility function to calculate gross profit percentage for a row
function calculate_gross_profit_percentage(row) {
    let gross_profit = (row.rate - row.valuation_rate) * row.qty;
    row.custom_gross_profit_percentage = (gross_profit === 0 || row.custom_valuation_amount <= 0) ? 0 : (flt(gross_profit) / flt(row.custom_valuation_amount)) * 100;
}

function calculate_valuation_amount(row) {
    
    row.custom_valuation_amount = flt(row.valuation_rate) * flt(row.qty);
}

function calculate_average_gross_profit(frm) {
    let total_gross_profit_percentage = 0;
    let number_of_items = frm.doc.items.length;

    frm.doc.items.forEach(function(item) {
        total_gross_profit_percentage += item.custom_gross_profit_percentage;
    });
    console.log("Mee",total_gross_profit_percentage)
    if (number_of_items > 0) {
        average_percentage= total_gross_profit_percentage / number_of_items;
        frm.set_value('custom_gross_profit_', average_percentage);

        frm.refresh_field('custom_gross_profit_');
    } else {
        frm.doc.custom_gross_profit_ = 0;
    }
}

// Utility function to validate cost status for the Sales Order
function validate_cost_status(frm) {
    const isAnyFailedCostValidation = (element) => element.custom_cost_validation === "FAIL";
    const costValStatus = frm.doc.items.some(isAnyFailedCostValidation);
    frm.set_value("custom_cost_validation_status", costValStatus ? "FAIL" : "PASS");
}
