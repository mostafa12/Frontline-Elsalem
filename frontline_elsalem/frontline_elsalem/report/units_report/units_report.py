# Copyright (c) 2026, Al-Salem Holding and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = get_columns()
	conditions, values = get_conditions(filters)
	data = frappe.db.sql(
		f"""
		SELECT
			c.customer_name,
			unit.unit_number,
			unit.unit_type,
			unit.unit_status,
			unit.cost_center,
			unit.unit_price,
			unit.maintenance_price,
			unit.total_installments,
			unit.total_paid,
			unit.total_remaining,
			ROUND(
				(unit.total_paid / NULLIF(unit.total_installments, 0)) * 100,
				2
			) AS payment_ratio
		FROM
			`tabunit` unit
		LEFT JOIN
			`tabCustomer` c ON c.name = unit.customer_link
		WHERE
			{conditions}
		ORDER BY
			unit.unit_number ASC
		""",
		tuple(values),
		as_list=True,
	)
	return columns, data


def get_conditions(filters):
	filters = filters or {}
	conditions = ["unit.docstatus != 2"]
	values = []

	if filters.get("company"):
		conditions.append("unit.company = %s")
		values.append(filters["company"])

	if filters.get("project_name"):
		conditions.append("unit.project_name = %s")
		values.append(filters["project_name"])

	if filters.get("cost_center"):
		conditions.append("unit.cost_center = %s")
		values.append(filters["cost_center"])

	if filters.get("unit"):
		conditions.append("unit.name = %s")
		values.append(filters["unit"])

	if filters.get("unit_status"):
		conditions.append("unit.unit_status = %s")
		values.append(filters["unit_status"])

	if filters.get("unit_type"):
		conditions.append("unit.unit_type = %s")
		values.append(filters["unit_type"])

	if filters.get("customer_link"):
		conditions.append("unit.customer_link = %s")
		values.append(filters["customer_link"])

	return " AND ".join(conditions), values


def get_columns():
	return [
		"اسم العميل:Data:180",
		"رقم الوحدة:Data:120",
		"نوع الوحدة:Data:120",
		"حالة الوحدة:Data:120",
		"مركز التكلفة:Link/Cost Center:140",
		"قيمة الوحدة:Currency:130",
		"قيمة الصيانة:Currency:130",
		"اجمالي الاقساط:Currency:130",
		"المسدد:Currency:130",
		"المتبقي:Currency:130",
		"نسبة السداد:Percent:120",
	]
