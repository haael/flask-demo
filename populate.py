#!brython.js
#-*- coding: utf-8 -*-


from browser import document, ajax, alert, window, console
from browser.timer import set_timeout, clear_timeout
import re



loaded_devices = set()


def is_scrolled_into_view(element):
	rect = element.getBoundingClientRect()
	return (rect.top <= window.innerHeight) and (rect.bottom >= 0)


def load_visible_macs():
	console.log("load_visible_macs")
	rows = document['devices'].getElementsByTagName('tr')
	
	l = len(rows)
	start = 0
	stop = l
	while True:
		if stop - start <= 1:
			break
		row = rows[(start + stop) // 2]
		if row.getBoundingClientRect().top <= 0:
			start = (start + stop) // 2
		else:
			stop = (start + stop) // 2
	
	for n in range(start, l):
		row = rows[n]
		if not is_scrolled_into_view(row):
			break
		
		for cell in row.getElementsByTagName('td'):
			if cell.getAttribute('class') == 'mac_address':
				mac = str(cell.textContent).strip().lower()
				if mac and all((_ch in '0123456789abcdef:') for _ch in mac) and (mac not in loaded_devices):
					load_device_details(mac)
				break
		else:
			continue


device_rows = {}

def load_device_list():
	def device_list_loaded(response):
		if response.status != 200:
			console.log("Request failed: " + str(response.status))
			return
		
		mac_list = []
		
		parser = window.DOMParser.new()
		tree = parser.parseFromString(response.text, 'application/xml')
		devices = tree.getElementsByTagName('devices')[0].getElementsByTagName('device')
		fragment = document.createDocumentFragment()
		
		rows_at_time = 100
		def process_devices(i=0):
			console.log("process_devices " + str(i) + "/" + str(len(devices) // rows_at_time))
			
			if i == 0:
				while document['progress'].firstChild:
					document['progress'].removeChild(document['progress'].firstChild)
				for n in range(len(devices) // rows_at_time):
					prog_span = document.createElement('span')
					prog_span.setAttribute('class', 'prog_block_disabled')
					prog_span.appendChild(document.createTextNode("-"));
					document['progress'].appendChild(prog_span)
				document['overlay'].style.display = 'block'
			
			if i < len(devices) // rows_at_time:
				document['progress'].children[i].setAttribute('class', 'prog_block_enabled')
			
			for n in range(rows_at_time * i, rows_at_time * (i + 1)):
				if n >= len(devices):
					document['devices'].appendChild(fragment)
					document['overlay'].style.display = 'none'
					invalidate_devices_list()
					console.log("process_devices finished")
					break
				
				dev = devices[n]
				
				tr = fragment.appendChild(document.createElement('tr'))
				tr.setAttribute('class', 'devices_first')
				
				td = tr.appendChild(document.createElement('td'))
				td.setAttribute('class', 'mac_address')
				td.setAttribute('rowspan', '2')
				mac_address = dev.getAttribute('mac')
				td.appendChild(document.createTextNode(mac_address))
				
				mac_list.append(mac_address)
				device_rows[mac_address] = [tr, None]
				
				td = tr.appendChild(document.createElement('td'))
				td.setAttribute('class', 'mac_vendor')
				
				td = tr.appendChild(document.createElement('td'))
				td.setAttribute('class', 'dhcp_fingerprint')
				
				td = tr.appendChild(document.createElement('td'))
				td.setAttribute('class', 'fingerbank_guess')
				
				td = tr.appendChild(document.createElement('td'))
				td.setAttribute('class', 'hostname')
				
				td = tr.appendChild(document.createElement('td'))
				td.setAttribute('class', 'deduced_os')
				
				td = tr.appendChild(document.createElement('td'))
				td.setAttribute('class', 'operating_system')
				td.setAttribute('rowspan', '2')
				input_field = td.appendChild(document.createElement('input'))
				input_field.setAttribute('type', 'text')
				input_field.setAttribute('list', 'opsys_name')
				s_mac = mac_address.replace(':', '').lower()
				input_field.setAttribute('name', 'operating_system_' + s_mac)
				bind_input_field(input_field)
				
				td = tr.appendChild(document.createElement('td'))
				td.setAttribute('class', 'devweight')
				td.setAttribute('rowspan', '2')
				input_field = td.appendChild(document.createElement('input'))
				input_field.setAttribute('type', 'number')
				input_field.setAttribute('step', '0.01')
				input_field.setAttribute('name', 'devweight_' + s_mac)
				bind_input_field(input_field)

				tr = fragment.appendChild(document.createElement('tr'))
				tr.setAttribute('class', 'devices_second')
				
				td = tr.appendChild(document.createElement('td'))
				td.setAttribute('class', 'mac_address')
				td.setAttribute('rowspan', '2')
				mac_address = dev.getAttribute('mac')
				td.appendChild(document.createTextNode(mac_address))
				
				mac_list.append(mac_address)
				device_rows[mac_address][1] = tr
				
				td = tr.appendChild(document.createElement('td'))
				td.setAttribute('class', 'bonjour_name')
				
				td = tr.appendChild(document.createElement('td'))
				td.setAttribute('class', 'bonjour_model')
				
				td = tr.appendChild(document.createElement('td'))
				td.setAttribute('class', 'bonjour_services')
				
				td = tr.appendChild(document.createElement('td'))
				td.setAttribute('class', 'bonjour_txt')
				td.setAttribute('colspan', '2')

			else:
				set_timeout(lambda: process_devices(i + 1), 0)
		
		process_devices()
	
	ajax_request = ajax.ajax()
	ajax_request.bind('complete', device_list_loaded)
	ajax_request.open('GET', '/device/', True)
	ajax_request.send()


def device_details_loaded(response, mac, invalidate=False):
	if not len(mac) == 2 * 6 + 5: raise ValueError("mac should have length of " + str(2 * 6 + 5) + " characters")
	if not all(_ch in '0123456789abcdef:' for _ch in mac): raise ValueError("the only characters allowed in mac: [0123456789abcdef]")
	if not mac.count(':') == 5: raise ValueError("mac should have 5 ':' characters")
	
	if response.status not in (200, 404):
		console.log("Request failed: " + str(response.status))
		return
	
	try:
		remove_device = (response.status == 404)
		
		if remove_device:
			try:
				loaded_devices.remove(mac)
			except KeyError:
				pass
		
		mac_list = []
		
		if not remove_device:
			parser = window.DOMParser.new()
			tree = parser.parseFromString(response.text, 'application/xml')
			device_root = tree.getElementsByTagName('device')[0]
		
		#for row in document['devices'].getElementsByTagName('tr'):
		#	for cell in row.getElementsByTagName('td'):
		#		if cell.getAttribute('class') == 'mac_address' and str(cell.textContent).strip() == mac:
		#			break
		#	else:
		#		continue
		
		try:
			row1, row2 = device_rows[mac]
		except KeyError:
			console.log("No corresponding entry for " + mac)
			return
		
		if remove_device:
			document['devices'].removeChild(row1)
			document['devices'].removeChild(row2)
			loaded_devices.remove(mac)
			return
		
		loaded_devices.add(mac)
		
		for cell in [_cell for _cell in row1.getElementsByTagName('td')] + [_cell for _cell in row2.getElementsByTagName('td')]:
			if cell.getAttribute('class') != 'mac_address':
				if len(cell.getElementsByTagName('input')):
					input_field = cell.getElementsByTagName('input')[0]
					input_field.value = ''
				else:
					input_field = None
					while cell.firstChild:
						cell.removeChild(cell.firstChild)
			
			for child in device_root.children:
				#console.log("adding child: ", child.tagName, cell.getAttribute('class'), (child.tagName == cell.getAttribute('class')))
				if cell.getAttribute('class') == child.tagName:
					if input_field is not None:
						input_field.value = child.textContent
					elif child.tagName == 'fingerbank_guess':
						for textbit in child.textContent.split('/'):
							cell.appendChild(document.createTextNode(textbit))
							cell.appendChild(document.createElement('br'))
					else:
						cell.appendChild(document.createTextNode(child.textContent))

			if cell.getAttribute('class') == 'bonjour_txt':
				cell.appendChild(document.createElement('br'))

	finally:
		if invalidate:
			invalidate_devices_list({mac})

					

def load_device_details(mac):
	s_mac = mac.replace(':', '').lower()
	ajax_request = ajax.ajax()
	ajax_request.bind('complete', lambda response: device_details_loaded(response, mac))
	ajax_request.open('GET', '/device/' + s_mac, True)
	ajax_request.send()


def node_text(node):
	text_parts = []
	for child in node:
		if not hasattr(child, 'tagName'):
			text_parts.append(child.textContent)
	return ''.join(text_parts)


def opsys_details_loaded(response, invalidate=False):
	if response.status != 200:
		console.log("Request failed: " + str(response.status))
		return
	
	parser = window.DOMParser.new()
	tree = parser.parseFromString(response.text, 'application/xml')
	opsys_root = tree.getElementsByTagName('operating_system')[0]
	
	os_name_parts = []
	for child in opsys_root.childNodes:
		if child.nodeValue:
			os_name_parts.append(child.nodeValue)
	os_name = ''.join(os_name_parts).strip()
	del os_name_parts
	
	for row in document['operatingsystems'].getElementsByTagName('tr'):
		for cell in row.getElementsByTagName('td'):
			if cell.getAttribute('class') == 'os_name' and node_text(cell).strip() == os_name:
				break
		else:
			continue
		
		for child in opsys_root.children:
			for cell in row.getElementsByTagName('td'):
				if cell.getAttribute('class') == child.tagName:
					input_field = None
					try:
						input_field = cell.getElementsByTagName('input')[0]
					except IndexError:
						pass
					
					if input_field:
						val = child.textContent
						input_field.setAttribute('value', val)
						options_list = input_field.getAttribute('list')
						if options_list:
							extend_options_list(options_list, val)
					else:
						cell.appendChild(document.createTextNode(child.textContent))
					break
	
	if invalidate:
		invalidate_devices_list()


def load_opsys_details(oshash):
	ajax_request = ajax.ajax()
	ajax_request.bind('complete', opsys_details_loaded)
	ajax_request.open('GET', '/opsys/' + oshash, True)
	ajax_request.send()


def create_opsys_details(oshash, name, details={}):
	ajax_request = ajax.ajax()
	ajax_request.bind('complete', opsys_details_loaded)
	ajax_request.open('PUT', '/opsys/' + oshash, True)

	os_root = document.createElement('operating_system')
	os_root.setAttribute('hash', oshash)
	os_root.appendChild(document.createTextNode(name))
	for key, value in details.items():
		os_entry = os_root.appendChild(document.createElement(key))
		os_entry.appendChild(document.createTextNode(value))
	
	ajax_request.send(remove_xmlns(os_root.outerHTML))


def opsys_list_loaded(response, get_details=False, put_details=False):
	if response.status != 200:
		console.log("Request failed: " + str(response.status))
		return
	
	opsys_hashes = {}
	
	parser = window.DOMParser.new()
	tree = parser.parseFromString(response.text, 'application/xml')
	opsys_root = tree.getElementsByTagName('operating_systems')[0]
	for os in opsys_root.getElementsByTagName('operating_system'):
		tr = document['operatingsystems'].appendChild(document.createElement('tr'))
		
		os_hash = os.getAttribute('hash')
		os_name = str(os.textContent).strip()
		opsys_hashes[os_hash] = os_name
		td = tr.appendChild(document.createElement('td'))
		td.setAttribute('class', 'os_name')
		td.appendChild(document.createTextNode(os_name))
		delb = td.appendChild(document.createElement('button'))
		delb.setAttribute('name', 'os_delete_' + os_hash)
		delb.setAttribute('class', 'os_delete')
		delb.appendChild(document.createTextNode("x"));
		bind_os_delete_button(delb)
		
		#option = document['opsys_name'].appendChild(document.createElement('option'))
		#option.setAttribute('value', os_name)
		extend_options_list('opsys_name', os_name)
		
		td = tr.appendChild(document.createElement('td'))
		td.setAttribute('class', 'kernel_family')
		input_field = td.appendChild(document.createElement('input'))
		input_field.setAttribute('type', 'text')
		input_field.setAttribute('list', 'opsys_kernel')
		input_field.setAttribute('name', 'kernel_family_' + os_hash)
		bind_input_field(input_field)
		
		td = tr.appendChild(document.createElement('td'))
		td.setAttribute('class', 'platform')
		input_field = td.appendChild(document.createElement('input'))
		input_field.setAttribute('type', 'text')
		input_field.setAttribute('list', 'opsys_platform')
		input_field.setAttribute('name', 'platform_' + os_hash)
		bind_input_field(input_field)

		td = tr.appendChild(document.createElement('td'))
		td.setAttribute('class', 'flavor')
		input_field = td.appendChild(document.createElement('input'))
		input_field.setAttribute('type', 'text')
		input_field.setAttribute('list', 'opsys_flavor')
		input_field.setAttribute('name', 'flavor_' + os_hash)
		bind_input_field(input_field)

		td = tr.appendChild(document.createElement('td'))
		td.setAttribute('class', 'version_number')
		input_field = td.appendChild(document.createElement('input'))
		input_field.setAttribute('type', 'text')
		input_field.setAttribute('name', 'version_number_' + os_hash)
		bind_input_field(input_field)

		td = tr.appendChild(document.createElement('td'))
		td.setAttribute('class', 'code_name')
		input_field = td.appendChild(document.createElement('input'))
		input_field.setAttribute('type', 'text')
		input_field.setAttribute('name', 'code_name_' + os_hash)
		bind_input_field(input_field)
		
		td = tr.appendChild(document.createElement('td'))
		td.setAttribute('class', 'release_date')
		input_field = td.appendChild(document.createElement('input'))
		input_field.setAttribute('type', 'date')
		input_field.setAttribute('name', 'release_date_' + os_hash)
		bind_input_field(input_field)
		
		td = tr.appendChild(document.createElement('td'))
		td.setAttribute('class', 'osweight')
		input_field = td.appendChild(document.createElement('input'))
		input_field.setAttribute('type', 'number')
		input_field.setAttribute('step', '0.01')
		input_field.setAttribute('name', 'osweight_' + os_hash)
		bind_input_field(input_field)

	
	if get_details:
		for os_hash in opsys_hashes.keys():
			load_opsys_details(os_hash)
	elif put_details:
		for os_hash, os_name in opsys_hashes.items():
			create_opsys_details(os_hash, os_name)


def load_opsys_list():
	ajax_request = ajax.ajax()
	ajax_request.bind('complete', lambda response: opsys_list_loaded(response, get_details=True))
	ajax_request.open('GET', '/opsys/', True)
	ajax_request.send()


def extend_options_list(name, value):
	if not value:
		return
	console.log("extend_options_list " + name + " '" + value + "'")
	options_list = document[name]
	value_set = set()
	for option in options_list.getElementsByTagName('option'):
		value_set.add(option.getAttribute('value'))
	if value not in value_set:
		option = options_list.appendChild(document.createElement('option'))
		option.setAttribute('value', value)



input_fields = {}


def commit_data(name):
	if __debug__:
		console.log("commit_data %s", name)
	
	try:
		value = input_fields[name][0]
		options_list = input_fields[name][1]
		del input_fields[name]
	except KeyError:
		if __debug__:
			console.log("Key '%s' not found in input_fields" % (name))
		return
	
	found = False
	if options_list:
		for option in document[options_list].getElementsByTagName('option'):
			if option.getAttribute('value') == value:
				found = True
				break
		else:
			found = False
	
	if value and options_list and not found:
		extend_options_list(options_list, value)
	
	console.log("commit_data: sending ['" + name + "']:'" + value + "'")
	if value and name[:len('operating_system_')] == 'operating_system_' and not found:
		register_new_os(value)
	
	if name[:len('operating_system_')] == 'operating_system_' or name[:len('devweight_')] == 'devweight_':
		console.log("patching device...")
		patch_device(name, value)
	else:
		console.log("patching os...")
		patch_opsys(name, value)


def patch_device(name, value):
	mac = name.split('_')[-1]
	field_name = name[:-len(mac) - 1]
	s_mac = ':'.join(mac[2*_i:2*_i+2] for _i in range(6))
	
	ajax_request = ajax.ajax()
	ajax_request.bind('complete', lambda response: device_details_loaded(response, s_mac, True))
	ajax_request.open('PATCH', '/device/' + mac, True)
	ajax_request.set_header('Content-Type', 'text/xml;charset=utf-8')
	
	device = document.createElement('device')
	device.setAttribute('mac', s_mac)
	field = device.appendChild(document.createElement(field_name))
	field.appendChild(document.createTextNode(value))
	
	ajax_request.send(remove_xmlns(device.outerHTML))
	


def patch_opsys(name, value):
	oshash = name.split('_')[-1]
	field_name = name[:-len(oshash) - 1]
	
	ajax_request = ajax.ajax()
	ajax_request.bind('complete', lambda response: opsys_details_loaded(response, True))
	ajax_request.open('PATCH', '/opsys/' + oshash, True)
	ajax_request.set_header('Content-Type', 'text/xml;charset=utf-8')
	
	device = document.createElement('operating_system')
	device.setAttribute('hash', oshash)
	field = device.appendChild(document.createElement(field_name))
	field.appendChild(document.createTextNode(value))
	
	ajax_request.send(remove_xmlns(device.outerHTML))


def input_field_modified(event):
	name = event.target.name
	value = event.target.value

	if __debug__:
		console.log("input_field_modified %s : %s" % (name, value))
	
	timeout_id = None
	found = False
	options_list = event.target.getAttribute('list')
	if value and options_list:
		for option in document[options_list].getElementsByTagName('option'):
			if option.getAttribute('value') == value:
				found = True
				break
		else:
			found = False
	
	weight_entry = name[:len('devweight_')] == 'devweight_'
	
	if __debug__:
		if found:
			console.log("Entry '%s' found in options list '%s', setting timeout." % (value, options_list))
		elif not value:
			console.log("Empty entry, setting timeout.")
		elif weight_entry:
			console.log("'Weight' entry value %s, setting timeout." % (value))
	
	if found or not value or weight_entry:
		try:
			if input_fields[name][2]:
				clear_timeout(input_fields[name][2])
			del input_fields[name]
		except KeyError:
			pass
		timeout_id = set_timeout(lambda: commit_data(name), 7500)
	
	input_fields[name] = [value, options_list, timeout_id]


def input_field_activate(event):
	name = event.target.name
	value = event.target.value

	if __debug__:
		console.log("input_field_activate %s : %s" % (name, value))
	
	try:
		timeout_id = input_fields[name][1]
		if timeout_id:
			clear_timeout(timeout_id)
			input_fields[name][2] = None
		commit_data(name)
	except KeyError:
		pass


def input_field_keyup(event):
	if event.which == 13:
		if __debug__:
			console.log("input_field_keyup <enter>")
		if event.target.name not in input_fields:
			input_field_modified(event)
		input_field_activate(event)


def bind_input_field(input_field):
	input_field.bind('input', input_field_modified)
	input_field.bind('blur', input_field_activate)
	input_field.bind('keyup', input_field_keyup)


def register_new_os(osname):
	def os_hash_generated(response):
		if response.status != 200:
			console.log("Request failed: " + str(response.status))
			return
		
		result_hash = None
		parser = window.DOMParser.new()
		tree = parser.parseFromString(response.text, 'application/xml')
		opsys_root = tree.getElementsByTagName('operating_systems')[0]
		for os in opsys_root.getElementsByTagName('operating_system'):
			if str(os.textContent).strip() == osname:
				result_hash = os.getAttribute('hash')
				break
		
		if result_hash:
			opsys_list_loaded(response, put_details=True)
	
	ajax_request = ajax.ajax()
	ajax_request.bind('complete', os_hash_generated)
	ajax_request.open('POST', '/opsys/', True)
	ajax_request.set_header('Content-Type', 'text/xml;charset=utf-8')
	
	os_root = document.createElement('operating_systems')
	os_entry = os_root.appendChild(document.createElement('operating_system'))
	os_entry.appendChild(document.createTextNode(osname))
	
	ajax_request.send(remove_xmlns(os_root.outerHTML))


def remove_xmlns(xmltext):
	return re.sub('\\ xmlns\\=\\"[^\\"]*\\"', '', xmltext)

def delete_os_entry(event):
	os_hash = event.target.name.split('_')[-1]
	
	def os_deleted(response):
		invalidate_devices_list()
		
		if response.status != 204:
			console.log("Request failed: " + str(response.status))
			return
		
		console.log("remove " + os_hash)
		
		os_name = None
		for tr in document['operatingsystems'].getElementsByTagName('tr'):
			for td in tr.getElementsByTagName('td'):
				if td.getAttribute('class') == 'os_name':
					buttons = td.getElementsByTagName('button')
					if len(buttons):
						button = buttons[0]
						console.log("" + button.tagName)
						if button.getAttribute('name') == event.target.name:
							console.log("removing " + event.target.name)
							os_name = node_text(td).strip()
							tr.parentNode.removeChild(tr)
							break
			else:
				continue
			break
		
		for option in document['opsys_name'].getElementsByTagName('option'):
			if option.getAttribute('value') == os_name:
				option.parentNode.removeChild(option)
	
	ajax_request = ajax.ajax()
	ajax_request.bind('complete', os_deleted)
	ajax_request.open('DELETE', '/opsys/' + os_hash, True)
	ajax_request.send()


delete_buttons = set()


def bind_os_delete_button(button):
	console.log("bind_os_delete_button" + button.name)
	delete_buttons.add(button.name)
	def os_delete_clicked(event):
		console.log("os_delete_clicked " + event.target.name)
		if document['show_os_delete'].checked:
			delete_os_entry(event)
	button.bind('click', os_delete_clicked)


def bind_show_os_delete_button():
	console.log("bind_show_os_delete_button")
	def show_os_delete_changed(event):
		for delete_button in set(delete_buttons):
			try:
				if event.target.checked:
					document[delete_button].style.opacity = "1"
				else:
					document[delete_button].style.opacity = "0"
			except KeyError:
				delete_buttons.remove(delete_button)
	document['show_os_delete'].bind('check', show_os_delete_changed)


scrolling_timeout = None

def bind_load_visible_devices_on_scroll():
	console.log("load_visible_devices_on_scroll")
	
	def scrolled_timeout():
		global scrolling_timeout
		scrolling_timeout = None
		load_visible_macs()
	
	def window_scrolled(event):
		global scrolling_timeout
		if scrolling_timeout:
			clear_timeout(scrolling_timeout)
		scrolling_timeout = set_timeout(scrolled_timeout, 500)
	
	window.bind('scroll', window_scrolled)


def invalidate_devices_list(except_macs=frozenset()):
	console.log("invalidate_devices_list")
	loaded_devices.clear()
	loaded_devices.update(except_macs)
	load_visible_macs()

