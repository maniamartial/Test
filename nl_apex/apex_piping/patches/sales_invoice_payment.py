import frappe

def execute():
    # Get all Sales Invoices that are linked to a Sales Order, fetching delivery_note and sales_order from Sales Invoice Item
    sales_invoices = frappe.db.sql("""
        SELECT si.name as sales_invoice_name, sii.sales_order, sii.delivery_note
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        WHERE si.docstatus = 1 AND sii.sales_order IS NOT NULL
    """, as_dict=True)

    for invoice in sales_invoices:
        # Fetch the linked Sales Order and its payments
        sales_order = frappe.get_doc("Sales Order", invoice.sales_order)
        
        if sales_order.custom_order_payment:
            sales_invoice = frappe.get_doc("Sales Invoice", invoice.sales_invoice_name)
            
            # Update the payments table with missing fields
            for payment in sales_order.custom_order_payment:
                payment_entry = next((p for p in sales_invoice.payments if p.mode_of_payment == payment.mode_of_payment), None)
                
                if payment_entry:
                    # Use set_value to update each field to bypass the save validation
                    frappe.db.set_value(
                        "Sales Invoice Payment",
                        payment_entry.name,
                        {
                            "reference_no": payment.reference_no or payment_entry.reference_no,
                            "custom_reference_date":payment.custom_reference_date,
                            "account": payment.account or payment_entry.account,
                            "type": payment.type or payment_entry.type,
                            "clearance_date": payment.clearance_date or payment_entry.clearance_date,
                            "default": payment.default or payment_entry.default,
                        }
                    )

    frappe.db.commit()
    

