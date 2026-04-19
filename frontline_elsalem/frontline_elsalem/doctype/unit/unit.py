# Copyright (c) 2024, frontline solutions and contributors
# For license information, please see license.txt

# Import necessary modules
import frappe
from frappe import _
from frappe.utils import add_to_date, nowdate, flt, getdate
from frappe.model.document import Document
from erpnext.accounts.party import get_party_account
from erpnext.accounts.utils import get_account_currency
from dateutil.relativedelta import relativedelta

from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry


class unit(Document):
    def validate(self):
        if self.unit_status == 'Rent' and not self.brand_name:
            frappe.throw(_("Brand Name is required for Rent units"))

        if not self.is_revenue_share:
            self.revenue_percent = 0

        self.set_rent_contract_end_date()
        self.calculate_required_amount()
        self.calculate_total_installments()
        self.calculate_total_maintenance_amount()
        self.validate_duplicate_maintenance_dates()

    def set_rent_contract_end_date(self):
        if self.unit_status == 'Rent' and self.rent_contract_start_date:
            end_date = add_to_date(self.rent_contract_start_date, months=self.rent_contract_duration)
            self.rent_contract_end_date = add_to_date(end_date, days=-1)

    def calculate_required_amount(self):
        for row in self.rent_contract_details:
            revenue_share_amount = row.revenue_share_amount or 0
            monthly_rent_amount = row.monthly_rent_amount or 0

            required_amount = 0
            if revenue_share_amount > monthly_rent_amount:
                required_amount = revenue_share_amount - monthly_rent_amount

            row.required_amount = required_amount

    @frappe.whitelist()
    def generate_rent_details(self):
        if self.unit_status == 'Rent':
            can_generate = True
            if self.rent_contract_details:
                for row in self.rent_contract_details:
                    if row.rent_sales_invoice or row.rent_payment_entry or row.revenue_share_sales_invoice or row.revenue_share_payment_entry:
                        can_generate = False
                        break

            if not can_generate:
                frappe.throw(_("You cannot generate rent details because there are references to rent sales invoices or payment entries"))

            if not self.brand_name:
                frappe.throw(_("Please select Brand Name first"))

            if not self.monthly_rent_amount:
                frappe.throw(_("Please set Monthly Rent Amount first"))
            
            self.rent_contract_details = []
            base_rent = self.monthly_rent_amount or 0
            increase_type = (self.yearly_increase_type or "").strip()
            rent_type = (self.rent_type or "Monthly").strip()

            i = 0
            while i < self.rent_contract_duration:
                if rent_type == "Quarterly":
                    period_months = min(3, self.rent_contract_duration - i)
                else:
                    period_months = 1

                # Calculate which year we're in (0-indexed) from period start month
                year = i // 12
                if increase_type == "Amount":
                    monthly_rent = base_rent + (flt(self.yearly_increase_amount or 0) * year) if year > 0 else base_rent
                elif increase_type == "Percentage":
                    pct = flt(self.rent_contract_increase_percent or 0)
                    increase_percent = pct / 100 if pct > 0 else 0
                    monthly_rent = base_rent * ((1 + increase_percent) ** year)
                else:
                    monthly_rent = base_rent

                current_rent = monthly_rent

                period_start = add_to_date(self.rent_contract_start_date, months=i)
                next_period_start = add_to_date(self.rent_contract_start_date, months=i + period_months)
                period_end = getdate(next_period_start) - relativedelta(days=1)

                revenue_share_amount = 0
                if self.brand_name == 'تاون تيم':
                    townteam_amount = get_townteam_net_amount(period_start, period_end)
                    revenue_share_amount = townteam_amount * (flt(self.revenue_percent) / 100) if flt(self.revenue_percent) > 0 else 0

                required_amount = 0
                if revenue_share_amount > current_rent:
                    required_amount = revenue_share_amount - current_rent

                payment_type = (
                    'إيجار شهرى' if rent_type == "Monthly" else 'إيجار ربع سنوى'
                )

                self.append('rent_contract_details', {
                    'payment_type': payment_type,
                    'monthly_rent_amount': current_rent,
                    'revenue_share_amount': revenue_share_amount if getdate() >= period_end else 0,
                    'rent_date': period_start,
                    'revenue_share_date': period_end,
                    'required_amount': required_amount
                })

                i += period_months


    @frappe.whitelist()
    def update_payment_methods(self):
        mode_of_payment = self.mode_of_payment
        if mode_of_payment:
            for contract in self.get("contract_details"):
                contract.paymentmethod = mode_of_payment
        self.save()


    def get_default_account(self, mode_of_payment, company):
        # Fetch the Mode of Payment document
        mop = frappe.get_doc('Mode of Payment', mode_of_payment)
        
        # Loop through the accounts table to find the default account for the given company
        for account in mop.accounts:
            if account.company == company:
                return account.default_account
        
        # Return None if no matching account is found
        return None

    def calculate_total_installments(self):
        self.total_installments = 0
        self.total_paid = 0
        self.total_remaining = 0

        for row in self.contract_details:
            self.total_installments += flt(row.installments)
            self.total_paid += flt(row.paid)
            self.total_remaining += flt(row.remaining)
        
        self.custom_collection_rate = (flt(self.total_paid) / flt(self.total_installments)) * 100 if flt(self.total_installments) > 0 else 0

    def calculate_total_maintenance_amount(self):
        for row in self.maintenance_details:
            self.total = flt(row.maintenance_amount) + flt(row.water_amount) + flt(row.penalty_amount)

            if self.total == 0 or self.total is None:
                frappe.throw(_(f"Total maintenance amount cannot be zero for row {row.idx}"))
            elif self.total < 0:
                frappe.throw(_(f"Total maintenance amount cannot be negative for row {row.idx}"))

    def validate_duplicate_maintenance_dates(self):
        seen_months = set()
        duplicate_months = []
        for row in self.maintenance_details:
            if not row.date:
                continue
            d = getdate(row.date)
            key = (d.year, d.month)
            if key in seen_months:
                duplicate_months.append(key)
            else:
                seen_months.add(key)

        if duplicate_months:
            months_str = ", ".join(
                f"{y:04d}-{m:02d}" for y, m in sorted(set(duplicate_months))
            )
            frappe.throw(
                _(
                    "Maintenance dates cannot be duplicate for the following months: {0}"
                ).format(months_str)
            )


