# Copyright (c) 2023, frontline solutions and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = get_columns(),[]
	withoutMaintenance = getWithoutMaintenance(filters)
	withMaintenance = get_maintenance_data(filters)
	data.append({'payment_method': 'القيمة الاجمالية للوحدة','parent_account':None,'indent':0})
	data.extend(withoutMaintenance)
	data.append({'payment_method': 'القيمة الاجماليه للصيانة','parent_account':None,'indent':0})
	data.extend(withMaintenance)
	data[0].update({'transfered': 'القيمة المتبقية للوحدة'})
	data[len(withoutMaintenance)+1].update({'transfered': 'القيمة المتبقية للصيانة'})
	data[0].update({'bank_taken_value': 0})
	data[len(withoutMaintenance)+1].update({'bank_taken_value': 0})
	total_paid_amount,total_rest_amount,total_bank_taken_value = get_totals(withoutMaintenance)
	data[0].update({'paid_amount':total_paid_amount})
	data[0].update({'rest':total_rest_amount})
	data[0].update({'bank_taken_value': total_bank_taken_value})
	total_paid_amount,total_rest_amount,total_bank_taken_value = get_totals(withMaintenance)
	data[len(withoutMaintenance)+1].update({'paid_amount':total_paid_amount})
	data[len(withoutMaintenance)+1].update({'rest':total_rest_amount})
	data[len(withoutMaintenance)+1].update({'bank_taken_value':total_bank_taken_value})

	sales_order_items_list = getSalesOrderItems(filters)
	sales_person_name = get_sales_person(filters)
	report_summary = get_report_summary(sales_order_items_list,sales_person_name)
	return columns , data,'',[],report_summary


def get_totals(list_of_data):
	total_paid_amount = 0
	total_rest_amount = 0
	total_bank_taken_value = 0
	for entry in list_of_data:
		if entry:
			total_paid_amount += entry.paid_amount
			total_rest_amount += entry.rest
			total_bank_taken_value += entry.bank_taken_value
	return total_paid_amount , total_rest_amount , total_bank_taken_value


def get_report_summary(sales_order_items_list,sales_person_name):
	return [
		{
			"value" : sales_order_items_list[0].get('customer_name'),
			"label": ("اسم العميل"),
			"datatype" : "Data"
		},
		{
			"value" : sales_order_items_list[0].get('cost_center'),
			"label" : ("رقم الوحدة"),
			"datatype" : "Data",
		},
		{
			"value" : sales_order_items_list[0].get('unit_area'),
			"label" : ("مساحة الوحدة"),
			"datatype" : "Data",
		},
		{
			"value": sales_order_items_list[0].get('amount'),
			"label": (sales_order_items_list[0].get('item_code')),
			"datatype": "Currency",
		},
		{
			"value": sales_order_items_list[1].get('amount'),
			"label": (sales_order_items_list[1].get('item_code')),
			"datatype": "Currency",
		},
		{
			"value": sales_order_items_list[0].get('amount') + sales_order_items_list[1].get('amount'),
			"label": ("المجموع الكلي"),
			"datatype": "Currency",
		},
		{
			"value" : sales_order_items_list[0].get('payment_system'),
			"label" : ("نظام السداد"),
			"datatype" : "Data"
		},
		{
			"value" : sales_order_items_list[0].get('transaction_date'),
			"label" : ("تاريخ التعاقد"),
			"datatype" : "Date"
		},
		{
			"value" : sales_order_items_list[1].get('delivery_date'),
			"label" : ("تاريخ الاستلام التعاقدي"),
			"datatype" : "Date"
		},
		{
			"value" : sales_order_items_list[0].get('investment_deadline'),
			"label" : ("ميعاد الاستثمار"),
			"datatype" : "Date"
		},
		{
			"value" : sales_person_name,
			"label": ("مسئول البيع"),
			"datatype" : "Data"
		},

	]



def get_columns():
	return [
		{
		"fieldname": "payment_method",
		"label":("نوع الدفعه"),
		"fieldtype": "Data",
		},
		{
		"fieldname": "transaction_date",
		"label":("تاريخ التعاقد"),
		"fieldtype": "Date",
		},
		{
		"fieldname": "mode_of_payment",
		"label":("نوع السداد"),
		"fieldtype": "Link",
		"options":"Mode of Payment"
		},
		{
		"fieldname": "payment_entry_name",
		"label":("رقم الحركة"),
		"fieldtype": "Data"
		},
		{
		"fieldname": "paid_amount",
		"label":("قيمة الشيك"),
		"fieldtype": "Currency",
		},
		{
		"fieldname": "reference_no",
		"label":("رقم الشيك"),
		"fieldtype": "Link",
		"options": "Customer",
		},
		{
		"fieldname": "reference_date",
		"label":("تاريخ استحقاق الشيك"),
		"fieldtype": "Date",
		},
		{
		"fieldname": "bank_name",
		"label":("البنك المسحوب عليه"),
		"fieldtype": "data",
		},
		{
		"fieldname": "branch_name",
		"label":("الفرع"),
		"fieldtype": "data",
		},
		{
		"fieldname": "paid_to",
		"label":("paid_to"),
		"fieldtype": "data",
		},
		{
		"fieldname": "bank_taken_value",
		"label":("المحصل من الشيكات"),
		"fieldtype": "Currency",
		},
		{
		"fieldname": "transfered",
		"label":("transfered_to"),
		"fieldtype": "data",
		},
		{
		"fieldname": "rest",
		"label":("المتبقى على العميل"),
		"fieldtype": "Currency",
		},

		]



