import frappe
from frappe import _
from frappe.contacts.doctype.address.address import get_company_address
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cint, flt
from erpnext.controllers.accounts_controller import merge_taxes
from erpnext.stock.doctype.serial_no.serial_no import get_delivery_note_serial_no
from frappe.model.document import Document
from frappe.query_builder import DocType


@frappe.whitelist()
def make_sales_invoice(doc, method=None):
    # Fetch the delivery note
    doc = frappe.get_doc("Delivery Note", doc.name)
    if not doc.custom_delivery_note_no:
        order_no_generated(doc.name)
    # Check if a Sales Invoice already exists for this Delivery Note
    existing_invoices = frappe.get_all(
        "Sales Invoice",
        filters={"docstatus": ["!=", 2], "delivery_note": doc.name},
        fields=["name"]
    )
    
    if existing_invoices:
        frappe.msgprint(_("Sales Invoice already exists for this Delivery Note: {0}").format(existing_invoices[0].name))
        return frappe.get_doc("Sales Invoice", existing_invoices[0].name)
    
    # Proceed with the creation if no existing invoice
    to_make_invoice_qty_map = {}
    returned_qty_map = get_returned_qty_map(doc.name)
    invoiced_qty_map = get_invoiced_qty_map(doc.name)

    def set_missing_values(source, target):
        target.run_method("set_missing_values")
        target.run_method("set_po_nos")

        if len(target.get("items")) == 0:
            frappe.throw(_("All these items have already been Invoiced/Returned"))

        target.run_method("calculate_taxes_and_totals")

        # Set company address
        if source.company_address:
            target.update({"company_address": source.company_address})
        else:
            target.update(get_company_address(target.company))

        if target.company_address:
            target.update(frappe.get_fetch_values("Sales Invoice", "company_address", target.company_address))

    def update_item(source_doc, target_doc, source_parent):
        target_doc.qty = to_make_invoice_qty_map[source_doc.name]

        if source_doc.serial_no and source_parent.per_billed > 0 and not source_parent.is_return:
            target_doc.serial_no = get_delivery_note_serial_no(
                source_doc.item_code, target_doc.qty, source_parent.name
            )

    def get_pending_qty(item_row):
        pending_qty = item_row.qty - invoiced_qty_map.get(item_row.name, 0)

        returned_qty = 0
        if returned_qty_map.get(item_row.name, 0) > 0:
            returned_qty = flt(returned_qty_map.get(item_row.name, 0))
            returned_qty_map[item_row.name] -= pending_qty

        if returned_qty:
            if returned_qty >= pending_qty:
                pending_qty = 0
            else:
                pending_qty -= returned_qty

        to_make_invoice_qty_map[item_row.name] = pending_qty

        return pending_qty

    # Map Delivery Note to Sales Invoice
    sales_invoice = get_mapped_doc(
        "Delivery Note",
        doc.name,
        {
            "Delivery Note": {
                "doctype": "Sales Invoice",
                "field_map": {"is_return": "is_return"},
                "validation": {"docstatus": ["=", 1]},
            },
            "Delivery Note Item": {
                "doctype": "Sales Invoice Item",
                "field_map": {
                    "name": "dn_detail",
                    "parent": "delivery_note",
                    "so_detail": "so_detail",
                    "against_sales_order": "sales_order",
                    "serial_no": "serial_no",
                    "cost_center": "cost_center",
                    "custom_delivery_note_no":"custom_delivery_note_no",
                    "custom_tax_rate":"custom_tax_rate",
                    "custom_tax_amount":"custom_tax_amount",
                },
                "postprocess": update_item,
                "filter": lambda d: get_pending_qty(d) <= 0
                if not doc.get("is_return")
                else get_pending_qty(d) > 0,
            },
            "Sales Taxes and Charges": {
                "doctype": "Sales Taxes and Charges",
                "add_if_empty": True,
            },
            "Sales Team": {
                "doctype": "Sales Team",
                "field_map": {"incentives": "incentives"},
                "add_if_empty": True,
            },
        },
        None,
        set_missing_values,
    )

    # Include payment handling logic here
    # Only fetch payment information from one item linked to a sales order
    sales_order = None
    for item in doc.items:
        if item.against_sales_order:
            sales_order = frappe.get_doc("Sales Order", item.against_sales_order)
            break  # Break after getting the first Sales Order

    if sales_order and sales_order.custom_sales_type=="Cash":
        add_payments_from_sales_order(sales_order, sales_invoice)
        sales_invoice.is_pos = 1 
    if cint(frappe.db.get_single_value("Accounts Settings", "automatically_fetch_payment_terms")):
        sales_invoice.set_payment_schedule()

    sales_invoice.save()
    sales_invoice.submit()
    frappe.msgprint(_("Sales Invoice {0} created successfully").format(sales_invoice.name))

    return sales_invoice

def add_payments_from_sales_order(sales_order, sales_invoice):
    """Add payment entries from custom_order_payment table to the Sales Invoice payments table."""

    # Check if there are payments to add
    if not sales_order.custom_order_payment:
        frappe.msgprint(_("No payments found in custom_order_payment for Sales Order: {0}").format(sales_order.name))
        return
    
    # Append each payment
    for payment in sales_order.custom_order_payment:
        sales_invoice.append("payments", {
            "mode_of_payment": payment.mode_of_payment,
            "amount": payment.amount,
        })


def get_returned_qty_map(delivery_note):
    """Returns a map: {dn_detail: returned_qty}"""
    returned_qty_map = frappe._dict(
        frappe.db.sql(
            """select dn_item.dn_detail, abs(dn_item.qty) as qty
               from `tabDelivery Note Item` dn_item, `tabDelivery Note` dn
               where dn.name = dn_item.parent
               and dn.docstatus = 1
               and dn.is_return = 1
               and dn.return_against = %s""",
            delivery_note,
        )
    )
    return returned_qty_map

def get_invoiced_qty_map(delivery_note):
    """Returns a map: {dn_detail: invoiced_qty}"""
    invoiced_qty_map = frappe._dict()
    for dn_detail, qty in frappe.db.sql(
        """select dn_detail, qty from `tabSales Invoice Item`
           where delivery_note=%s and docstatus=1""",
        delivery_note,
    ):
        invoiced_qty_map[dn_detail] = invoiced_qty_map.get(dn_detail, 0) + qty
    return invoiced_qty_map


@frappe.whitelist(allow_guest=True)
def get_series(doc_name):
    delivery_note = frappe.get_doc("Delivery Note", doc_name)
    
    # Assuming the Delivery Note name starts with "DN-", remove the "DN-" part and return only the number
    if delivery_note.name.startswith("DN-"):
        number_part = delivery_note.name.replace("DN-", "")
    else:
        number_part = delivery_note.name
    
    return number_part

def order_no_generated(doc_name):
    series=get_series(doc_name)
    frappe.db.set_value("Delivery Note",doc_name,"custom_delivery_note_no",series)
