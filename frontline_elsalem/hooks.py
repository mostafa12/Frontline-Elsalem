from . import __version__ as app_version

app_name = "frontline_elsalem"
app_title = "Frontline Elsalem"
app_publisher = "Al-Salem Holding"
app_description = "New Custom App by Frontline"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "erp@alsalemholding.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/frontline_elsalem/css/frontline_elsalem.css"
# app_include_js = "/assets/frontline_elsalem/js/frontline_elsalem.js"

# include js, css files in header of web template
# web_include_css = "/assets/frontline_elsalem/css/frontline_elsalem.css"
# web_include_js = "/assets/frontline_elsalem/js/frontline_elsalem.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "frontline_elsalem/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Payment Entry" : "public/js/payment_entry.js",
	"Sales Invoice" : "public/js/sales_invoice.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "frontline_elsalem.install.before_install"
# after_install = "frontline_elsalem.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "frontline_elsalem.uninstall.before_uninstall"
# after_uninstall = "frontline_elsalem.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "frontline_elsalem.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"Payment Entry": "frontline_elsalem.overrides.payment_entry.CustomPaymentEntry"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Sales Invoice": {
		"before_cancel": "frontline_elsalem.overrides.sales_invoice.before_cancel"
	},
	"Payment Entry": {
		"on_trash": "frontline_elsalem.overrides.payment_entry.unlink_unit_rent_details",
		"validate": "frontline_elsalem.overrides.payment_entry.validate_unit_paid_amounts",
		"on_submit": "frontline_elsalem.overrides.payment_entry.on_submit",
		"before_cancel": "frontline_elsalem.overrides.payment_entry.before_cancel"
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"frontline_elsalem.frontline_elsalem.doctype.unit.unit.update_revenue_share_amount"
	]
}

# Testing
# -------

# before_tests = "frontline_elsalem.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "frontline_elsalem.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "frontline_elsalem.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Request Events
# ----------------
# before_request = ["frontline_elsalem.utils.before_request"]
# after_request = ["frontline_elsalem.utils.after_request"]

# Job Events
# ----------
# before_job = ["frontline_elsalem.utils.before_job"]
# after_job = ["frontline_elsalem.utils.after_job"]

# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"frontline_elsalem.auth.validate"
# ]

