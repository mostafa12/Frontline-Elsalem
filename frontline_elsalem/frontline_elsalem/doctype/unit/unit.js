// =======================
// UNIT FORM SCRIPT (Enhanced & Fixed)
// =======================

const CUSTOMER_TO_BRAND = {
	'شركة إية يو إف إيجيبت لصناعة وتوزيع المكسرات ( أبو عوف )': 'Abu Auf',
	'أساور': 'Asawer',
	'Pieno E Neno': 'Pino',
	'وديدة': 'Wadeda',
	'بوخارست بلاك': 'Borest',
	'شركة نهضة مصر للسنيما - Renaissance Cinemas': 'Cinema',
	'Dream 2000': 'Dream 2000',
	'ديفاكتو': 'Defacto',
	'تاي شوب': 'TieShop',
	'New Active': 'Activ',
	'تاون تیم': 'Town Team',
	'تاون تيم': 'Town Team'  // alternate spelling (Arabic ي vs Persian ی)
};

frappe.ui.form.on('unit', {
	refresh: function (frm) {
		calculate_totals(frm);

		if (frm.doc.contract_details) {
			frm.doc.contract_details.forEach(function (row) {
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

			$btn_container.find('#download_contract_details').on('click', function () {
				download_contract_details(frm);
			});

			$btn_container.find('#upload_contract_details').on('click', function () {
				upload_contract_details(frm);
			});
		}

		if (frm.is_new()) {
			if (!frm.doc.r_sh_year) {
				const year = frappe.defaults.get_user_default('fiscal_year') || frappe.datetime.now_date().substring(0, 4);
				frm.set_value('r_sh_year', year);
			}
		}
	},

	unit_status: function (frm) {
		toggle_fields_by_unit_type(frm);
	},

	unit_type: function (frm) {
		toggle_fields_by_unit_type(frm);
	},

	contract_details_add: function (frm) {
		calculate_totals(frm);
	},

	contract_details_remove: function (frm) {
		calculate_totals(frm);
	},

	rent_contract_start_date: function (frm) {
		calculate_rent_contract_end_date(frm);
	},

	rent_contract_duration: function (frm) {
		calculate_rent_contract_end_date(frm);
	},

	generate_monthly_rent_details: function (frm) {
		generate_rent_details(frm);
	},

	r_sh_year: function (frm) {
		frm.events.set_r_sh_start_end_dates(frm);
	},

	r_sh_month: function (frm) {
		if (!frm.doc.r_sh_year) {
			frappe.throw(__('Year is required'));
		}

		frm.events.set_r_sh_start_end_dates(frm);
	},

	set_r_sh_start_end_dates: function (frm) {
		if (frm.doc.r_sh_month && frm.doc.r_sh_year) {
			var month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
			var month_num = month_names.indexOf(frm.doc.r_sh_month) + 1;
			if (month_num === 0) {
				frappe.throw(__('Invalid month'));
			}

			var year = frm.doc.r_sh_year;
			if (year.length > 4) {
				// Fiscal Year is "2025-2026" -> use end year (2026) when user selects that year
				year = year.split('-')[1];
			}

			var pad = function (n) { return String(n).padStart(2, '0'); };
			var brand = (frm.doc.brand_name && CUSTOMER_TO_BRAND[frm.doc.brand_name]) ? CUSTOMER_TO_BRAND[frm.doc.brand_name] : (frm.doc.brand_name || '');
			var is_al_salem_4_brand = ['Asawer', 'Pino', 'Wadeda', 'Borest'].includes(brand);

			var r_sh_start_date, r_sh_end_date;
			if (is_al_salem_4_brand) {
				// AlSalem4Brand: 1st at 05:00 AM to next month's 1st at 04:59
				r_sh_start_date = year + '-' + pad(month_num) + '-01 05:00:00';
				var next_month_first = new Date(parseInt(year, 10), month_num, 1);
				r_sh_end_date = next_month_first.getFullYear() + '-' + pad(next_month_first.getMonth() + 1) + '-01 04:59:59';
			} else {
				r_sh_start_date = year + '-' + pad(month_num) + '-01 00:00:00';
				var last_day = new Date(parseInt(year, 10), month_num, 0);
				r_sh_end_date = year + '-' + pad(month_num) + '-' + pad(last_day.getDate()) + ' 23:59:59';
			}

			frm.set_value('r_sh_start_date', r_sh_start_date);
			frm.set_value('r_sh_end_date', r_sh_end_date);
		} else {
			frm.set_value('r_sh_start_date', '');
			frm.set_value('r_sh_end_date', '');
		}
	},

	calculate_reveue_share: function (frm) {
		if (frm.doc.r_sh_month && frm.doc.r_sh_year) {
			frm.events.set_r_sh_start_end_dates(frm);
		}

		if (!frm.doc.r_sh_start_date || !frm.doc.r_sh_end_date) {
			frappe.throw(__('Start and End Date are required'));
		}

		let brand = '';
		if (frm.doc.brand_name) {
			const brand_key = String(frm.doc.brand_name);
			if (CUSTOMER_TO_BRAND.hasOwnProperty(brand_key)) {
				brand = CUSTOMER_TO_BRAND[brand_key];
			} else {
				brand = `'${brand_key}'`;
			}
		}

		if (brand && frm.doc.r_sh_start_date && frm.doc.r_sh_end_date) {
			frappe.call({
				method: 'frontline_elsalem.frontline_elsalem.doctype.unit.unit.get_revenue_share_amount',
				args: {
					brand: brand,
					from_date: frm.doc.r_sh_start_date,
					to_date: frm.doc.r_sh_end_date
				},
				freeze: true,
				freeze_message: 'Calculating revenue share...',
				callback: function (r) {
					if (r.message) {
						let revenue_share_amount = flt(r.message);
						let revenue_share_percent = frm.doc.revenue_percent || 0;
						frm.set_value({
							total_revenues: revenue_share_amount,
							caluclated_revenue_share_amount: revenue_share_amount * (revenue_share_percent / 100)
						}).then(() => {
							frm.save();
						});
					} else {
						frm.set_value({
							total_revenues: 0,
							caluclated_revenue_share_amount: 0
						}).then(() => {
							frm.save();
						});
					}
				}
			});
		} else {
			frappe.throw(__('Brand Name, Start Date and End Date are required'));
		}
	},

	confirm_reveue_share: function (frm) {
		if (flt(frm.doc.caluclated_revenue_share_amount, 2) == flt(frm.doc.provided_revenue_share, 2)
			|| flt(frm.doc.caluclated_revenue_share_amount) == flt(frm.doc.provided_revenue_share)) {
			frappe.confirm('Are you sure you want to confirm the revenue share?', function () {
				var start_d = (frm.doc.r_sh_start_date || '').toString().substring(0, 10);
				var end_d = (frm.doc.r_sh_end_date || '').toString().substring(0, 10);
				$.each(frm.doc.rent_contract_details, function (index, row) {
					var rent_d = (row.rent_date || '').toString().substring(0, 10);
					if (rent_d && start_d && end_d && rent_d >= start_d && rent_d < end_d) {
						if (row.revenue_share_sales_invoice) {
							frappe.throw(__('Revenue Share Sales Invoice already exists for this rent date'));
						} else {
							frappe.model.set_value(row.doctype, row.name, 'revenue_share_amount', frm.doc.caluclated_revenue_share_amount);

							// check if not exists in revenue_share_details table, create a new one and if exists, update the existing one
							let month_label = frm.doc.r_sh_month;
							let start_date = (frm.doc.r_sh_start_date || '').toString().substring(0, 10);
							let end_date = (frm.doc.r_sh_end_date || '').toString().substring(0, 10);

							if (start_date && !month_label) {
								try {
									let start_obj = frappe.datetime.str_to_obj(start_date);
									month_label = start_obj.toLocaleString('default', {
										month: 'long',
										year: 'numeric'
									});
								} catch (e) {
									month_label = start_date;
								}
							}

							let existing_detail = (frm.doc.revenue_share_details || []).find(function (d) {
								let d_start = (d.start_date || '').toString().substring(0, 10);
								let d_end = (d.end_date || '').toString().substring(0, 10);
								return d_start === start_date && d_end === end_date;
							});

							if (existing_detail) {
								frappe.model.set_value(existing_detail.doctype, existing_detail.name, 'month', month_label);
								frappe.model.set_value(existing_detail.doctype, existing_detail.name, 'total_revenues', frm.doc.total_revenues);
								frappe.model.set_value(existing_detail.doctype, existing_detail.name, 'final_revenue_share_amount', frm.doc.caluclated_revenue_share_amount);
							} else {
								let child = frm.add_child('revenue_share_details');
								frappe.model.set_value(child.doctype, child.name, 'month', month_label);
								frappe.model.set_value(child.doctype, child.name, 'start_date', frm.doc.r_sh_start_date);
								frappe.model.set_value(child.doctype, child.name, 'end_date', frm.doc.r_sh_end_date);
								frappe.model.set_value(child.doctype, child.name, 'total_revenues', frm.doc.total_revenues);
								frappe.model.set_value(child.doctype, child.name, 'final_revenue_share_amount', frm.doc.caluclated_revenue_share_amount);
							}

							frm.refresh_field('revenue_share_details');
						}
					}
				});
				frm.save();
			});
		} else {
			frappe.throw(__('Calculated Revenue Share Amount should equal Provided Revenue Share Amount'));
		}

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
		callback: function (r) {
			frm.refresh_field("rent_contract_details");
			frm.dirty();
		}
	});
};


frappe.ui.form.on('Unit Rent Detail', {
	revenue_share_amount: function (frm, cdt, cdn) {
		calculate_required_amount(frm, cdt, cdn);
	},
	monthly_rent_amount: function (frm, cdt, cdn) {
		calculate_required_amount(frm, cdt, cdn);
	},

	payment_type: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.payment_type) {
			$.each(locals[cdt], function (index, d) {
				if (!d.payment_type) {
					frappe.model.set_value(d.doctype, d.name, 'payment_type', row.payment_type);
				}
			});
		}
	},

	caculate_revenue_share_amount: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		frappe.call({
			method: 'frontline_elsalem.frontline_elsalem.doctype.unit.unit.get_townteam_net_amount',
			args: {
				from_date: row.rent_date,
				to_date: row.revenue_share_date
			},
			callback: function (r) {
				if (r.message) {
					let townteam_amount = flt(r.message);
					let revenue_share_amount = townteam_amount * (frm.doc.revenue_percent / 100);
					frappe.model.set_value(cdt, cdn, 'revenue_share_amount', revenue_share_amount);
				}
			}
		});
	},

	generate_rent_transactions: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (frm.is_dirty()) {
			frappe.throw(__('You have unsaved changes. Please save the form first'));
		};

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
			callback: function () {
				frm.reload_doc();
			}
		});
	},

	generate_revenue_share_transactions: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (frm.is_dirty()) {
			frappe.throw(__('You have unsaved changes. Please save the form first'));
		};

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
			callback: function () {
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
	installments: function (frm, cdt, cdn) {
		calculate_remaining_only(frm, cdt, cdn);
		calculate_totals(frm);
	},
	paid: function (frm, cdt, cdn) {
		calculate_remaining_only(frm, cdt, cdn);
		calculate_totals(frm);
	},
	part_paid: function (frm, cdt, cdn) {
		calculate_remaining_only(frm, cdt, cdn);
		calculate_totals(frm);
	},
	bounced_checks: function (frm, cdt, cdn) {
		check_remaining_vs_bounced(frm, cdt, cdn, false);
	},

	checkstatus1: function (frm, cdt, cdn) {
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
			], function (values) {
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
			], function (values) {
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


frappe.ui.form.on('Unit Maintenance Detail', {
	maintenance_amount: function (frm, cdt, cdn) {
		calculate_total_maintenance_amount(frm, cdt, cdn);
	},
	water_amount: function (frm, cdt, cdn) {
		calculate_total_maintenance_amount(frm, cdt, cdn);
	},
	penalty_amount: function (frm, cdt, cdn) {
		calculate_total_maintenance_amount(frm, cdt, cdn);
	},

	generate_maintenance_transactions: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (frm.is_dirty()) {
			frappe.throw(__('You have unsaved changes. Please save the form first'));
		}

		frappe.call({
			method: 'frontline_elsalem.frontline_elsalem.doctype.unit.unit.generate_maintenance_transactions',
			args: {
				company: frm.doc.company,
				brand_name: frm.doc.brand_name,
				rowname: row.name,
				mode_of_payment: frm.doc.mode_of_payment
			},
			freeze: true,
			freeze_message: __('Generating maintenance transactions...'),
			callback: function () {
				frm.reload_doc();
			}
		});
	},
});

function calculate_total_maintenance_amount(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	let total_maintenance_amount = 0;
	total_maintenance_amount = flt(row.maintenance_amount) + flt(row.water_amount) + flt(row.penalty_amount);
	frappe.model.set_value(cdt, cdn, 'total', total_maintenance_amount);
}

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
		"paymenttype", "installments", "paid", "part_paid", "remaining",
		"bounced_checks", "checkstatus1", "paymentmethod", "bank", "branch",
		"checknumber", "duedate", "paymentdate"
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
	$input.on('change', function (e) {
		let file = e.target.files[0];
		let reader = new FileReader();

		reader.onload = function (event) {
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
		if (in_list(["Sold", "Reserved"], frm.doc.unit_status)) {
			frm.toggle_reqd('customer_link', true);
		}else{
			frm.toggle_reqd('customer_link', false);
		}

	} else if (frm.doc.unit_type === "Commercial") {
		frm.toggle_display('commercial_section_section', true);
		commercial_fields.forEach(field => frm.toggle_reqd(field, true));

		frm.toggle_display('features_section', false);
		residential_fields.forEach(field => frm.toggle_reqd(field, false));

		frm.toggle_display('customer_link', false);
		// frm.toggle_reqd('customer_link', false);

	} else {
		frappe.throw(__('Unit Type must be either "Residential" or "Commercial". Please select a valid option.'));
	}
}