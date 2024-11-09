# Copyright (c) 2024, Navari Ltd and contributors
# For license information, please see license.txt

from collections import defaultdict

import frappe
from frappe import _


def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_data(report_filters):
	fields = get_fields()
	filters = get_filter_condition(report_filters)

	wo_items = {}

	work_orders = frappe.get_all("Work Order", filters=filters, fields=fields)
	
	#Map machine to work orders
	machine_map = get_machine_map(work_orders)
	employee_shift_map = get_employee_shift_map(work_orders)
	for d in work_orders:
		d.machine = machine_map.get(d.name, "")
		employee_shift_data = employee_shift_map.get(d.name, {"employees":[], "custom_shift": ""})
		# d.employee = employee_shift_data["employees"]
		d.employee = ", ".join(employee_shift_data["employees"]) if employee_shift_data["employees"] else ""
		d.custom_shift = employee_shift_data["custom_shift"]
  
	# Get returned and scrap materials
	get_returned_materials(work_orders)
	scrap_items_map = get_scrap_item_and_qty(work_orders)
	extra_items_map = get_extra_item_and_qty(work_orders)  # Get extra items here


	for d in work_orders:
		d.extra_consumed_qty = 0.0
		if d.consumed_qty and d.consumed_qty > d.required_qty:
			d.extra_consumed_qty = d.consumed_qty - d.required_qty

		# Set scrap item and qty if available for the work order
		scrap_data = scrap_items_map.get(d.name, {"scrap_item": "", "scrap_qty": 0.0})
		d.scrap_item = scrap_data.get("scrap_item")
		d.scrap_qty = scrap_data.get("scrap_qty")

		# Set extra item and qty if available for the work order
		extra_data = extra_items_map.get(d.name, {"extra_item": "", "extra_qty": 0.0})
		d.extra_item = extra_data.get("extra_item")
		d.extra_qty = extra_data.get("extra_qty")
		d.extra_item_name = extra_data.get("extra_item_name")

		# Calculate saving_qty: the difference between transferred and consumed quantity
		d.saving_qty = d.transferred_qty - d.consumed_qty if d.transferred_qty and d.consumed_qty else 0.0

		# Calculate amount: valuation rate * consumed qty
		d.amount=(d.valuation_rate * d.consumed_qty) if d.valuation_rate and d.consumed_qty else 0.0
  
  
		# Calculate scrap percentage: (scrap_qty / produced_qty) * 100
		if d.produced_qty:
			d.scrap_percentage = (d.scrap_qty / d.produced_qty) * 100
		else:
			d.scrap_percentage = 0.0
			
		if d.extra_consumed_qty or not report_filters.show_extra_consumed_materials:
			wo_items.setdefault((d.name, d.production_item), []).append(d)

	data = []
	for _key, wo_data in wo_items.items():
		for index, row in enumerate(wo_data):
			if index != 0:
				# If one work order has multiple raw materials then show parent data in the first row only
				for field in ["name", "status", "production_item", "qty", "produced_qty", "scrap_item", "scrap_qty","extra_item","extra_qty","extra_item_name","machine","employee","shift"]:
					row[field] = ""

			data.append(row)
	# frappe.throw(str(data))
	return data

def get_returned_materials(work_orders):
	raw_materials_qty = defaultdict(float)

	raw_materials = frappe.get_all(
		"Stock Entry",
		fields=["`tabStock Entry Detail`.`item_code`", "`tabStock Entry Detail`.`qty`"],
		filters=[
			["Stock Entry", "is_return", "=", 1],
			["Stock Entry Detail", "docstatus", "=", 1],
			["Stock Entry", "work_order", "in", [d.name for d in work_orders]],
		],
	)

	for d in raw_materials:
		raw_materials_qty[d.item_code] += d.qty

	for row in work_orders:
		row.returned_qty = 0.0
		if raw_materials_qty.get(row.raw_material_item_code):
			row.returned_qty = raw_materials_qty.get(row.raw_material_item_code)

def get_fields():
	return [
		"`tabWork Order Item`.`parent`",
		"`tabWork Order Item`.`item_code` as raw_material_item_code",
		"`tabWork Order Item`.`item_name` as raw_material_name",
		"`tabWork Order Item`.`required_qty`",
		"`tabWork Order Item`.`transferred_qty`",
		"`tabWork Order Item`.`consumed_qty`",
		"`tabWork Order Item`.`rate` as valuation_rate" , #Added this rate from work order items
		"`tabWork Order`.`status`",
		"`tabWork Order`.`name`",
		"`tabWork Order`.`production_item`",
		"`tabWork Order`.`qty`",
		"`tabWork Order`.`produced_qty`",
		"`tabWork Order Operation`.`parent`",
  		"`tabWork Order Operation`.`workstation` as machine",

	]

