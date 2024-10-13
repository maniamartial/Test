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
