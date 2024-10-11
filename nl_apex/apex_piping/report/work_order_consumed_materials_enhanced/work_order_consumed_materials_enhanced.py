# Copyright (c) 2024, Navari Ltd and contributors
# For license information, please see license.txt

# import frappe


# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from collections import defaultdict

import frappe
from frappe import _


def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)

	return columns, data


# def get_data(report_filters):
# 	fields = get_fields()
# 	filters = get_filter_condition(report_filters)

# 	wo_items = {}

# 	work_orders = frappe.get_all("Work Order", filters=filters, fields=fields)
# 	get_returned_materials(work_orders)

# 	for d in work_orders:
# 		d.extra_consumed_qty = 0.0
# 		if d.consumed_qty and d.consumed_qty > d.required_qty:
# 			d.extra_consumed_qty = d.consumed_qty - d.required_qty

# 		if d.extra_consumed_qty or not report_filters.show_extra_consumed_materials:
# 			wo_items.setdefault((d.name, d.production_item), []).append(d)

# 	data = []
# 	for _key, wo_data in wo_items.items():
# 		for index, row in enumerate(wo_data):
# 			if index != 0:
# 				# If one work order has multiple raw materials then show parent data in the first row only
# 				for field in ["name", "status", "production_item", "qty", "produced_qty"]:
# 					row[field] = ""

# 			data.append(row)

# 	return data

def get_data(report_filters):
    fields = get_fields()
    filters = get_filter_condition(report_filters)

    wo_items = {}

    work_orders = frappe.get_all("Work Order", filters=filters, fields=fields)
    
    # Get returned and scrap materials
    get_returned_materials(work_orders)
    scrap_items_map = get_scrap_item_and_qty(work_orders)

    for d in work_orders:
        d.extra_consumed_qty = 0.0
        if d.consumed_qty and d.consumed_qty > d.required_qty:
            d.extra_consumed_qty = d.consumed_qty - d.required_qty

        # Set scrap item and qty if available for the work order
        scrap_data = scrap_items_map.get(d.name, {"scrap_item": "", "scrap_qty": 0.0})
        d.scrap_item = scrap_data.get("scrap_item")
        d.scrap_qty = scrap_data.get("scrap_qty")

        if d.extra_consumed_qty or not report_filters.show_extra_consumed_materials:
            wo_items.setdefault((d.name, d.production_item), []).append(d)

    data = []
    for _key, wo_data in wo_items.items():
        for index, row in enumerate(wo_data):
            if index != 0:
                # If one work order has multiple raw materials then show parent data in the first row only
                for field in ["name", "status", "production_item", "qty", "produced_qty", "scrap_item", "scrap_qty"]:
                    row[field] = ""

            data.append(row)

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
		"`tabWork Order`.`status`",
		"`tabWork Order`.`name`",
		"`tabWork Order`.`production_item`",
		"`tabWork Order`.`qty`",
		"`tabWork Order`.`produced_qty`",
	]


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
		"fieldname": "returned_qty",
		"fieldtype": "Float",
		"width": 100,
  
  },
		{
			"label": _("Returned Qty"),
			"fieldname": "returned_qty",
			"fieldtype": "Float",
			"width": 100,
		},
  

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
# def get_scrap_item_and_qty(work_orders):
#     # Using the query builder to construct the query
#     scrap_items = frappe.get_all(
#         'Stock Entry Detail',
#         fields=['item_code', 'qty'],
#         filters={
#             'parenttype': 'Stock Entry',
#             'docstatus': 1,
#             'is_scrap_item': 1,  # Corrected spelling here
#             'parent': [
#                 'in',
#                 [se.name for se in frappe.get_all(
#                     'Stock Entry',
#                     filters={
#                         'is_return': 0,
#                         'purpose': 'Manufacture',
#                         'work_order': ['in', work_orders]
#                     },
#                     fields=['name']
#                 )]
#             ]
#         },
#         order_by='docstatus asc, creation desc'
#     )

#     return scrap_items

