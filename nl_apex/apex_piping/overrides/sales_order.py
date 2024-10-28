import frappe
import frappe.defaults
from frappe.model.document import Document
from frappe.utils import flt
from erpnext.selling.doctype.customer.customer import (
	get_credit_limit,
	get_customer_outstanding,
)


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
			
