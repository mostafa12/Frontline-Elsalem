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
            increase_percent = flt(self.rent_contract_increase_percent or 0) / 100 if flt(self.rent_contract_increase_percent or 0) > 0 else 0
            
            for i in range(self.rent_contract_duration):
                # Calculate which year we're in (0-indexed)
                year = i // 12
                # Calculate rent with yearly increase
                current_rent = base_rent * ((1 + increase_percent) ** year)
                
                # Calculate month start date
                month_start = add_to_date(self.rent_contract_start_date, months=i)
                # Calculate month end date (start of next month minus 1 day)
                next_month_start = add_to_date(self.rent_contract_start_date, months=i+1)
                month_end = getdate(next_month_start) - relativedelta(days=1)

                revenue_share_amount = 0
                if self.brand_name == 'تاون تيم':
                    townteam_amount = get_townteam_net_amount(month_start, month_end)
                    revenue_share_amount = townteam_amount * (flt(self.revenue_percent) / 100) if flt(self.revenue_percent) > 0 else 0

                required_amount = 0
                if revenue_share_amount > current_rent:
                    required_amount = revenue_share_amount - current_rent

                self.append('rent_contract_details', {
                    'payment_type': 'إيجار شهرى',
                    'monthly_rent_amount': current_rent,
                    'revenue_share_amount': revenue_share_amount if getdate() >= month_end else 0,
                    'rent_date': month_start, # Month start date
                    'revenue_share_date': month_end, # Month end date,
                    'required_amount': required_amount
                })


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

    @frappe.whitelist()
    def create_payment_entries_for_rent(self):
        """Create payment entries for rent contract details with required_amount > 0"""
        if self.unit_status != 'Rent':
            frappe.throw("Unit status must be 'Rent' to create payment entries")
        
        if not self.company:
            frappe.throw("Please set Company first")
        
        if not self.customer_link:
            frappe.throw("Please set Customer first")
        
        # Get rows that need payment entries
        rows_to_process = [
            row for row in self.rent_contract_details 
            if flt(row.required_amount) > 0 and not row.payment_entry
        ]
        
        if not rows_to_process:
            frappe.msgprint("No rows found with required amount > 0 and no payment entry")
            return
        
        created_entries = []
        
        for idx, row in enumerate(rows_to_process, 1):
            try:
                # Get party account
                party_account = get_party_account("Customer", self.customer_link, self.company)
                party_account_currency = get_account_currency(party_account)
                
                # Get default bank/cash account from mode of payment if available
                bank_account = None
                if self.mode_of_payment:
                    bank_account = self.get_default_account(self.mode_of_payment, self.company)
                
                if not bank_account:
                    # Get default company bank account
                    bank_account = frappe.db.get_value(
                        "Account",
                        {"account_type": "Bank", "is_group": 0, "company": self.company},
                        "name"
                    )
                
                if not bank_account:
                    frappe.throw(f"Please set up a bank account for company {self.company}")
                
                bank_account_currency = get_account_currency(bank_account)
                
                # Check if bank account type is "Bank" (requires reference_no and reference_date)
                bank_account_type = frappe.db.get_value("Account", bank_account, "account_type")
                reference_date = nowdate()
                
                # Create payment entry
                pe = frappe.new_doc("Payment Entry")
                pe.payment_type = "Receive"  # Receiving rent from customer
                pe.company = self.company
                pe.cost_center = self.cost_center
                pe.posting_date = nowdate()
                pe.reference_date = reference_date
                pe.party_type = "Customer"
                pe.party = self.customer_link
                pe.paid_from = party_account
                pe.paid_to = bank_account
                pe.paid_from_account_currency = party_account_currency
                pe.paid_to_account_currency = bank_account_currency
                pe.paid_amount = flt(row.required_amount)
                pe.received_amount = flt(row.required_amount)
                pe.mode_of_payment = self.mode_of_payment
                pe.remarks = f"Rent payment for Unit {self.unit_number} - {row.payment_type or 'Monthly'}"
                
                if bank_account_type == "Bank":
                    payment_type_short = (row.payment_type or 'MONTHLY')[:4].upper()
                    pe.reference_no = f"RENT-{self.unit_number}-{payment_type_short}-{idx:03d}"
                
                pe.setup_party_account_field()
                
                # Set missing values and validate
                pe.set_missing_values()
                pe.set_exchange_rate()
                
                # Save payment entry
                pe.insert()
                # pe.submit()
                
                # Update row with payment entry reference
                row.db_set("payment_entry", pe.name)
                row.db_set("paid_amount", flt(row.required_amount))
                created_entries.append(pe.name)
                
            except Exception as e:
                frappe.log_error(f"Error creating payment entry for row: {str(e)}")
                frappe.throw(f"Error creating payment entry: {str(e)}")
        
        # Save the unit document with updated payment entry references
        self.save()
        
        if created_entries:
            frappe.msgprint(f"Created {len(created_entries)} payment entry/entries: {', '.join(created_entries)}")
        
        return created_entries


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
def generate_rent_transactions(company, brand_name, rowname, mode_of_payment=None):
    # First create a sales invoice for the rent amount and ايجار محل تجارى item
    try:
        row = frappe.get_doc("Unit Rent Detail", rowname)
        invoice = frappe.new_doc("Sales Invoice")
        invoice.customer = brand_name
        invoice.company = company
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