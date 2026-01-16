import frappe
from frappe.utils import flt
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry as ParentStockEntry


class StockEntry(ParentStockEntry):
    """Custom Stock Entry class to override mark_finished_and_scrap_items method and calculation methods"""
    
    def mark_finished_and_scrap_items(self):
        """
        Override mark_finished_and_scrap_items for Stock Entry.
        For repack purpose, don't force all items with t_target to have is_finished_item.
        """
        # Keep all original ERPNext logic except for Repack handling
        company = frappe.get_doc("Company", self.company)
        if "custom_bypass_finished_item_check_in_repack" in [f.fieldname for f in company.meta.get("fields")]:
            custom_bypass_finished_item_check_in_repack = company.get("custom_bypass_finished_item_check_in_repack") or 0
        else:
            custom_bypass_finished_item_check_in_repack = 0
            
        if self.purpose != "Repack" and any(
            [d.item_code for d in self.items if (d.is_finished_item and d.t_warehouse)]
        ):
            return
        finished_item = self.get_finished_item()

        if not finished_item and self.purpose == "Manufacture":
            # In case of independent Manufacture entry, don't auto set
            # user must decide and set
            return

        for d in self.items:
            if d.t_warehouse and not d.s_warehouse:
                # For Repack, don't auto-mark anything (user decides)
                
                if self.purpose == "Repack":
                    
                    if custom_bypass_finished_item_check_in_repack:
                        if d.item_code == finished_item:
                            d.is_finished_item = 1
                        else:
                            pass  # Don't auto-mark as scrap either
                    else:
                        d.is_finished_item = 1
                        
                elif d.item_code == finished_item:
                    d.is_finished_item = 1
                else:
                    d.is_scrap_item = 1
            else:
                d.is_finished_item = 0
                d.is_scrap_item = 0
    
    
    def calculate_rate_and_amount(self, reset_outgoing_rate=True, raise_error_if_no_rate=True):
        """
        Override to ensure repack finished items use the modified outgoing_items_cost
        """
        # Use our overridden set_basic_rate which uses modified outgoing_items_cost
        self.set_basic_rate(reset_outgoing_rate, raise_error_if_no_rate)
        
        # Call the rest of the parent method's logic
        from erpnext.stock.doctype.stock_entry.stock_entry import init_landed_taxes_and_totals
        init_landed_taxes_and_totals(self)
        self.distribute_additional_costs()
        self.update_valuation_rate()
        self.set_total_incoming_outgoing_value()
        self.set_total_amount()
        
        
    def set_total_incoming_outgoing_value(self):
        """
        Override to exclude additional scrap items from total_outgoing_value calculation
        when custom_bypass_repack is ticked for Repack purpose
        """
        # Check if we should bypass repack calculations
        should_bypass = (
            self.purpose == "Repack" and 
            self.get("custom_bypass_repack")
        )
        
        self.total_incoming_value = self.total_outgoing_value = 0.0
        additional_scrap_amount = 0.0
        
        # First, calculate the standard total_outgoing_value (includes all items with s_warehouse)
        for d in self.get("items"):
            if d.t_warehouse:
                # Only exclude scrap items if it's Repack with bypass enabled
                if should_bypass and (d.get("custom_is_additional_scrap") and d.get("is_scrap_item")):
                    # Skip additional scrap items from total_incoming_value
                    pass
                else:
                    self.total_incoming_value += flt(d.amount) 
            
            if d.s_warehouse:
                self.total_outgoing_value += flt(d.amount)
        
        # Then, if bypass is enabled, subtract additional scrap items' basic_amount
        if should_bypass:
            
            for d in self.get("items"):
                if d.t_warehouse:
                    # Check if this is an additional scrap item that should be subtracted
                    is_additional_scrap = (
                        d.get("custom_is_additional_scrap") and
                        d.get("is_scrap_item")
                    )
                    
                    if is_additional_scrap:
                        # Subtract the basic_amount from total_outgoing_value
                        # Use basic_amount (not amount) for additional scrap items
                        scrap_basic_amount = flt(d.basic_amount)
                        self.total_outgoing_value -= scrap_basic_amount
                        additional_scrap_amount += scrap_basic_amount
        
        # Store the subtracted scrap basic_amount
        if should_bypass:
            
            self.custom_total_outgoingscrap = additional_scrap_amount
            self.total_incoming_value -= additional_scrap_amount
        else:
            self.custom_total_outgoingscrap = 0.0
        
        self.value_difference = self.total_incoming_value - self.total_outgoing_value
        # frappe.throw(str(self.value_difference))
    
    def set_rate_for_outgoing_items(self, reset_outgoing_rate=True, raise_error_if_no_rate=True):
        """
        Override to exclude additional scrap items from outgoing_items_cost calculation
        when custom_bypass_repack is ticked for Repack purpose
        """
        from erpnext.stock.stock_ledger import get_incoming_rate
        
        # Check if we should bypass repack calculations
        should_bypass = (
            self.purpose == "Repack" and 
            self.get("custom_bypass_repack")
        )
        
        outgoing_items_cost = 0.0
        additional_scrap_cost = 0.0
        
        for d in self.get("items"):
            if d.s_warehouse:
                # Check if this is an additional scrap item (scrap items have t_warehouse, not s_warehouse)
                # So items with s_warehouse are regular outgoing items
                # Still calculate basic_rate for all items
                if reset_outgoing_rate:
                    args = self.get_args_for_incoming_rate(d)
                    rate = get_incoming_rate(args, raise_error_if_no_rate)
                    if rate >= 0:
                        d.basic_rate = rate
                
                d.basic_amount = flt(flt(d.transfer_qty) * flt(d.basic_rate), d.precision("basic_amount"))
                
                # Add to outgoing_items_cost if no t_warehouse (pure outgoing items)
                if not d.t_warehouse:
                    outgoing_items_cost += flt(d.basic_amount)
            
            # Also check items with t_warehouse for additional scrap items
            # Scrap items have t_warehouse (target warehouse) and should be subtracted
            if d.t_warehouse and should_bypass:
                is_additional_scrap = (
                    d.get("custom_is_additional_scrap") and
                    d.get("is_scrap_item")
                )
                
                if is_additional_scrap:
                    
                    # Calculate basic_rate for scrap items if not already calculated
                    if reset_outgoing_rate and not d.basic_rate:
                        args = self.get_args_for_incoming_rate(d)
                        rate = get_incoming_rate(args, raise_error_if_no_rate)
                        if rate >= 0:
                            d.basic_rate = rate
                    
                    d.basic_amount = flt(flt(d.transfer_qty) * flt(d.basic_rate), d.precision("basic_amount"))
                    additional_scrap_cost += flt(d.basic_amount)
        
        # Subtract additional scrap cost from outgoing_items_cost
        outgoing_items_cost -= additional_scrap_cost
        return outgoing_items_cost


