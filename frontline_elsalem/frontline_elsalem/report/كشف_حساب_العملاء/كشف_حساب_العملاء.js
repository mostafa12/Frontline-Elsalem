// Copyright (c) 2023, frontline solutions and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["كشف حساب العملاء"] = {
  filters: [
    {
      fieldname: "cost_center",
      label: __("cost_center"),
      fieldtype: "Link",
      options: "Cost Center",
      reqd: 1,
    },
  ],
  formatter: function (value, row, column, data, default_formatter) {
    if (data && column.fieldname == "account") {
      value = data.account_name || value;

      column.link_onclick =
        "erpnext.financial_statements.open_general_ledger(" +
        JSON.stringify(data) +
        ")";
      column.is_tree = true;
    }

    value = default_formatter(value, row, column, data);

    if (!data.parent_account) {
      value = $(`<span>${value}</span>`);

      var $value = $(value).css("font-weight", "bold");

      value = $value.wrap("<p></p>").parent().html();
    }
    return value;
  },
};
