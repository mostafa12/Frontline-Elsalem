import frappe


def before_cancel(doc, method):
    doc.ignore_linked_doctypes = (
			"GL Entry",
			"Stock Ledger Entry",
			"Repost Item Valuation",
			"Repost Payment Ledger",
			"Repost Payment Ledger Items",
			"Repost Accounting Ledger",
			"Repost Accounting Ledger Items",
			"Unreconcile Payment",
			"Unreconcile Payment Entries",
			"Payment Ledger Entry",
			"Serial and Batch Bundle",
			"Tax Withholding Entry",
            "unit",
            "Unit Rent Detail"
		)


@frappe.whitelist()
def unlink_unit_rent_details(doc, method):
    sales_invoice = doc.name
    try:
        rent_details = frappe.db.get_all("Unit Rent Detail", filters={"rent_sales_invoice": sales_invoice})
        for rent_detail in rent_details:
            frappe.db.set_value("Unit Rent Detail", rent_detail.name, "rent_sales_invoice", None)
        frappe.msgprint(f"Unit rent details unlinked successfully for sales invoice: {sales_invoice}", alert=True, indicator='green')

        revenue_share_details = frappe.db.get_all("Unit Rent Detail", filters={"revenue_share_sales_invoice": sales_invoice})
        for revenue_share_detail in revenue_share_details:
            frappe.db.set_value("Unit Rent Detail", revenue_share_detail.name, "revenue_share_sales_invoice", None)
        frappe.msgprint(f"Revenue share details unlinked successfully for sales invoice: {sales_invoice}", alert=True, indicator='green')

    except Exception as e:
        frappe.log_error(f"Error unlinking unit rent details: {str(e)}")
        frappe.throw(f"Error unlinking unit rent details: {str(e)}")