frappe.ui.form.on('Sales Invoice', {
    onload_post_render: function (frm) {
        frm.ignore_doctypes_on_cancel_all = ignore_doctypes_on_cancel_all = [
            "POS Invoice",
            "Timesheet",
            "POS Invoice Merge Log",
            "POS Closing Entry",
            "Journal Entry",
            "Payment Entry",
            "Repost Payment Ledger",
            "Repost Accounting Ledger",
            "Unreconcile Payment",
            "Unreconcile Payment Entries",
            "Serial and Batch Bundle",
            "Bank Transaction",
            "unit",
            "Unit Rent Detail"
        ];
    }
});
