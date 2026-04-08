// Copyright (c) 2026, Al-Salem Holding and contributors
// For license information, please see license.txt

frappe.query_reports["Units Report"] = {
	filters: [
		{
			fieldname: "company",
			label: __("الشركة"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "project_name",
			label: __("المشروع"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "cost_center",
			label: __("مركز التكلفة"),
			fieldtype: "Link",
			options: "Cost Center",
			get_query: function () {
				return {
					filters: {
						is_group: 0,
					},
				};
			},
		},
		{
			fieldname: "unit",
			label: __("الوحدة"),
			fieldtype: "Link",
			options: "unit",
			get_query: function () {
				const f = {};
				const company = frappe.query_report.get_filter_value("company");
				const project = frappe.query_report.get_filter_value("project_name");
				if (company) {
					f.company = company;
				}
				if (project) {
					f.project_name = project;
				}
				return { filters: f };
			},
		},
		{
			fieldname: "unit_status",
			label: __("حالة الوحدة"),
			fieldtype: "Select",
			options: ["", "Sold", "Rent", "Block", "Available", "Reserved"].join("\n"),
		},
		{
			fieldname: "unit_type",
			label: __("نوع الوحدة"),
			fieldtype: "Select",
			options: ["", "Residential", "Commercial"].join("\n"),
		},
		{
			fieldname: "customer_link",
			label: __("العميل"),
			fieldtype: "Link",
			options: "Customer",
		},
	],
};
