// =======================
// UNIT FORM SCRIPT (Enhanced & Fixed)
// =======================

frappe.ui.form.on('unit', {
	refresh: function(frm) {
		calculate_totals(frm);

		if (frm.doc.contract_details) {
			frm.doc.contract_details.forEach(function(row) {
				calculate_remaining_only(frm, row.doctype, row.name);
			});
		}

		toggle_fields_by_unit_type(frm);

		if (frm.fields_dict.contract_details && !frm.fields_dict.contract_details.wrapper.download_upload_added) {
			let $btn_container = $(`
				<div class="contract-details-buttons" style="margin-top: 10px;">
					<button class="btn btn-sm btn-primary" id="download_contract_details">
						<i class="fa fa-download"></i> Download
					</button>
					<button class="btn btn-sm btn-secondary" id="upload_contract_details" style="margin-left: 5px;">
						<i class="fa fa-upload"></i> Upload
					</button>
				</div>
			`);

			$(frm.fields_dict.contract_details.wrapper).append($btn_container);
			frm.fields_dict.contract_details.wrapper.download_upload_added = true;

			$btn_container.find('#download_contract_details').on('click', function() {
				download_contract_details(frm);
			});

			$btn_container.find('#upload_contract_details').on('click', function() {
				upload_contract_details(frm);
			});
		}

		// Add custom button for creating payment entries
		// if (frm.doc.unit_status == 'Rent' && frm.doc.rent_contract_details) {
		// 	frm.add_custom_button('Create Payment Entries', function() {
		// 		create_payment_entries_for_rent(frm);
		// 	});
		// }
	},

	unit_type: function(frm) {
		toggle_fields_by_unit_type(frm);
	},

	contract_details_add: function(frm) {
		calculate_totals(frm);
	},

	contract_details_remove: function(frm) {
		calculate_totals(frm);
	},

	rent_contract_start_date: function(frm) {
		calculate_rent_contract_end_date(frm);
	},

	rent_contract_duration: function(frm) {
		calculate_rent_contract_end_date(frm);
	},

	generate_monthly_rent_details: function(frm) {
		generate_rent_details(frm);
	}
});


function calculate_rent_contract_end_date(frm) {
	let start_date = frm.doc.rent_contract_start_date;
	let duration = frm.doc.rent_contract_duration;
	let end_date = frappe.datetime.add_months(start_date, duration);
	end_date = frappe.datetime.add_days(end_date, -1);
	frm.set_value('rent_contract_end_date', end_date);
}


function generate_rent_details(frm) {
	frappe.call({
		method: 'generate_rent_details',
		doc: frm.doc,
		freeze: true,
		freeze_message: 'Generating rent details...',
		callback: function(r) {
			frm.refresh_field("rent_contract_details");
			frm.dirty = true;
		}
	});
}

function create_payment_entries_for_rent(frm) {
	frappe.confirm(
		'This will create payment entries for all rows. Continue?',
		function() {
			frappe.call({
				method: 'create_payment_entries_for_rent',
				doc: frm.doc,
				freeze: true,
				freeze_message: 'Creating payment entries...',
				callback: function() {
					frm.reload_doc();
				}
			});
		}
	);
}


frappe.ui.form.on('Unit Rent Detail', {
	revenue_share_amount: function(frm, cdt, cdn) {
		calculate_required_amount(frm, cdt, cdn);
	},
	monthly_rent_amount: function(frm, cdt, cdn) {
		calculate_required_amount(frm, cdt, cdn);
	},

	payment_type: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.payment_type) {
			$.each(locals[cdt], function(index, d) {
				if (!d.payment_type) {
					frappe.model.set_value(d.doctype, d.name, 'payment_type', row.payment_type);
				}
			});
		}
	},

	caculate_revenue_share_amount: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		frappe.call({
			method: 'frontline_elsalem.frontline_elsalem.doctype.unit.unit.get_townteam_net_amount',
			args: {
				from_date: row.rent_date,
				to_date: row.revenue_share_date
			},
			callback: function(r) {
				if (r.message) {
					let townteam_amount = flt(r.message);
					let revenue_share_amount = townteam_amount * (frm.doc.revenue_percent / 100);
					frappe.model.set_value(cdt, cdn, 'revenue_share_amount', revenue_share_amount);
				}
			}
		});
	},

	generate_rent_transactions: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (frm.is_dirty()) {
			frappe.throw(__('You have unsaved changes. Please save the form first'));
		};

		if (frm.doc.docstatus != 1) {
			frappe.throw(__('You must submit the form first'));
		}

		frappe.call({
			method: 'frontline_elsalem.frontline_elsalem.doctype.unit.unit.generate_rent_transactions',
			args: {
				company: frm.doc.company,
				brand_name: frm.doc.brand_name,
				rowname: row.name,
				mode_of_payment: frm.doc.mode_of_payment
			},
			freeze: true,
			freeze_message: 'Generating rent transactions...',
			callback: function() {
				frm.reload_doc();
			}
		});
	},

	generate_revenue_share_transactions: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (frm.is_dirty()) {
			frappe.throw(__('You have unsaved changes. Please save the form first'));
		};

		if (frm.doc.docstatus != 1) {
			frappe.throw(__('You must submit the form first'));
		}

		frappe.call({
			method: 'frontline_elsalem.frontline_elsalem.doctype.unit.unit.generate_revenue_share_transactions',
			args: {
				company: frm.doc.company,
				brand_name: frm.doc.brand_name,
				rowname: row.name,
				mode_of_payment: frm.doc.mode_of_payment
			},
			freeze: true,
			freeze_message: 'Generating revenue share transactions...',
			callback: function() {
				frm.reload_doc();
			}
		});
	},
});


