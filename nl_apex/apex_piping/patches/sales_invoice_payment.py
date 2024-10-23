
# import frappe

# def execute():
#     # Get all Sales Invoices that are linked to a Sales Order
#     sales_invoices = frappe.db.sql("""
#         SELECT si.name, si.delivery_note, so.name as sales_order_name
#         FROM `tabSales Invoice` si
#         JOIN `tabSales Order Item` soi ON soi.sales_order = si.sales_order
#         JOIN `tabSales Order` so ON so.name = soi.sales_order
#         WHERE si.docstatus = 1
#     """, as_dict=True)

#     for invoice in sales_invoices:
#         # Fetch the linked Sales Order and its payments
#         sales_order = frappe.get_doc("Sales Order", invoice.sales_order_name)
        
#         if sales_order.custom_order_payment:
#             # Load the Sales Invoice document
#             sales_invoice = frappe.get_doc("Sales Invoice", invoice.name)
            
#             # Update the payments table with missing fields
#             for payment in sales_order.custom_order_payment:
#                 # Find corresponding payment entry in the invoice to update
#                 payment_entry = next((p for p in sales_invoice.payments if p.mode_of_payment == payment.mode_of_payment), None)
                
#                 if payment_entry:
#                     # Update missing fields if present in Sales Order payment
#                     payment_entry.reference_no = payment.reference_no or payment_entry.reference_no
#                     payment_entry.account = payment.account or payment_entry.account
#                     payment_entry.type = payment.type or payment_entry.type
#                     payment_entry.clearance_date = payment.clearance_date or payment_entry.clearance_date
#                     payment_entry.default = payment.default or payment_entry.default

#             # Save the updated Sales Invoice
#             sales_invoice.save(ignore_permissions=True)

#     frappe.db.commit()
