import frappe
from frappe.utils import today
from erpnext.stock.get_item_details import get_item_price

@frappe.whitelist(allow_guest=True)
def get_price_list_rate():
    # Retrieve parameters from the request
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
        frappe.throw(str(item_prices))
        frappe.response.message = item_prices[0]["price_list_rate"]
        return item_prices[0]["price_list_rate"]
    else:
        frappe.response.message = 0
        return 0