function calculate_required_amount(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	let revenue_share_amount = flt(row.revenue_share_amount) || 0;
	let monthly_rent_amount = flt(row.monthly_rent_amount) || 0;
	
	let required_amount = 0;
	if (revenue_share_amount > monthly_rent_amount) {
		required_amount = revenue_share_amount - monthly_rent_amount;
	}
	
	frappe.model.set_value(cdt, cdn, 'required_amount', required_amount);
}


// ==========================
// CONTRACT DETAILS CHILD TABLE EVENTS
// ==========================
frappe.ui.form.on('Contract details', {
	installments: function(frm, cdt, cdn) {
		calculate_remaining_only(frm, cdt, cdn);
		calculate_totals(frm);
	},
	paid: function(frm, cdt, cdn) {
		calculate_remaining_only(frm, cdt, cdn);
		calculate_totals(frm);
	},
	part_paid: function(frm, cdt, cdn) {
		calculate_remaining_only(frm, cdt, cdn);
		calculate_totals(frm);
	},
	bounced_checks: function(frm, cdt, cdn) {
		check_remaining_vs_bounced(frm, cdt, cdn, false);
	},

	checkstatus1: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		// محصل فورى
		if (row.checkstatus1 === 'محصل فورى') {
			frappe.model.set_value(cdt, cdn, 'paid', flt(row.installments));
			frappe.model.set_value(cdt, cdn, 'part_paid', 0);
			calculate_remaining_only(frm, cdt, cdn);
			calculate_totals(frm);
		}

		// محصل جزئى - الحل الصحيح
		else if (row.checkstatus1 === 'محصل جزئى') {
			let installments = flt(row.installments);
			let current_paid = flt(row.paid);
			let current_part_paid = flt(row.part_paid);
			let current_remaining = installments - current_paid;

			frappe.prompt([
				{
					label: 'قيمة المدفوع الجزئي',
					fieldname: 'partial_payment',
					fieldtype: 'Float',
					reqd: true,
					description: `القسط الكلي: ${installments} | المدفوع حالياً: ${current_paid} | المتبقي: ${current_remaining}`
				}
			], function(values) {
				let partial = flt(values.partial_payment);

				// التحقق من أن المبلغ الجزئي لا يتجاوز المتبقي
				if (partial > current_remaining) {
					frappe.msgprint({
						title: 'تنبيه',
						indicator: 'red',
						message: `المبلغ المدخل (${partial}) أكبر من المتبقي (${current_remaining}). سيتم تعديله تلقائياً.`
					});
					partial = current_remaining;
				}

				// ✅ الحساب الصحيح: إضافة المبلغ الجزئي للمدفوع الحالي
				let new_paid = current_paid + partial;

				// ✅ تحديث المحصل الجزئي المتراكم
				let new_part_paid = current_part_paid + partial;

				// ✅ حساب المتبقي الصحيح
				let new_remaining = installments - new_paid;
				if (new_remaining < 0) new_remaining = 0;

				// تحديث القيم
				frappe.model.set_value(cdt, cdn, 'paid', new_paid);
				frappe.model.set_value(cdt, cdn, 'part_paid', new_part_paid);
				frappe.model.set_value(cdt, cdn, 'remaining', new_remaining);

				// إعادة حساب الإجماليات
				calculate_totals(frm);

				frappe.msgprint({
					title: 'تم التحديث',
					indicator: 'green',
					message: `تم إضافة ${partial} ج<br>
							  المدفوع الجديد: ${new_paid} ج<br>
							  المتبقي الجديد: ${new_remaining} ج`
				});
			}, 'المدفوع الجزئي', 'حفظ');
		}

		// شيك مرتد
		else if (row.checkstatus1 === 'شيك مرتد') {
			frappe.prompt([
				{
					label: 'قيمة الشيك المرتد',
					fieldname: 'bounced_amount',
					fieldtype: 'Float',
					reqd: true
				}
			], function(values) {
				let current_paid = flt(row.paid);
				let bounced_amount = flt(values.bounced_amount);
				let new_paid = current_paid - bounced_amount;

				if (new_paid < 0) new_paid = 0;

				frappe.model.set_value(cdt, cdn, 'paid', new_paid);
				frappe.model.set_value(cdt, cdn, 'bounced_checks', bounced_amount);
				calculate_remaining_only(frm, cdt, cdn);
				calculate_totals(frm);
			}, 'قيمة الشيك المرتد', 'حفظ');
		}
	}
});

