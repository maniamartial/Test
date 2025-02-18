
import frappe

def set_cost_per_unit(doc, method:None):
    for  operation in doc.operations:
        custom_cost_per_unit = frappe.db.get_value("Item", doc.item, "custom_cost_per_unit")
        if custom_cost_per_unit:
            operation.custom_cost_per_kg = custom_cost_per_unit