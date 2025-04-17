import frappe

def get_permission_query_conditions(user):
    if not user:
        user = frappe.session.user

    # Allow Administrator to see all records
    if user == "Administrator":
        return ""
        
    allowed_branches = get_allowed_branches(user)

    if not allowed_branches:
        return "1=0"

    allowed_branches = [f"'{b}'" for b in allowed_branches]
    branch_list = ", ".join(allowed_branches)
    
    return f" EXISTS (SELECT 1 FROM `tabItem Default` AS d WHERE d.parent = `tabItem`.name AND d.custom_branch IN ({branch_list})) "

def get_allowed_branches(user):
    return frappe.get_all(
        "User Permission",
        filters={"user": user, "allow": "Branch"},
        pluck="for_value"
    )
