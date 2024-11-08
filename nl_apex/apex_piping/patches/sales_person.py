
import frappe
from frappe.query_builder import DocType

def execute():
    SalesOrder = DocType("Sales Order")
    SalesTeam = DocType("Sales Team")

    sales_orders_query = (
        frappe.qb.from_(SalesOrder)
        .left_join(SalesTeam)
        .on(SalesTeam.parent == SalesOrder.name)
        .select(SalesOrder.name, SalesOrder.owner)
        .where(
            (SalesOrder.docstatus == 1) &
            (SalesOrder.custom_sales_type == 'Cash') &
            (SalesTeam.name.isnull())  
        )
    )

    sales_orders = sales_orders_query.run(as_dict=True)

    for so in sales_orders:
        sales_order = frappe.get_doc("Sales Order", so["name"])
        if sales_order.sales_team:
            continue
        
        owner_full_name = frappe.db.get_value("User", so["owner"], "full_name")
        
        sales_order.append("sales_team", {
            "sales_person": owner_full_name,
            "allocated_percentage": 100,
            "allocated_amount": sales_order.net_total,
            "incentives": 0
        })
        
        sales_order.save()

        delivery_notes = frappe.db.sql("""
            SELECT dn.name 
            FROM `tabDelivery Note` dn
            JOIN `tabDelivery Note Item` dni ON dn.name = dni.parent
            WHERE dni.against_sales_order = %s
        """, so["name"], as_dict=True)

        for dn in delivery_notes:
            delivery_note = frappe.get_doc("Delivery Note", dn["name"])
            if not delivery_note.sales_team:
                delivery_note.append("sales_team", {
                    "sales_person": owner_full_name,
                    "allocated_percentage": 100,
                    "allocated_amount": delivery_note.net_total,
                    "incentives": 0
                })
                delivery_note.save()

            sales_invoices = frappe.db.sql("""
                SELECT si.name 
                FROM `tabSales Invoice` si
                JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
                WHERE sii.delivery_note = %s
            """, dn["name"], as_dict=True)

            for si in sales_invoices:
                sales_invoice = frappe.get_doc("Sales Invoice", si["name"])
                if not sales_invoice.sales_team:
                    sales_invoice.append("sales_team", {
                        "sales_person": owner_full_name,
                        "allocated_percentage": 100,
                        "allocated_amount": sales_invoice.net_total,
                        "incentives": 0
                    })
                    sales_invoice.save()

    frappe.db.commit()


'''Just made use of sql because I will delete this script later'''