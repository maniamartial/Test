import frappe
import frappe.defaults
from frappe.model.document import Document
from frappe.utils import flt
from erpnext.selling.doctype.customer.customer import (
	get_credit_limit,
	get_customer_outstanding,
)
from frappe.utils import flt
from frappe.core.doctype.communication.email import make
from collections import defaultdict


def validate(doc: Document, method: str | None = None) -> None:
	if doc.custom_sales_type == "Credit":
		# Only perform credit check for credit customers
		company = frappe.defaults.get_user_default("Company")
		status=check_credit_limit(doc, doc.customer, company)
		
		doc.custom_credit_check=status
		# Update Outstanding Limit and Credit Limit custom fields of Sales Order
		doc.custom_outstanding_balance = get_customer_outstanding(doc.customer, company)
		doc.custom_credit_limit = get_credit_limit(doc.customer, company)


def check_credit_limit(
	doc,
	customer: str,
	company: str,
	ignore_outstanding_sales_order: bool = False,
	extra_amount: int = 0,
) -> bool:
	"""Perform Credit Limit check on customer.
	Checks credit limit and outstanding balance to determine credit status.
	"""
	credit_limit = get_credit_limit(customer, company)
	customer_outstanding = get_customer_outstanding(
		customer, company, ignore_outstanding_sales_order
	)
	customer_outstanding_and_base=get_customer_outstanding(
		customer, company, ignore_outstanding_sales_order
	)
	customer_total_so=get_customers_total_base_for_sales_order(customer) + doc.base_total
	status="FAIL"

	if credit_limit > 0.0:
		if customer_outstanding <= 0.0 and customer_total_so < credit_limit:
			status="PASS"
	else:
		if customer_outstanding <= 0.0:
			status="PASS"
		
	return status

#calculate customer sales order base total
def get_customers_total_base_for_sales_order(customer):
	sales_orders = frappe.get_all("Sales Order", filters={"customer": customer, "docstatus":1}, fields=["base_total"])
	total_base = sum([so["base_total"] for so in sales_orders])
	return total_base

def calculate_gross_profit(doc):

	total_gross_profit_percentage = 0
	number_of_items = len(doc.items)
	total_gross_profit=0
	for item in doc.items:

		item.custom_valuation_amount = item.valuation_rate * item.qty if item.valuation_rate and item.qty else 0

		gross_profit = (item.rate - item.valuation_rate) * item.qty if item.rate and item.valuation_rate and item.qty else 0
		if gross_profit == 0 or item.custom_valuation_amount == 0:
			item.custom_gross_profit_percentage = 0
		else:
			item.custom_gross_profit_percentage = gross_profit / item.custom_valuation_amount * 100

		total_gross_profit_percentage = total_gross_profit_percentage + item.custom_gross_profit_percentage

		total_gross_profit = total_gross_profit + item.gross_profit


	doc.custom_gross_profit_ = total_gross_profit_percentage / number_of_items
	doc.custom_gross_proft = total_gross_profit
 
def before_save(doc, method=None):
	calculate_gross_profit(doc)
 
 
@frappe.whitelist(allow_guest=True)
def invoices_payment_due_validation():
	customer=frappe.form_dict.get("customer")
	if customer:
		undue_invoices = frappe.db.count("Sales Invoice", {"status": "Overdue", "customer": customer})
		
		if undue_invoices > 0:
			frappe.response["status"] = "FAIL"
		else:
			frappe.response["status"] = "PASS"
			

'''Notify when stock is added in the system'''
def check_and_notify_stock_status():	
	orders_to_notify = defaultdict(list)

	sales_orders = frappe.get_all("Sales Order Item",
		filters={
			"custom_delivery_status": "Sourcing",
			"custom_email_sent": 0
		},
		fields=["name", "parent", "item_code", "qty", "warehouse", "idx"]
	)

	for item in sales_orders:
		available_qty = get_available_qty(item.item_code, item.warehouse)
		if available_qty >= item.qty:
			orders_to_notify[item.parent].append(item)
			frappe.db.set_value("Sales Order Item", item.name, "custom_delivery_status", "Awaiting Delivery")
			frappe.db.set_value("Sales Order Item", item.name, "custom_email_sent", 1)

	# Send consolidated notifications per Sales Order
	for order_id, items in orders_to_notify.items():
		send_stock_available_notification(order_id, items)

	frappe.db.commit()

def send_stock_available_notification(order_id, items):
	sales_order = frappe.get_doc("Sales Order", order_id)
	user_email = get_customer_email(sales_order)
	owner_email = frappe.get_doc("User", sales_order.owner).email

	subject = f"Stock Available for Your Sales Order {order_id}"
	item_rows = "".join(
		f"<tr><td>{item.item_code}</td><td>{item.qty}</td><td>{get_available_qty(item.item_code, item.warehouse)}</td></tr>"
		for item in items
	)
	message = f"""
		<p>Dear {sales_order.customer_name},</p>
		<p>The following items you requested are now in stock:</p>
		<table border="1">
			<tr><th>Item Code</th><th>Requested Quantity</th><th>Available Quantity</th></tr>
			{item_rows}
		</table>
		<p>You may proceed with pickup or purchase. Status has been updated to "Awaiting Delivery".</p>
	"""
	frappe.sendmail(recipients=user_email,cc=owner_email, expose_recipients = 'header', subject=subject, message=message)

def get_available_qty(item_code, warehouse):
	stock_qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty")
	return flt(stock_qty) if stock_qty else 0


def get_customer_email(doc):
    if doc.customer == "CASH CUSTOMER CONTROL":
        if doc.custom_cash_customer:
            email = get_contact_email(doc.custom_cash_customer, doc)
            if not email:
                return None
            return email
        else:
            return None
    else:
        return get_contact_email(doc.customer, doc)

def get_contact_email(contact_name, doc):
    contact_id = ''

    if doc.custom_cash_customer:
        try:
            contact_id = frappe.get_doc("Contact", contact_name)
        except frappe.DoesNotExistError:
            return None
    else:
        contact_names = frappe.get_all("Contact", filters={"full_name": contact_name}, fields=["name"])
        if contact_names:
            try:
                contact_id = frappe.get_doc("Contact", contact_names[0].name)
            except frappe.DoesNotExistError:
                return None
        else:
            return None

    # Get the email address from the contact
    email_address = contact_id.get("email_id")
    if email_address:
        return email_address
    else:
        return None