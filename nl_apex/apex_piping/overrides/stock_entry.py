import frappe
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry as ParentStockEntry


class StockEntry(ParentStockEntry):
    """Custom Stock Entry class to override mark_finished_and_scrap_items method"""
    
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
