import frappe

def get_permission_query_conditions(user):
    if not user:
        user = frappe.session.user

    if user == "Administrator":
        return ""
    
    allowed_branches = get_allowed_values(user, "Branch")
    allowed_companies = get_allowed_values(user, "Company")
    
    if not allowed_branches and not allowed_companies:
        return ""
    
    # Case 1: User has both branch and company permissions
    if allowed_branches and allowed_companies:
        allowed_branches_str = ", ".join([f"'{b}'" for b in allowed_branches])
        allowed_companies_str = ", ".join([f"'{c}'" for c in allowed_companies])
        
        # Both branch AND company must match for the item to be visible
        return f"""
            EXISTS (
                SELECT 1 FROM `tabItem Default` AS d1
                WHERE d1.parent = `tabItem`.name 
                AND d1.custom_branch IN ({allowed_branches_str})
                AND EXISTS (
                    SELECT 1 FROM `tabItem Default` AS d2
                    WHERE d2.parent = `tabItem`.name
                    AND d2.company IN ({allowed_companies_str})
                )
            )
        """
    
    # Case 2: User has only branch permissions
    elif allowed_branches:
        allowed_branches_str = ", ".join([f"'{b}'" for b in allowed_branches])
        return f"EXISTS (SELECT 1 FROM `tabItem Default` AS d WHERE d.parent = `tabItem`.name AND d.custom_branch IN ({allowed_branches_str}))"
    
    # Case 3: User has only company permissions
    else: 
        allowed_companies_str = ", ".join([f"'{c}'" for c in allowed_companies])
        return f"EXISTS (SELECT 1 FROM `tabItem Default` AS d WHERE d.parent = `tabItem`.name AND d.company IN ({allowed_companies_str}))"

def get_allowed_values(user, doctype):
    return frappe.get_all(
        "User Permission",
        filters={"user": user, "allow": doctype},
        pluck="for_value"
    )