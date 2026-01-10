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
        
        for d in self.get("items"):
            if d.t_warehouse:
                self.total_incoming_value += flt(d.amount)
            
            if d.s_warehouse:
                # Check if this is an additional scrap item that should be excluded
                is_additional_scrap = (
                    should_bypass and
                    d.get("custom_is_additional_scrap") and
                    d.get("is_scrap_item")
                )
                
                if is_additional_scrap:
                    # Exclude from total_outgoing_value but track the amount
                    additional_scrap_amount += flt(d.amount)
                else:
                    self.total_outgoing_value += flt(d.amount)
        
        # Store the excluded scrap amount
        if should_bypass:
            self.custom_total_outgoingscrap = additional_scrap_amount
        else:
            self.custom_total_outgoingscrap = 0.0
        
        self.value_difference = self.total_incoming_value - self.total_outgoing_value
    
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
        for d in self.get("items"):
            if d.s_warehouse:
                # Check if this is an additional scrap item that should be excluded
                is_additional_scrap = (
                    should_bypass and
                    d.get("custom_is_additional_scrap") and
                    d.get("is_scrap_item")
                )
                
                if reset_outgoing_rate and not is_additional_scrap:
                    args = self.get_args_for_incoming_rate(d)
                    rate = get_incoming_rate(args, raise_error_if_no_rate)
                    if rate >= 0:
                        d.basic_rate = rate
                
                d.basic_amount = flt(flt(d.transfer_qty) * flt(d.basic_rate), d.precision("basic_amount"))
                
                # Only add to outgoing_items_cost if not additional scrap and no t_warehouse
                if not d.t_warehouse and not is_additional_scrap:
                    outgoing_items_cost += flt(d.basic_amount)
        
        return outgoing_items_cost