@frappe.whitelist()
def get_townteam_net_amount(from_date, to_date):
    net_amount = frappe.db.sql(
        """
        SELECT 
            SUM(NetAmount) as total_net_amount
        FROM `TownTeamFinal4`
        WHERE TRANSDATE BETWEEN %s AND %s
        """,
        (from_date, to_date),
        as_dict=True
    )
    
    return net_amount[0].total_net_amount if net_amount and net_amount[0].total_net_amount else 0


@frappe.whitelist()
def get_revenue_share_amount(brand, from_date, to_date):
    """
    Get the net_amount for a given brand and date range from Revenue Share doctype
    brand: str
    from_date: datetime
    to_date: datetime
    """

    store_id = None
    if brand in ['Asawer', 'Pino', 'Wadeda', 'Borest']:
        if brand == 'Asawer':
            store_id = 7
        elif brand == 'Pino':
            store_id = 5
        elif brand == 'Wadeda':
            store_id = 3
        elif brand == 'Borest':
            store_id = 1

        brand = 'Bocrest/Wadeda/Pino/Asawer'
    
    if store_id:
        revenue_share = frappe.db.sql(
            """
            SELECT 
                SUM(net_amount) as total_net_amount
            FROM `tabRevenue Share`
            WHERE brand = %s AND store_id = %s AND transaction_date_and_time BETWEEN %s AND %s
            """,
            (brand, store_id, from_date, to_date),
            as_dict=True
        )
    else:
        revenue_share = frappe.db.sql(
            """
            SELECT 
                SUM(net_amount) as total_net_amount
            FROM `tabRevenue Share`
            WHERE brand = %s AND transaction_date_and_time BETWEEN %s AND %s
            """,
            (brand, from_date, to_date),
            as_dict=True
        )
    return revenue_share[0].total_net_amount if revenue_share and revenue_share[0].total_net_amount else 0


