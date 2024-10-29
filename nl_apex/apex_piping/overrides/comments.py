
import frappe

def before_save(doc, method=None):
	get_update_approver(doc)

def get_update_approver(doc, method=None):
    reference_doctype = "Sales Order"
    comment_content = "Approved"

    # Initialize a variable for the email and full name
    email = doc.comment_email
    full_name = None

    if email:
        full_name = frappe.db.get_value("User", {"email": email}, "full_name")

    # Check if the document is a Sales Order and if it is submitted
    if doc.reference_doctype == reference_doctype and doc.content==comment_content:
        sales_order = frappe.get_doc(reference_doctype, doc.reference_name)
        
        if sales_order.docstatus == 1:
            frappe.set_value(reference_doctype, doc.reference_name, "custom_approver", full_name)

		