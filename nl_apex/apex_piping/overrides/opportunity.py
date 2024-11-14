import frappe
from frappe.utils import today
from erpnext.stock.get_item_details import get_item_price

@frappe.whitelist(allow_guest=True)
def get_price_list_rate():
    # Retrieve parameters from the request
    item_code = frappe.form_dict.get('item_code')
    price_list = frappe.form_dict.get('custom_price_list')
    customer = frappe.form_dict.get('party_name')

    # Create args dictionary to pass to get_item_price
    args = {
        "price_list": price_list,
        "customer": customer,
        "transaction_date": today(),
        # You can add more conditions like uom, batch_no if required
    }

    # Call get_item_price with args dictionary and item_code
    item_prices = get_item_price(args, item_code)

    # Check if a price was found and return the first match or 0
    if item_prices:
        frappe.throw(str(item_prices))
        # Returns the first matched price
        frappe.response.message = item_prices[0]["price_list_rate"]
        return item_prices[0]["price_list_rate"]
    else:
        frappe.throw(str(item_prices))
        frappe.response.message = 0
        return 0