@frappe.whitelist()
def generate_rent_transactions(company, brand_name, rowname, mode_of_payment=None):
    # First create a sales invoice for the rent amount and ايجار محل تجارى item
    try:
        row = frappe.get_doc("Unit Rent Detail", rowname)
        invoice = frappe.new_doc("Sales Invoice")
        invoice.customer = brand_name
        invoice.company = company
        invoice.set_posting_time = 1
        invoice.posting_date = row.rent_date
        invoice.posting_time = "00:00:00"
        invoice.due_date = row.rent_date
        invoice.update_stock = 0
        invoice.debit_to = get_account_paid_from()
        invoice.append("items", {
            "item_code": "ايجار محل تجارى",
            "item_name": "ايجار محل تجارى",
            "qty": 1,
            "rate": row.monthly_rent_amount,
        })
        invoice.set_missing_values()
        invoice.insert(ignore_permissions=True)
        invoice.submit()
        row.db_set("rent_sales_invoice", invoice.name)
        frappe.msgprint(f"Rent sales invoice created successfully: {invoice.name}", alert=True, indicator='green')

        # Create payment entry for the rent amount
        payment_entry = get_payment_entry(dt="Sales Invoice", dn=invoice.name)

        payment_entry.posting_date = row.rent_date
        payment_entry.paid_from = get_account_paid_from()
        payment_entry.paid_amount = row.monthly_rent_amount
        payment_entry.reference_no = invoice.name
        payment_entry.reference_date = invoice.posting_date
        payment_entry.set_missing_values()
        payment_entry.set_exchange_rate()
        payment_entry.flags.ignore_validate = True
        payment_entry.insert(ignore_permissions=True, ignore_mandatory=True)

        row.db_set("rent_payment_entry", payment_entry.name)
        frappe.msgprint(f"Payment entry created successfully: {payment_entry.name}", alert=True, indicator='green')
    except Exception as e:
        frappe.log_error(f"Error generating rent transactions: {str(e)}")
        frappe.throw(f"Error generating rent transactions: {str(e)}")


@frappe.whitelist()
def generate_revenue_share_transactions(company, brand_name, rowname, mode_of_payment=None):
    # First create a sales invoice for the revenue share amount and 'Revenue Share' item
    try:
        row = frappe.get_doc("Unit Rent Detail", rowname)
        
        # Validate that revenue share date has passed
        if row.revenue_share_date:
            if getdate(nowdate()) < getdate(row.revenue_share_date):
                frappe.throw(_("Cannot create revenue share transactions before the revenue share date: {0}").format(
                    frappe.format(row.revenue_share_date, {"fieldtype": "Date"})
                ))
        invoice = frappe.new_doc("Sales Invoice")
        invoice.customer = brand_name
        invoice.company = company
        invoice.set_posting_time = 1
        invoice.posting_date = row.revenue_share_date
        invoice.posting_time = "00:00:00"
        invoice.due_date = row.revenue_share_date
        invoice.update_stock = 0
        invoice.debit_to = get_account_paid_from()
        invoice.append("items", {
            "item_code": "Revenue Share",
            "item_name": "Revenue Share",
            "qty": 1,
            "rate": row.required_amount,
        })
        invoice.set_missing_values()
        invoice.insert(ignore_permissions=True)
        invoice.submit()
        row.db_set("revenue_share_sales_invoice", invoice.name)

        # Update the revenue share details table
        unit = frappe.get_doc("unit", row.parent)
        for detail in unit.revenue_share_details:
            if getdate(detail.start_date) <= getdate(row.revenue_share_date) <= getdate(detail.end_date):
                detail.db_set("sales_invoice", invoice.name)
                break
        
        frappe.msgprint(f"Revenue share sales invoice created successfully: {invoice.name}", alert=True, indicator='green')

        payment_entry = get_payment_entry(dt="Sales Invoice", dn=invoice.name)

        payment_entry.posting_date = row.revenue_share_date
        payment_entry.paid_from = get_account_paid_from()
        payment_entry.paid_amount = row.required_amount
        payment_entry.reference_no = invoice.name
        payment_entry.reference_date = invoice.posting_date

        payment_entry.set_missing_values()
        payment_entry.set_exchange_rate()
        payment_entry.flags.ignore_validate = True
        payment_entry.insert(ignore_permissions=True, ignore_mandatory=True)

        row.db_set("revenue_share_payment_entry", payment_entry.name)
        frappe.msgprint(f"Revenue share payment entry created successfully: {payment_entry.name}", alert=True, indicator='green')
    except Exception as e:
        frappe.log_error(f"Error generating revenue share transactions: {str(e)}")
        frappe.throw(f"Error generating revenue share transactions: {str(e)}")


maintenance_items = [
    {
        "item_code": "صيانة محل تجارى",
        "rate_field": "maintenance_amount",
    },
    {
        "item_code": "مياه محلات",
        "rate_field": "water_amount",
    },
    {
        "item_code": "SER-10186",
        "rate_field": "penalty_amount",
    }
]


