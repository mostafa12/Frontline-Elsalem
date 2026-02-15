frappe.ui.form.on('Payment Entry', {
	setup: function(frm) {
		frm.set_query("unit", function(doc, cdt, cdn) {
			return {
				filters: {
					unit_type: "Residential"
				}
			}
		})
		frm.set_query("unit_payment_type", function(doc, cdt, cdn) {
			return {
				query: "frontline_elsalem.overrides.payment_entry.get_payment_type",
				filters: {
					unit: doc.unit
				}
			}
		})
	},

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
    },

	unit: function(frm) {
		frm.events.get_unit_details(frm);
	},

	unit_payment_type: function(frm) {
		frm.events.get_unit_details(frm);
	},

	get_unit_details: function(frm) {
		if (frm.doc.unit) {
			// get customer name from unit
			frappe.db.get_doc("unit", frm.doc.unit)
			.then(doc => {
				frm.set_value("party", doc.customer_link);
				frm.set_value("party_type", "Customer");
				$.each(doc.contract_details, (index, row) => {
					if (frm.doc.unit_payment_type == row.paymenttype) {
						let remaining_amount = row.installments - row.paid;
						frm.set_value("paid_amount", remaining_amount);
						return;
					}
				});
			});
		}
	}
});