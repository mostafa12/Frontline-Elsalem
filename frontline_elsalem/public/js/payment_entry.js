frappe.ui.form.on('Payment Entry', {
    onload_post_render: function(frm) {
        frm.ignore_doctypes_on_cancel_all = [
			"Sales Invoice",
			"Purchase Invoice",
			"Journal Entry",
			"Repost Payment Ledger",
			"Repost Accounting Ledger",
			"Unreconcile Payment",
			"Unreconcile Payment Entries",
			"Bank Transaction",
            "unit",
            "Unit Rent Detail"
		];
    }
});