@frappe.whitelist()
def generate_maintenance_transactions(company, brand_name, rowname, mode_of_payment=None):
    try:
        row = frappe.get_doc("Unit Maintenance Detail", rowname)
        if row.sales_invoice or row.payment_entry:
            frappe.throw(_("Sales Invoice or Payment Entry already exists for this maintenance row"))

        if not brand_name:
            frappe.throw(_("Brand Name (customer) is required"))

        invoice = frappe.new_doc("Sales Invoice")
        invoice.customer = brand_name
        invoice.company = company
        invoice.set_posting_time = 1
        invoice.posting_date = row.date
        invoice.posting_time = "00:00:00"
        invoice.due_date = row.date
        invoice.update_stock = 0
        invoice.debit_to = get_account_paid_from()

        grand_total = 0
        for spec in maintenance_items:
            rate = flt(getattr(row, spec["rate_field"], None) or 0)
            if rate <= 0:
                continue
            grand_total += rate
            item_name = frappe.db.get_value("Item", spec["item_code"], "item_name") or spec["item_code"]
            invoice.append(
                "items",
                {
                    "item_code": spec["item_code"],
                    "item_name": item_name,
                    "qty": 1,
                    "rate": rate,
                },
            )

        if grand_total <= 0:
            frappe.throw(
                _("Enter at least one non-zero maintenance, water, or penalty amount before generating transactions.")
            )

        invoice.set_missing_values()
        invoice.insert(ignore_permissions=True)
        invoice.submit()
        row.db_set("sales_invoice", invoice.name)
        frappe.msgprint(
            _("Sales invoice created successfully: {0}").format(invoice.name), alert=True, indicator="green"
        )

        payment_entry = get_payment_entry(dt="Sales Invoice", dn=invoice.name)
        payment_entry.posting_date = row.date
        payment_entry.paid_from = get_account_paid_from()
        payment_entry.paid_amount = grand_total
        payment_entry.reference_no = invoice.name
        payment_entry.reference_date = invoice.posting_date
        payment_entry.set_missing_values()
        payment_entry.set_exchange_rate()
        payment_entry.flags.ignore_validate = True
        payment_entry.insert(ignore_permissions=True, ignore_mandatory=True)

        row.db_set("payment_entry", payment_entry.name)
        frappe.msgprint(
            _("Payment entry created successfully: {0}").format(payment_entry.name), alert=True, indicator="green"
        )
    except Exception as e:
        frappe.log_error(f"Error generating maintenance transactions: {str(e)}")
        frappe.throw(f"Error generating maintenance transactions: {str(e)}")


def get_account_paid_from():
    # get the account with number 123103
    return frappe.db.get_value("Account", {"account_number": "123103"}, "name")


def update_revenue_share_amount():
    # Daily scheduled job to update the revenue share amount if today = revenue share date
    today = getdate()

    rent_details = frappe.db.sql("""
        SELECT 
            urd.name,
            urd.parent,
            urd.rent_date,
            urd.revenue_share_date,
            urd.monthly_rent_amount,
            urd.revenue_share_amount
        FROM `tabUnit Rent Detail` urd
        INNER JOIN `tabUnit` u ON u.name = urd.parent
        WHERE urd.revenue_share_date = %s
        AND (urd.revenue_share_sales_invoice IS NULL OR urd.revenue_share_sales_invoice = '')
        AND (urd.revenue_share_payment_entry IS NULL OR urd.revenue_share_payment_entry = '')
        AND u.brand_name = 'تاون تيم'
        AND u.is_revenue_share = 1
        AND u.unit_status = 'Rent'
    """, (today,), as_dict=True)
    
    if not rent_details:
        return
    
    updated_count = 0
    
    for detail in rent_details:
        try:
            # Get the parent Unit document
            unit = frappe.get_doc("Unit", detail.parent)
            
            # Calculate revenue share amount using get_townteam_net_amount
            from_date = getdate(detail.rent_date)
            to_date = getdate(detail.revenue_share_date)
            
            townteam_amount = get_townteam_net_amount(from_date, to_date)
            revenue_share_amount = townteam_amount * (flt(unit.revenue_percent) / 100) if flt(unit.revenue_percent) > 0 else 0
            
            # Calculate required amount
            monthly_rent_amount = flt(detail.monthly_rent_amount) or 0
            required_amount = 0
            if revenue_share_amount > monthly_rent_amount:
                required_amount = revenue_share_amount - monthly_rent_amount
            
            # Update the Unit Rent Detail row
            frappe.db.set_value("Unit Rent Detail", detail.name, {
                "revenue_share_amount": revenue_share_amount,
                "required_amount": required_amount
            })
            
            updated_count += 1
            
        except Exception as e:
            frappe.log_error(
                f"Error updating revenue share amount for Unit Rent Detail {detail.name}: {str(e)}",
                "update_revenue_share_amount"
            )
            continue
    
    if updated_count > 0:
        frappe.log_error(
            f"Updated {updated_count} revenue share amount(s) for date: {today}",
            "update_revenue_share_amount"
        )