def getWithoutMaintenance(filters):
	data = None
	conditions = ''
	if filters.get('cost_center'):
		conditions += f"And pe.cost_center = '{filters.get('cost_center')}'"
	else:
		return []
	data = frappe.db.sql(f"""
	Select
		so.customer_name ,
		so.transaction_date ,
		pe.payment_method,
		pe.mode_of_payment,
		IFNULL(pe.name,'') as 'payment_entry_name',
		pe.paid_amount ,
		pe.reference_no ,
		pe.reference_date  ,
		pe.bank_name ,
		pe.branch_name ,
		pe.paid_to,
		pe.transfered,
		if(pe.transfered ,  pe.paid_amount , 0) as bank_taken_value,
		pe.paid_amount - if(pe.transfered ,  pe.paid_amount , 0) as rest,
		1 as indent,
		'القيمة الاجمالية للوحدة' as 'parent_account'
	from
		`tabPayment Entry` as pe
	inner join
		`tabSales Order` as so
	on
		pe.cost_center = so.cost_center

	where
		paid_to = '123221 - أوراق قبض عقود-البنك الاهلى المصرى - ASR' 
	And
		so.docstatus = 1
	And
		pe.docstatus = 1
	{conditions}
;
	""",as_dict=True)
	return data

def get_maintenance_data(filters):
	data = None
	conditions = ''
	if filters.get('cost_center'):
		conditions += f"And pe.cost_center = '{filters.get('cost_center')}'"
	else:
		return []
	data = frappe.db.sql(f"""
	Select
		so.customer_name ,
		so.transaction_date ,
		IFNULL(pe.name,'') as 'payment_entry_name',
		pe.payment_method,
		pe.mode_of_payment,
		pe.paid_amount ,
		pe.reference_no ,
		pe.reference_date  ,
		pe.bank_name ,
		pe.branch_name ,
		pe.paid_to,
		pe.transfered,
		if(pe.transfered ,  pe.paid_amount , 0) as bank_taken_value ,
		pe.paid_amount - if(pe.transfered ,  pe.paid_amount , 0) as rest,
		1 as indent,
		'القيمة الاجماليه للصيانة' as 'parent_account'
		
	from
    	`tabPayment Entry` as pe
	inner join
    	`tabSales Order` as so
	on
    	pe.cost_center = so.cost_center

	where
    	paid_to = '123222 - اوراق قبض صيانة-البنك الاهلى المصرى - ASR'
	And
		so.docstatus = 1
	And
		pe.docstatus = 1
	{conditions}
	;
	""",as_dict=True)
	return data



def getSalesOrderItems(filters):
	sales_order_items_list = []
	data = None
	if filters.get('cost_center'):
		data = frappe.db.sql(f"""
				Select
					so.name,
					so.customer,
					so.cost_center,
					so.unit_area,
					so.payment_system,
					so.transaction_date,
					soi.amount,
		       		soi.item_code,
					soi.delivery_date as items_dates
				from
					`tabSales Order` as so
				inner join
					`tabSales Order Item` as soi
				on
					so.name = soi.parent
				where
					so.cost_center = '{filters.get('cost_center')}'
				And
					so.docstatus = 1;

		""",as_dict=True)
		if len(data) == 2:
			for entry in data:
				sales_order_items_list.append({
					'item_code':entry.item_code,
					'amount':entry.amount,
					'customer_name':entry.customer,
					'cost_center':str(entry.cost_center).split(' - ')[0],
					'unit_area':entry.unit_area,
					'payment_system':entry.payment_system,
					'transaction_date':entry.transaction_date
					})
			sales_order_items_list[0].update({'investment_deadline':data[1].items_dates})
			sales_order_items_list[1].update({'delivery_date':data[0].items_dates})
		else:
			frappe.throw("this cost center has no sales order items or more than two")
	return sales_order_items_list


def get_sales_person(filters):
	sales_person_name = None
	data = frappe.db.sql(f"""
		select 
			`tabSales Team`.sales_person
		from 
			`tabSales Order`,`tabSales Team` 
		where 
			`tabSales Order`.name = `tabSales Team`.parent 
		And 
			`tabSales Order`.cost_center = '{filters.get('cost_center')}'
		And
			`tabSales Order`.docstatus = 1;
		""",as_dict=True)
	if len(data) > 0 :
		sales_person_name = data[0].sales_person
	return sales_person_name