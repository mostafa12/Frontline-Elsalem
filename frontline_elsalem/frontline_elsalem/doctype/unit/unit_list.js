// frappe.listview_settings['unit'] = {
// 	get_indicator: function (doc) {
// 		const status_colors = {
// 			'Sold': 'red',
// 			'Rent': 'green',
// 			'Block': 'orange',
// 			'Available': 'green',
// 			'Reserved': 'blue'
// 		};

// 		const color = status_colors[doc.unit_status] || 'gray';

// 		return [__(doc.unit_status), color, 'status,=,' + doc.unit_status];
// 	}
// };