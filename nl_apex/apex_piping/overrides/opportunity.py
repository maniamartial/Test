import frappe
import copy
import json

from frappe.utils import flt
from frappe.utils import today
from erpnext.stock.get_item_details import get_item_price
from erpnext.accounts.doctype.pricing_rule.utils import (
		get_applied_pricing_rules,
		get_pricing_rule_items,
		get_pricing_rules,
		get_product_discount_rule,
	)

@frappe.whitelist(allow_guest=True)
def get_price_list_rate():
	item_code = frappe.form_dict.get('item_code')
	price_list = frappe.form_dict.get('custom_price_list')
	customer = frappe.form_dict.get('party_name')

	args = {
		"price_list": price_list,
		"customer": customer,
		"transaction_date": today(),
	}

	item_prices = get_item_price(args, item_code)

	if item_prices:
		frappe.response.message = item_prices[0]["price_list_rate"]
		return item_prices[0]["price_list_rate"]
	else:
		frappe.response.message = 0
		return 0


def is_price_rule_enabled():
	selling_settings = frappe.get_single("Selling Settings")
	if selling_settings.custom_enable_price_rule:
		return True
	return False


import frappe
from frappe.utils import flt, nowdate

@frappe.whitelist()
def get_pricing_rule_for_item(
	item_code,
	customer=None,
	transaction_date=None,
	selling_price_list=None,
	price_list_currency=None,
	plc_conversion_rate=1.0,
	conversion_rate=1.0,
	doctype=None,
	name=None,
	company=None,
	qty=1,
	uom=None,
	stock_uom=None,
	conversion_factor=1.0,
	is_pos=0,
	is_subcontracted=0,
	ignore_pricing_rule=0,
	transaction_type="selling",
	parent=None,
	parenttype=None
):
    
	# if ignore_pricing_rule:
	# 	return {"free_item_data": []}

	# Set default values
	transaction_date = transaction_date or nowdate()
	# Build filters for pricing rules
	filters = [
		["Pricing Rule", "disable", "=", 0],
		["Pricing Rule", "apply_on", "=", "Item Code"],
		["Pricing Rule", "item_code", "=", item_code],
		["Pricing Rule", "selling", "=", 1],
		# ["Pricing Rule", "apply_on_other", "is", "not set"],
		# ["Pricing Rule", "price_or_product_discount", "=", "Product"],
		# ["Pricing Rule", "free_item", "is", "set"],
		# ["Pricing Rule", "valid_from", "<=", transaction_date],
		# ["Pricing Rule", "valid_upto", ">=", transaction_date]
	]

	# Add company filter if specified
	if company:
		filters.append(["Pricing Rule", "company", "in", [company, None]])

	# Add customer filter if specified
	if customer:
		or_filters = [
			["Pricing Rule", "customer", "is", "not set"],
			["Pricing Rule", "customer", "=", customer]
		]
	else:
		or_filters = [["Pricing Rule", "customer", "is", "not set"]]

	# Add price list filter if specified
	# if selling_price_list:
	# 	or_filters.append(["Pricing Rule", "price_list", "=", selling_price_list])

	# Get applicable pricing rules
	pricing_rules = frappe.get_all(
		"Pricing Rule",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "free_item", "free_qty", "min_qty", "max_qty", "priority","free_item_rate"]
	)
	# frappe.throw(str(pricing_rules))
	# Sort by priority (higher priority first)
	pricing_rules.sort(key=lambda x: flt(x.priority or 0), reverse=True)

	free_item_data = []
	
	# Check quantity conditions
	qty = flt(qty)
	applicable_rules = []

	for rule in pricing_rules:
		min_qty = flt(rule.get("min_qty"))
		max_qty = flt(rule.get("max_qty")) if rule.get("max_qty") else float("inf")
		
		if min_qty <= qty <= max_qty:
			applicable_rules.append(rule)

	# Process applicable rules
	for rule in applicable_rules:
		if not rule.get("free_item"):
			continue

		free_item_code = rule.get("free_item")
		free_qty = flt(rule.get("free_qty") or 0)
		
		if free_qty <= 0:
			continue

		# Get item details
		item_details = frappe.db.get_value("Item", free_item_code, 
			["item_name", "description", "stock_uom"], as_dict=1)
		
		if not item_details:
			continue
		free_item_data.append({
			"item_code": free_item_code,
			"item_name": item_details.item_name,
			"description": item_details.description,
			"uom": item_details.stock_uom,
			"stock_uom": item_details.stock_uom,
			"qty": free_qty,
			"rate": rule.free_item_rate,
			"price_list_rate": rule.free_item_rate,
			"conversion_factor": 1,
			"pricing_rules": rule.name
		})

	return {
		"free_item_data": free_item_data
	}