import frappe
from frappe.utils import today


'''TODO: revisist for better solution'''
@frappe.whitelist(allow_guest=True)
def get_price_list_rate(item_code, price_list, customer):
    """
    Fetch the price list rate for a given item code and price list.
    
    Parameters:
    item_code (str): The item code for which to fetch the price list rate.
    price_list (str): The price list to use for fetching the rate.
    customer (str): The customer to check for specific pricing.

    Returns:
    float: The price list rate for the item or 0 if not found.
    """
    
    # Attempt to fetch the price for the specific customer
    item_price = frappe.db.get_value(
        "Item Price",
        {
            "item_code": item_code,
            "price_list": price_list,
            "customer": customer,
            "valid_upto": [">", today()],
        },
        "price_list_rate"
    )

    # If a valid customer-specific price is found, return it
    if item_price:
        frappe.response.message = item_price
        return item_price  
    # If no item price was found for the customer, fetch the latest price list rate
    item_price = frappe.db.get_value(
        "Item Price",
        {
            "item_code": item_code,
            "price_list": price_list,
        },
        "price_list_rate",
        order_by="modified desc" 
    )
    # Set the response message and return the latest price or 0 if not found
    frappe.response.message = item_price if item_price else 0
    return item_price if item_price else 0
