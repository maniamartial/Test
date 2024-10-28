
import frappe

def before_save(doc, method=None):
	get_update_approver(doc)

def get_update_approver(doc, method=None):
	reference_doctype = "Sales Order"
	comment_content = "Approved"

	# Get the first comment that matches the specified filters
	comment = frappe.db.get_all("Comment", filters={
		"comment_type": "Workflow",
		"reference_doctype": reference_doctype,
		"content": comment_content
	}, fields=["comment_email", "reference_name"], limit=1)

	# Initialize a variable for the email
	email = None
	reference_name = None
	if comment:
		email = comment[0].get("comment_email")  
		reference_name = comment[0].get("reference_name")

	full_name = None

	if email:
		full_name = frappe.db.get_value("User", {"email": email}, "full_name")
	sales_order=frappe.get_doc("Sales Order", reference_name)
	if sales_order.docstatus == 1:
		frappe.set_value("Sales Order", reference_name, "custom_approver", full_name)
		