@frappe.whitelist()
def recalculate_repack_basic_rate(stock_entry_name):
    """
    Backend function to recalculate basic_rate for repack finished items
    when custom_bypass_repack is enabled
    """
    doc = frappe.get_doc("Stock Entry", stock_entry_name)
    
    if doc.purpose == "Repack" and doc.get("custom_bypass_repack"):
        outgoing_items_cost = 0.0
        additional_scrap_cost = 0.0
        
        for d in doc.items:
            if d.s_warehouse:
                if not d.t_warehouse:
                    is_additional_scrap = (
                        d.get("custom_is_additional_scrap") and
                        d.get("is_scrap_item")
                    )
                    if not is_additional_scrap:
                        outgoing_items_cost += flt(d.basic_amount)
            
            if d.t_warehouse:
                is_additional_scrap = (
                    d.get("custom_is_additional_scrap") and
                    d.get("is_scrap_item")
                )
                if is_additional_scrap:
                    additional_scrap_cost += flt(d.basic_amount)
        
        # Subtract scrap cost
        outgoing_items_cost -= additional_scrap_cost
        
        total_finished_qty = sum([flt(d.transfer_qty) for d in doc.items if d.is_finished_item and d.t_warehouse])
        
        # frappe.db.set_value("Stock Entry", stock_entry_name, "total_incoming_value", outgoing_items_cost + doc.total_additional_costs)
        if total_finished_qty:
            calculated_rate = flt(outgoing_items_cost / total_finished_qty)
            updated_items = []
            for d in doc.items:
                if d.is_finished_item and d.t_warehouse and d.transfer_qty:
                    # Only update if rate is significantly different (more than 0.01)
                    if abs(flt(d.basic_rate) - calculated_rate) > 0.01:
                        new_basic_amount = flt(flt(d.transfer_qty) * calculated_rate, d.precision("basic_amount"))
                        new_amount = flt(new_basic_amount + flt(d.additional_cost), d.precision("amount"))
                        new_valuation_rate = flt(calculated_rate) + (flt(d.additional_cost) / flt(d.transfer_qty)) if d.transfer_qty else calculated_rate
                        
                        frappe.db.set_value("Stock Entry Detail", d.name, {
                            "basic_rate": calculated_rate,
                            "basic_amount": new_basic_amount,
                            "amount": new_amount,
                            "valuation_rate": new_valuation_rate
                        })
                        updated_items.append(d.name)
            
            if updated_items:
                frappe.db.commit()
                return {
                    "success": True,
                    "calculated_rate": calculated_rate,
                    "updated_items": updated_items
                }
    
    return {"success": False, "message": "Not a repack entry with bypass enabled"}
   