def get_machine_map(work_orders):
	"""
	Fetches machine (workstation) details for each work order.
	"""
	machine_map = {}
	work_order_names = [d.name for d in work_orders]

	workstation_data = frappe.db.sql(
		"""
		SELECT 
			parent as work_order,
			workstation
		FROM `tabWork Order Operation`
		WHERE parent IN %(work_orders)s
		""",
		{"work_orders": work_order_names},
		as_dict=True,
	)

	for entry in workstation_data:
		machine_map[entry.work_order] = entry.workstation

	return machine_map


def get_filter_condition(report_filters):
	filters = {
		"docstatus": 1,
		"status": ("in", ["In Process", "Completed", "Stopped"]),
		"creation": ("between", [report_filters.from_date, report_filters.to_date]),
	}

	for field in ["name", "production_item", "company", "status"]:
		value = report_filters.get(field)
		if value:
			key = f"{field}"
			filters.update({key: value})

	return filters


def get_columns():
	return [
		{
			"label": _("Id"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Work Order",
			"width": 80,
		},
   
  {
	"label": _("Scrap Item"),
	"fieldname": "scrap_item",
	"fieldtype": "Link",
	"options": "Item",
	"width": 150,
},
{
	"label": _("Scrap Qty"),
	"fieldname": "scrap_qty",
	"fieldtype": "Float",
	"width": 100,
},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 80},
		{
			"label": _("Production Item"),
			"fieldname": "production_item",
			"fieldtype": "Link",
			"options": "Item",
			"width": 130,
		},
		{"label": _("Qty to Produce"), "fieldname": "qty", "fieldtype": "Float", "width": 120},
		{"label": _("Produced Qty"), "fieldname": "produced_qty", "fieldtype": "Float", "width": 110},
		{
			"label": _("Raw Material Item"),
			"fieldname": "raw_material_item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 150,
		},
		{"label": _("Item Name"), "fieldname": "raw_material_name", "width": 130},
		{"label": _("Required Qty"), "fieldname": "required_qty", "fieldtype": "Float", "width": 100},
		{
			"label": _("Transferred Qty"),
			"fieldname": "transferred_qty",
			"fieldtype": "Float",
			"width": 100,
		},
		{"label": _("Consumed Qty"), "fieldname": "consumed_qty", "fieldtype": "Float", "width": 100},
		{
			"label": _("Extra Consumed Qty"),
			"fieldname": "extra_consumed_qty",
			"fieldtype": "Float",
			"width": 100,
		},
  {
	  "label": _("Saving Qty"),
		"fieldname": "saving_qty",
		"fieldtype": "Float",
		"width": 100,
  
  },
		{
			"label": _("Returned Qty"),
			"fieldname": "returned_qty",
			"fieldtype": "Float",
			"width": 100,
		},
  {
			"label": _("Extra Item"),
			"fieldname": "extra_item",
			"fieldtype": "Link",
			"options": "Item",
			"width": 150,
		},
  {
	  "label": _("Extra Item Name"),
		"fieldname": "extra_item_name",
		"fieldtype": "Data",
		"width": 100,
  },
		{
			"label": _("Extra Qty"),
			"fieldname": "extra_qty",
			"fieldtype": "Float",
			"width": 100,
		},
  
		{
			"label": _("Valuation Rate"),
			"fieldname": "valuation_rate",
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"label": _("Amount"),# Amount = Valuation Rate * Consumed Qty
			"fieldname": "amount",
			"fieldtype": "Currency",
			"width": 100,
		},
  {
	  "label": _("Scrap(%)"),
		"fieldname": "scrap_percentage",
		"fieldtype": "Percentage",
		"width": 100,
  
  },
  {
	  "label": _("Machine"),
		"fieldname": "machine",
		"fieldtype": "Link",
		"options": "Workstation",
		"width": 100,
  },
  {
  "label": _("Employee"),
  "fieldname":"employee",
  "fieldtype":"Link",
  "options":"Employee",
  "width":100
  },
  {
	  "label":_("Shift"),
		"fieldname":"custom_shift",
		"fieldtype":"Link",
		"options":"Shift Type"
  }
  
	]
 
