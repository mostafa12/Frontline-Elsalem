from frappe import _

def get_data():
    return {
        "fieldname": "unit",
        "non_standard_fieldnames": {
            "Payment Entry": "unit",
            # "Journal Entry": "unit",
            # "Sales Order": "unit",
        },
        "transactions": [
            {"label": _("Payment Entry"), "items": ["Payment Entry"]},
            # {"label": _("Journal Entry"), "items": ["Journal Entry"]},
            # {"label": _("Sales Order"), "items": ["Sales Order"]},
        ],
    }

	