// ==========================
// DOWNLOAD / UPLOAD FUNCTIONS
// ==========================

function download_contract_details(frm) {
	let rows = frm.doc.contract_details || [];
	if (!rows.length) {
		frappe.msgprint("No rows found in Contract Details");
		return;
	}

	let headers = [
		"paymenttype","installments","paid","part_paid","remaining",
		"bounced_checks","checkstatus1","paymentmethod","bank","branch",
		"checknumber","duedate","paymentdate"
	];
	let csv = headers.join(",") + "\n";

	rows.forEach(r => {
		let row = headers.map(h => r[h] || "").join(",");
		csv += row + "\n";
	});

	let blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
	let link = document.createElement("a");
	link.href = URL.createObjectURL(blob);
	link.download = "contract_details.csv";
	link.click();
}

function upload_contract_details(frm) {
	let $input = $('<input type="file" accept=".csv">');
	$input.on('change', function(e) {
		let file = e.target.files[0];
		let reader = new FileReader();

		reader.onload = function(event) {
			let csv = event.target.result;
			let lines = csv.split("\n").filter(l => l.trim() !== "");
			let headers = lines[0].split(",");

			frm.clear_table("contract_details");

			for (let i = 1; i < lines.length; i++) {
				let values = lines[i].split(",");
				if (values.length !== headers.length) continue;

				let row = frm.add_child("contract_details");
				headers.forEach((h, idx) => {
					row[h.trim()] = values[idx] ? values[idx].trim() : "";
				});
			}

			frm.refresh_field("contract_details");
			calculate_totals(frm);
			frappe.msgprint("Contract Details uploaded successfully!");
		};

		reader.readAsText(file);
	});
	$input.click();
}

// ==========================
// HELPER FUNCTIONS
// ==========================

function calculate_remaining_only(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	let installments = flt(row.installments);
	let paid = flt(row.paid);

	// ✅ الحساب الصحيح: المتبقي = القسط - المدفوع فقط
	let remaining = installments - paid;
	if (remaining < 0) remaining = 0;

	frappe.model.set_value(cdt, cdn, 'remaining', remaining);

	if (frm.fields_dict.contract_details && frm.fields_dict.contract_details.grid) {
		frm.fields_dict.contract_details.grid.refresh();
	}

	setTimeout(() => {
		check_remaining_vs_bounced(frm, cdt, cdn, true);
	}, 100);
}

function check_remaining_vs_bounced(frm, cdt, cdn, skip_force_remaining = false) {
	let row = locals[cdt][cdn];
	let remaining = flt(row.remaining);
	let bounced_checks = flt(row.bounced_checks);

	if (remaining === 0 && bounced_checks !== 0) {
		frappe.model.set_value(cdt, cdn, 'bounced_checks', 0);
	} else if (bounced_checks === 0 && remaining !== 0 && !skip_force_remaining) {
		frappe.model.set_value(cdt, cdn, 'remaining', 0);
	}
}

function calculate_totals(frm) {
	let total_installments = 0;
	let total_paid = 0;
	let total_remaining = 0;

	(frm.doc.contract_details || []).forEach(row => {
		total_installments += flt(row.installments);
		total_paid += flt(row.paid);
		total_remaining += flt(row.remaining);
	});

	frm.set_value('total_installments', total_installments);
	frm.set_value('total_paid', total_paid);
	frm.set_value('total_remaining', total_remaining);
}

function toggle_fields_by_unit_type(frm) {
	const residential_fields = ['unit_area', 'room', 'bathroom', 'facing', 'unit_case', 'stage_number'];
	const commercial_fields = ['location_number', 'brand_name', 'unit_sqm', 'occupancy'];

	if (frm.doc.unit_type === "Residential") {
		frm.toggle_display('features_section', true);
		residential_fields.forEach(field => frm.toggle_reqd(field, true));

		frm.toggle_display('commercial_section_section', false);
		commercial_fields.forEach(field => frm.toggle_reqd(field, false));

		frm.toggle_display('customer_link', true);
		frm.toggle_reqd('customer_link', true);

	} else if (frm.doc.unit_type === "Commercial") {
		frm.toggle_display('commercial_section_section', true);
		commercial_fields.forEach(field => frm.toggle_reqd(field, true));

		frm.toggle_display('features_section', false);
		residential_fields.forEach(field => frm.toggle_reqd(field, false));

		frm.toggle_display('customer_link', false);
		frm.toggle_reqd('customer_link', false);

	} else {
		frappe.throw(__('Unit Type must be either "Residential" or "Commercial". Please select a valid option.'));
	}
}