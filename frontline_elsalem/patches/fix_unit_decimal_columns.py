# Copyright (c) 2025, Al-Salem Holding and contributors
# License: MIT. See LICENSE
"""
Normalize decimal/currency columns in tabunit so ALTER to decimal(21,9) NOT NULL default 0
succeeds during sync_customizations. Fixes: Data truncated for column 'total_installments' at row N.
"""
import frappe


def execute():
	if not frappe.db.table_exists("unit"):
		return

	# Columns that customization sync wants as decimal(21,9) not null default 0
	decimal_columns = [
		"custom_rent_amount",
		"current_amount",
		"unit_area",
		"total_remaining",
		"custom_advance_payment",
		"custom_maintenance_amount",
		"custom_total_paid_recent",
		"monthly_rent_amount",
		"revenue_percent",
		"custom_collection_rate",
		"custom_insurance",
		"custom_yearly_increase",
		"unit_price",
		"custom_term_contract",
		"maintenance_price",
		"total_paid",
		"rent_contract_increase_percent",
		"total_installments",
	]

	existing_columns = [c.get("Field") for c in frappe.db.sql("SHOW COLUMNS FROM `tabunit`", as_dict=True)]

	for col in decimal_columns:
		if col not in existing_columns:
			continue
		# Set NULL to 0 so MODIFY to decimal(21,9) not null default 0 won't truncate
		frappe.db.sql("UPDATE `tabunit` SET `{0}` = 0 WHERE `{0}` IS NULL".format(col))
	frappe.db.commit()
