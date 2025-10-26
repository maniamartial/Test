app_name = "nl_apex"
app_title = "Apex Piping"
app_publisher = "Navari Ltd"
app_description = "Apex customization"
app_email = "mania@navari.co.ke"
app_license = "agpl-3.0"
# required_apps = []

fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "name",
                "in",
                (
                    "Sales Invoice-custom_gross_proft",
                    "Sales Invoice-custom_gross_profit_",
                    "Delivery Note-custom_gross_proft",
                    "Delivery Note-custom_gross_profit_",
                    "BOM-custom_set_cost_per_unit",
                    "Selling Settings-custom_create_invoice_on_dnote_submission",
                    "Sales Order-custom_is_cash_sales",
                    "Selling Settings-custom_enable_price_rule",
                    
                    "Opportunity Item-custom_section_break_lnbyn",
                    "Opportunity Item-custom_is_alternative",
                    "Opportunity Item-custom_column_break_p8dlt",
                    "Opportunity Item-custom_price_list_rate",
                    "Opportunity Item-custom_is_free_item",
                    "Opportunity Item-custom_net_rate_company_currency",
                    "Opportunity Item-custom_net_rate",
                    "Opportunity Item-custom_net_amount_company_currency",
                    "Opportunity Item-custom_net_amount",
                    "Opportunity Item-custom_price_list_rate_company_currency",
                    "Opportunity Item-custom_column_break_lfoog",
                    "Opportunity Item-custom_section_break_mkuwy",
                    "Opportunity Item-custom_uom_conversion_factor",
                    "Opportunity Item-custom_column_break_iuabb",
                    "Opportunity Item-custom_stock_uom",
                    "Opportunity Item-custom_section_break_sfdpn",
                    "Opportunity Item-custom_pricing_rules",
                    "Opportunity Item-custom_column_break_lfoog"
                ),
            ]
        ],
    },

]


# Includes in <head>
# ------------------
doc_events = {
    # "*": {
    # 	"on_update": "method",
    # 	"on_cancel": "method",
    # 	"on_trash": "method"
    # }
    
    "Sales Order": {
        "validate": "nl_apex.apex_piping.overrides.sales_order.validate",
        "before_save":"nl_apex.apex_piping.overrides.sales_order.before_save",
    },
    "Delivery Note":{
        "on_submit":"nl_apex.apex_piping.overrides.delivery_note.make_sales_invoice"
    },
    "Comment":{
                "after_insert":"nl_apex.apex_piping.overrides.comments.before_save",
    },
    "BOM":{
        "before_save":"nl_apex.apex_piping.overrides.bom.set_cost_per_unit",
    },

}

# include js, css files in header of desk.html
# app_include_css = "/assets/nl_apex/css/nl_apex.css"
# app_include_js = "/assets/nl_apex/js/nl_apex.js"

# include js, css files in header of web template
# web_include_css = "/assets/nl_apex/css/nl_apex.css"
# web_include_js = "/assets/nl_apex/js/nl_apex.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "nl_apex/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {"Sales Order" : "public/js/sales_order.js",
              "Delivery Note": "public/js/delivery_note.js",
              "Opportunity": "public/js/opportunity.js",
              "BOM": "public/js/bom.js",}

# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "nl_apex/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "nl_apex.utils.jinja_methods",
# 	"filters": "nl_apex.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "nl_apex.install.before_install"
# after_install = "nl_apex.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "nl_apex.uninstall.before_uninstall"
# after_uninstall = "nl_apex.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "nl_apex.utils.before_app_install"
# after_app_install = "nl_apex.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "nl_apex.utils.before_app_uninstall"
# after_app_uninstall = "nl_apex.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "nl_apex.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# has_permission = {
#     "Item": "nl_apex.apex_piping.overrides.item.has_permission",
# }


# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Stock Entry": "nl_apex.apex_piping.overrides.stock_entry.StockEntry"
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------
scheduler_events = {
	
 "cron":{
        "0 0 * * *":["nl_apex.apex_piping.overrides.sales_order.check_and_notify_stock_status"], 
       
 },
	
}
# scheduler_events = {
# 	"all": [
# 		"nl_apex.tasks.all"
# 	],
# 	"daily": [
# 		"nl_apex.tasks.daily"
# 	],
# 	"hourly": [
# 		"nl_apex.tasks.hourly"
# 	],
# 	"weekly": [
# 		"nl_apex.tasks.weekly"
# 	],
# 	"monthly": [
# 		"nl_apex.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "nl_apex.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "nl_apex.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "nl_apex.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["nl_apex.utils.before_request"]
# after_request = ["nl_apex.utils.after_request"]

# Job Events
# ----------
# before_job = ["nl_apex.utils.before_job"]
# after_job = ["nl_apex.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"nl_apex.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

