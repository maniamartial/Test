
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

// frappe.ui.form.on('Sales Order', {
//     refresh(frm) {
//         setTimeout(() => {
//             // Hide 'Delivery Note' button in the 'Create' dropdown
//             frm.remove_custom_button('Delivery Note', 'Create');
//         }, 10);
//     }
// });
