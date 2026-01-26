import frappe
from frappe import _
from frappe.utils import flt


def on_submit(doc, method):
    update_unit_rent_details(doc, update=True)

def before_cancel(doc, method):
    doc.ignore_linked_doctypes = (  
        "GL Entry",  
        "Stock Ledger Entry",  
        "Payment Ledger Entry",  
        "Repost Payment Ledger",  
        "Repost Payment Ledger Items",  
        "Repost Accounting Ledger",  
        "Repost Accounting Ledger Items",  
        "Unreconcile Payment",  
        "Unreconcile Payment Entries",  
        "Advance Payment Ledger Entry",  
        "unit",
        "Unit Rent Detail"
    )
    update_unit_rent_details(doc, update=False)
    # unlink_unit_rent_details(doc, method)


def validate_unit_paid_amounts(doc, method):
    rent_detail = frappe.db.get_value("Unit Rent Detail", {"rent_payment_entry": doc.name}, "monthly_rent_amount")
    if rent_detail and flt(rent_detail, 2) != flt(doc.paid_amount, 2):
        frappe.throw(_("Paid amount is not equal to the monthly rent amount"))

    revenue_share_detail = frappe.db.get_value("Unit Rent Detail", {"revenue_share_payment_entry": doc.name}, "required_amount")
    if revenue_share_detail and flt(revenue_share_detail, 2) != flt(doc.paid_amount, 2):
        frappe.throw(_("Paid amount is not equal to the required amount"))


def update_unit_rent_details(doc, update=True):
    rent_detail = frappe.db.get_value("Unit Rent Detail", {"rent_payment_entry": doc.name}, "name")
    if rent_detail:
        if update:
            frappe.db.set_value("Unit Rent Detail", rent_detail, "paid_amount", doc.paid_amount)
        else:
            frappe.db.set_value("Unit Rent Detail", rent_detail, "paid_amount", 0)

    revenue_share_detail = frappe.db.get_value("Unit Rent Detail", {"revenue_share_payment_entry": doc.name}, "name")
    if revenue_share_detail:
        if update:
            frappe.db.set_value("Unit Rent Detail", revenue_share_detail, "revenue_share_paid_amount", doc.paid_amount)
        else:
            frappe.db.set_value("Unit Rent Detail", revenue_share_detail, "revenue_share_paid_amount", 0)


@frappe.whitelist()
def unlink_unit_rent_details(doc, method):
    payment_entry = doc.name
    try:
        rent_details = frappe.db.get_all("Unit Rent Detail", filters={"rent_payment_entry": payment_entry})
        for rent_detail in rent_details:
            frappe.db.set_value("Unit Rent Detail", rent_detail.name, "rent_payment_entry", None)
        frappe.msgprint(f"Unit rent details unlinked successfully for payment entry: {payment_entry}", alert=True, indicator='green')
    except Exception as e:
        frappe.log_error(f"Error unlinking unit rent details: {str(e)}")
        frappe.throw(f"Error unlinking unit rent details: {str(e)}")

    try:
        revenue_share_details = frappe.db.get_all("Unit Rent Detail", filters={"revenue_share_payment_entry": payment_entry})
        for revenue_share_detail in revenue_share_details:
            frappe.db.set_value("Unit Rent Detail", revenue_share_detail.name, "revenue_share_payment_entry", None)
        frappe.msgprint(f"Revenue share details unlinked successfully for payment entry: {payment_entry}", alert=True, indicator='green')
    except Exception as e:
        frappe.log_error(f"Error unlinking revenue share details: {str(e)}")
        frappe.throw(f"Error unlinking revenue share details: {str(e)}")