def get_scrap_item_and_qty(work_orders):
	# Fetch the scrap items related to the work orders
	scrap_items = frappe.db.sql(
		"""
		SELECT 
			`tabStock Entry`.work_order,
			`tabStock Entry Detail`.`item_code`, 
			`tabStock Entry Detail`.`qty`
		FROM 
			`tabStock Entry`
		LEFT JOIN 
			`tabStock Entry Detail` 
		ON 
			`tabStock Entry Detail`.parent = `tabStock Entry`.name
		WHERE 
			`tabStock Entry`.`is_return` = 0
			AND `tabStock Entry Detail`.`docstatus` = 1
			AND `tabStock Entry`.`purpose` = 'Manufacture'
			AND `tabStock Entry Detail`.`is_scrap_item` = 1
			AND `tabStock Entry`.`work_order` IN %(work_orders)s
		""", 
		{"work_orders": [d.name for d in work_orders]}, as_dict=True
	)
	
	scrap_item_qty_map = {}
	for d in scrap_items:
		scrap_item_qty_map[d.work_order] = {
			"scrap_item": d.item_code,
			"scrap_qty": d.qty
		}
	
	return scrap_item_qty_map


def get_extra_item_and_qty(work_orders):
	"""
	Fetch extra items that are not part of BOM or scrap/finished items
	for the given work orders.
	"""
	# Get BOM items for the work orders
	bom_items = frappe.db.sql(
		"""
		SELECT 
			`tabBOM Item`.item_code,
			`tabWork Order`.name AS work_order
		FROM 
			`tabWork Order`
		LEFT JOIN 
			`tabBOM Item` ON `tabBOM Item`.parent = `tabWork Order`.bom_no
		WHERE 
			`tabWork Order`.name IN %(work_orders)s
		""", 
		{"work_orders": [d.name for d in work_orders]}, 
		as_dict=True
	)
	
	# Create a map of BOM items for quick lookup
	bom_item_map = defaultdict(set)
	for d in bom_items:
		bom_item_map[d.work_order].add(d.item_code)

	# Get Stock Entry items and compare with BOM items
	stock_entry_items = frappe.db.sql(
		"""
		SELECT 
			`tabStock Entry`.work_order,
			`tabStock Entry Detail`.`item_code`, 
			`tabStock Entry Detail`.`item_name`, 
			`tabStock Entry Detail`.`qty`
		FROM 
			`tabStock Entry`
		LEFT JOIN 
			`tabStock Entry Detail` 
		ON 
			`tabStock Entry Detail`.parent = `tabStock Entry`.name
		WHERE 
			`tabStock Entry`.`is_return` = 0
			AND `tabStock Entry Detail`.`docstatus` = 1
			AND `tabStock Entry Detail`.`is_finished_item` = 0
   AND `tabStock Entry Detail`.`is_scrap_item` = 0
			AND `tabStock Entry`.`purpose` = 'Manufacture'
			AND `tabStock Entry`.`work_order` IN %(work_orders)s
		""", 
		{"work_orders": [d.name for d in work_orders]}, 
		as_dict=True
	)
	# Identify extra items by excluding those present in BOM
	extra_item_qty_map = {}
	for d in stock_entry_items:
		if d.item_code not in bom_item_map[d.work_order]:
			extra_item_qty_map[d.work_order] = {
				"extra_item": d.item_code,
				"extra_qty": d.qty,
				"extra_item_name": d.item_name
			}
	# frappe.throw(str(extra_item_qty_map))
	return extra_item_qty_map

# def get_employee_shift_map(work_orders):
# 	"""
# 	Fetches employee and shift details for each work order based on related Job Cards.
# 	"""
# 	employee_shift_map = {}
# 	work_order_names = [d.name for d in work_orders]
# 	job_card_data = frappe.db.sql(
# 		"""
# 		SELECT 
# 			work_order,
# 			employee,
# 			custom_shift
# 		FROM `tabJob Card`
# 		WHERE work_order IN %(work_orders)s
# 		""",
# 		{"work_orders": work_order_names},
# 		as_dict=True,
# 	)
# 	frappe.throw("Here")
# 	for entry in job_card_data:
# 		employee_shift_map[entry.work_order] = {
# 			"employee": entry.employee,
# 			"custom_shift": entry.custom_shift
# 		}

# 	return employee_shift_map

def get_employee_shift_map(work_orders):
	"""
	Fetches employee and shift details for each work order based on related Job Cards.
	"""
	employee_shift_map = {}
	work_order_names = [d.name for d in work_orders]

	# Fetch employee and shift data from the child table
	job_card_data = frappe.db.sql(
		"""
		SELECT 
			jc.work_order,
			jce.employee,
			jc.custom_shift
		FROM `tabJob Card` jc
		JOIN `tabJob Card Time Log` jce ON jce.parent = jc.name
		WHERE jc.work_order IN %(work_orders)s
		""",
		{"work_orders": work_order_names},
		as_dict=True,
	)

	for entry in job_card_data:
		if entry.work_order not in employee_shift_map:
			employee_shift_map[entry.work_order] = {
				"employees": [],
				"custom_shift": entry.custom_shift
			}
		employee_shift_map[entry.work_order]["employees"].append(entry.employee)
	return employee_shift_map

