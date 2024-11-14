import frappe
from frappe.utils import today
from erpnext.stock.get_item_details import get_item_price


'''TODO: revisist for better solution'''
# @frappe.whitelist(allow_guest=True)
# def get_price_list_rate(item_code, price_list, customer):
#     """
#     Fetch the price list rate for a given item code and price list.
    
#     Parameters:
#     item_code (str): The item code for which to fetch the price list rate.
#     price_list (str): The price list to use for fetching the rate.
#     customer (str): The customer to check for specific pricing.

#     Returns:
#     float: The price list rate for the item or 0 if not found.
#     """
    
#     # Attempt to fetch the price for the specific customer
#     item_price = frappe.db.get_value(
#         "Item Price",
#         {
#             "item_code": item_code,
#             "price_list": price_list,
#             "customer": customer,
#             "valid_upto": [">", today()],
#         },
#         "price_list_rate"
#     )

#     # If a valid customer-specific price is found, return it
#     if item_price:
#         frappe.response.message = item_price
#         return item_price  
#     # If no item price was found for the customer, fetch the latest price list rate
#     item_price = frappe.db.get_value(
#         "Item Price",
#         {
#             "item_code": item_code,
#             "price_list": price_list,
#         },
#         "price_list_rate",
#         order_by="modified desc" 
#     )
#     # Set the response message and return the latest price or 0 if not found
#     frappe.response.message = item_price if item_price else 0
#     return item_price if item_price else 0


@frappe.whitelist(allow_guest=True)
# def get_price_list_rate():
#     item_code=frappe.form_dict.get('item_code')
#     price_list=frappe.form_dict.get('custom_price_list')
#     customer=frappe.form_dict.get('party_name')
#     item_prices = get_item_price(
#         item_code=item_code,
#         price_list=price_list,
#         customer=customer,
#         transaction_date=today()
#     )
#     if item_prices:
#         # Returns the first matched price
#         frappe.response.message = item_prices[0][1]
        
#         return item_prices[0][1]
#     else:
#         frappe.response.message = 0
#         return 0



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
