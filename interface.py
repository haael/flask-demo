#!/usr/bin/python3
#-*- coding:utf-8 -*-


from flask import Flask, request, abort
from pathlib import Path
from lxml import etree
from hashlib import sha3_256
import csv
from collections import Counter
import math
from detect_os import *
#from dao import Devices
import json


app = Flask(__name__)


mime_xml = [('Content-Type', 'text/xml;charset=utf-8')]
mime_xhtml = [('Content-Type', 'application/xhtml+xml;charset=utf-8')]


@app.errorhandler(400)
def error_400(error):
	return Path('error_400.html').read_text(), 400, mime_xhtml


@app.errorhandler(401)
def error_401(error):
	return Path('error_401.html').read_text(), 401, mime_xhtml


@app.errorhandler(403)
def error_403(error):
	return Path('error_403.html').read_text(), 403, mime_xhtml


@app.errorhandler(404)
def error_404(error):
	return Path('error_404.html').read_text(), 404, mime_xhtml


@app.errorhandler(405)
def error_405(error):
	return Path('error_405.html').read_text(), 405, mime_xhtml


@app.errorhandler(410)
def error_410(error):
	return Path('error_410.html').read_text(), 410, mime_xhtml


@app.errorhandler(415)
def error_415(error):
	return Path('error_415.html').read_text(), 415, mime_xhtml


@app.errorhandler(422)
def error_422(error):
	return Path('error_422.html').read_text(), 422, mime_xhtml


@app.route('/')
def index_html():
	return Path('index.html').read_text(), mime_xhtml

'''
@app.route('/favicon.ico')
def favicon_ico():
	return open('favicon.ico').readall()
'''

@app.route('/style.css')
def style_css():
	return Path('style.css').read_text(), [('Content-Type', 'text/css;charset=utf-8'), ('Cache-Control', 'only-if-cached, max-age=604800')]

'''
@app.route('/device.xslt')
def devices_xslt():
	return Path('device.xslt').read_text(), [('Content-Type', 'text/xsl')]
'''

@app.route('/brython.js')
def brython_js():
	return Path('brython.js').read_text(), [('Content-Type', 'text/javascript;charset=utf-8'), ('Cache-Control', 'only-if-cached, max-age=604800')]


@app.route('/brython_stdlib.js')
def brython_stdlib_js():
	return Path('brython_stdlib.js').read_text(), [('Content-Type', 'text/javascript;charset=utf-8'), ('Cache-Control', 'only-if-cached, max-age=604800')]


@app.route('/populate.py')
def populate_py():
	return Path('populate.py').read_text(), [('Content-Type', 'text/python;charset=utf-8')]


@app.route('/device/')
def device_list():
	global devices
	
	response = etree.Element('devices')
	
	filter_data = request.args.get('filter', None)
	filter_bits = request.args.get('bits', None)
	filter_hashes = request.args.get('hashes', None)
	
	if (filter_data is None) and (filter_bits is None) and (filter_hashes is None):
		for mac in devices.keys():
			device = etree.SubElement(response, 'device')
			device.attrib['mac'] = mac
	else:
		try:
			filter_data = int(filter_data, 16)
			filter_bits = int(filter_bits)
			filter_hashes = int(filter_hashes)
		except ValueError:
			abort(400)
		
		macs_filter = Bloom(filter_bits, filter_hashes, filter_data)
		for mac in devices.keys():
			if mac not in macs_filter: continue
			
			device = etree.SubElement(response, 'device')
			device.attrib['mac'] = mac
			
			for key, value in devices[mac].items():
				subelement = etree.SubElement(response, key)
				subelement.text = value
			
			try:
				deduced_os = detect_os(devices[mac])[0][0]
				subelement = etree.SubElement(response, 'deduced_os')
				subelement.text = deduced_os
			except IndexError:
				pass
	
	result = []
	result.append("<?xml version=\"1.0\"?>\n")
	#result.append("<?xml-stylesheet type=\"text/xsl\" href=\"/device.xslt\"?>\n")
	result.append(etree.tostring(response, pretty_print=True).decode('utf-8'))
	
	return ''.join(result), mime_xml


@app.route('/device/<mac>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
def device_info(mac):
	global devices, dev_2_os
	
	if len(mac) != 12:
		abort(404)
	
	for ch in mac:
		if ch not in '0123456789abcdef':
			abort(404)
	
	try:
		d_mac = ':'.join(mac[2*i:2*i+2] for i in range(6))
	except ValueError:
		abort(404)
	
	if (request.method in ['GET', 'PATCH', 'DELETE']) and (d_mac not in devices):
		abort(410)
	
	if (request.method in ['PUT']) and (d_mac in devices):
		abort(405)
	
	if request.method == 'DELETE':
		del devices[d_mac]
	
	status = 200
	
	if request.method in ['PUT', 'PATCH']:
		if request.mimetype not in ['text/xml', 'application/xml']:
			abort(415)
		
		if request.method == 'PUT':
			entry = devices[d_mac] = {}
			status = 201
		elif request.method == 'PATCH':
			entry = devices[d_mac]
		else:
			entry = {}
		
		try:
			rdata = etree.fromstring(request.data)
		except etree.XMLSyntaxError as error:
			abort(400)
		
		for subd in rdata:
			if subd.text and subd.text.strip():
				entry[subd.tag] = subd.text.strip()
			else:
				try:
					del entry[subd.tag]
				except KeyError:
					pass
	
	if request.method in ['PUT', 'PATCH', 'DELETE']:
		generate_model(devices)
		with Path('model.json').open('w') as fp:
			json.dump(save_model(), fp)
		with Path('dev2os.json').open('w') as fp:
			json.dump(dev_2_os, fp)
	
	if request.method == 'DELETE':
		del devices[d_mac]
		return "", 204
	
	#print(detect_os_sorted(devices[d_mac]))
	
	try:
		deduced_os = detect_os(devices[d_mac])[0][0]
		#print("found:", deduced_os)
	except IndexError:
		deduced_os = None
		#print("not found")
	
	response = etree.Element('device')
	response.attrib['mac'] = d_mac
	for key, value in devices[d_mac].items():
		subelement = etree.SubElement(response, key)
		subelement.text = value
	
	if deduced_os:
		subelement = etree.SubElement(response, 'deduced_os')
		subelement.text = deduced_os
	
	return etree.tostring(response, pretty_print=True), status, mime_xml


@app.route('/opsys/', methods=['GET', 'POST'])
def opsys_list():
	global operating_systems
	
	if request.method == 'GET':
		operating_systems_list = operating_systems
	
	elif request.method == 'POST':
		if request.mimetype not in ['text/xml', 'application/xml']:
			abort(415)

		try:
			osroot = etree.fromstring(request.data)
		except etree.XMLSyntaxError as error:
			abort(400)
		
		if osroot.tag == 'operating_systems':
			operating_systems_list = {}
			for child in osroot:
				if child.tag != 'operating_system':
					continue
				if not child.text:
					abort(422)
				operating_systems_list[child.text] = {}
		else:
			abort(422)
	
	response = etree.Element('operating_systems')
	for os_name in operating_systems_list.keys():
		os = etree.SubElement(response, 'operating_system')
		os.attrib['hash'] = sha3_256(os_name.encode('utf-8')).hexdigest()[:16]
		os.text = os_name
	
	result = []
	result.append("<?xml version=\"1.0\"?>\n")
	#result.append("<?xml-stylesheet type=\"text/xsl\" href=\"/device.xslt\"?>\n")
	result.append(etree.tostring(response, pretty_print=True).decode('utf-8'))
	
	return ''.join(result), mime_xml


@app.route('/opsys/<oshash>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
def opsys_info(oshash):
	global operating_systems
	
	if len(oshash) != 16:
		abort(404)
	
	for ch in oshash:
		if ch not in '0123456789abcdef':
			abort(404)
	
	for key, value in operating_systems.items():
		if oshash == sha3_256(key.encode('utf-8')).hexdigest()[:16]:
			os_name = key
			properties = value
			if request.method in ['PUT']:
				abort(405)
			break
	else:
		if request.method in ['GET', 'PATCH', 'DELETE']:
			abort(410)
	
	if request.method in ['DELETE']:
		del operating_systems[os_name]
	elif request.method in ['PUT', 'PATCH']:
		try:
			osroot = etree.fromstring(request.data)
		except etree.XMLSyntaxError as error:
			abort(400)
		
		if osroot.text:
			os_name_literal = osroot.text.strip()
			if oshash != sha3_256(os_name_literal.encode('utf-8')).hexdigest()[:16]:
				abort(422)
		else:
			os_name_literal = None
		
		#print("update: " + request.method + " " + os_name)
		if request.method == 'PUT':
			if not os_name_literal:
				abort(422)
			os_name = os_name_literal
			properties = operating_systems[os_name] = {}
		else:
			if os_name_literal and os_name != os_name_literal:
				abort(422)
			properties = operating_systems[os_name]
		
		for child in osroot:
			if child.text and child.text.strip():
				properties[child.tag] = child.text.strip()
			else:
				try:
					del properties[child.tag]
				except KeyError:
					pass
	
	if request.method in ['PUT', 'PATCH', 'DELETE']:
		generate_model(devices)
		with Path('model.json').open('w') as fp:
			json.dump(save_model(), fp)
		with Path('opsys.json').open('w') as fp:
			json.dump(operating_systems, fp)
	
	if request.method in ['DELETE']:
		return "", 204
	
	response = etree.Element('operating_system')
	response.attrib['hash'] = oshash
	response.text = os_name
	for key, value in properties.items():
		subel = etree.SubElement(response, key)
		subel.text = value
	
	result = []
	result.append("<?xml version=\"1.0\"?>\n")
	#result.append("<?xml-stylesheet type=\"text/xsl\" href=\"/device.xslt\"?>\n")
	result.append(etree.tostring(response, pretty_print=True).decode('utf-8'))
	
	return ''.join(result), mime_xml





try:
	with Path('opsys.json').open() as fp:
		operating_systems = json.load(fp)
except FileNotFoundError:
	operating_systems = {
		"Apple/Mac": {'kernel_family':"Apple", 'platform':"computer/laptop"},
		"Apple/iPad": {'kernel_family':"Apple", 'platform':"mobile/pad"},
		"Apple/iPhone": {'kernel_family':"Apple", 'platform':"mobile/phone"},
		"Apple/TV": {'kernel_family':"Apple", 'platform':"iot/tv"},
		
		"Windows/Laptop": {'kernel_family':"Microsoft", 'platform':"computer/laptop"},
		"Windows/Desktop": {'kernel_family':"Microsoft", 'platform':"computer/desktop"},
		"Nokia/Phone": {'kernel_family':"Microsoft", 'platform':"mobile/phone"},
		#"Amazon/Echo": {'kernel_family':"Microsoft", 'platform':"iot/assistant"},
		
		"Linux/Laptop": {'kernel_family':"Linux", 'platform':"computer/laptop"},
		"Linux/Desktop": {'kernel_family':"Linux", 'platform':"computer/desktop"},
		"Android/Phone": {'kernel_family':"Linux", 'platform':"mobile/phone"},
		"Linux/TV": {'kernel_family':"Linux", 'platform':"iot/tv"}
	}

set_os_list(operating_systems)


try:
	with Path('dev2os.json').open() as fp:
		dev_2_os = json.load(fp)
except FileNotFoundError:
	dev_2_os = {}


class Dev2OSRecord:
	dev_2_os_keys = 'operating_system', 'devweight'
	
	def __init__(self, under, dev_2_os):
		if 'mac' not in under:
			raise ValueError("'under' dict should have 'mac' key")
		self.__under = dict(under)
		self.__dev_2_os = dev_2_os
	
	def keys(self):
		assert 'mac' in self.__under
		if self.__under['mac'] in self.__dev_2_os:
			for key in self.dev_2_os_keys:
				if self.__dev_2_os[self.__under['mac']][self.dev_2_os_keys.index(key)] != None:
					yield key
		yield from self.__under
	
	def values(self):
		for key in keys:
			yield self[key]
	
	def items(self):
		for key in self.keys():
			yield key, self[key]
	
	def __getitem__(self, key):
		if key in self.dev_2_os_keys:
			assert 'mac' in self.__under
			result = self.__dev_2_os[self.__under['mac']][self.dev_2_os_keys.index(key)]
			if result == None:
				raise KeyError("Key not set in __dev_2_os field: " + key)
			return result
		else:
			return self.__under[key]
	
	def __setitem__(self, key, value):
		if key in self.dev_2_os_keys:
			assert 'mac' in self.__under
			mac = self.__under['mac']
			if mac not in self.__dev_2_os:
				self.__dev_2_os[mac] = [None, None]
			self.__dev_2_os[mac][self.dev_2_os_keys.index(key)] = value
		else:
			self.__under[key] = value
	
	def __delitem__(self, key):
		if key in self.dev_2_os_keys:
			assert 'mac' in self.__under
			mac = self.__under['mac']
			existing = self.__dev_2_os[mac][self.dev_2_os_keys.index(key)]
			if existing == None:
				raise KeyError("Key not set in __dev_2_os field: " + key)
			self.__dev_2_os[mac][self.dev_2_os_keys.index(key)] = None
			if self.__dev_2_os[mac] == [None, None]:
				del self.__dev_2_os[mac]
		else:
			del self.__under[key]
	
	def __repr__(self):
		r = dict(self.__under)
		try:
			r.update(dict((_key, self.__dev_2_os[self.__under['mac']][self.dev_2_os_keys.index(_key)]) for _key in self.dev_2_os_keys))
		except KeyError:
			pass
		return repr(r)


class Dev2OSProxy:
	def __init__(self, devices_db, dev_2_os):
		self.devices_db = devices_db
		self.dev_2_os = dev_2_os
	
	def __getitem__(self, mac):
		#print("Dev2OSProxy.__getitem__", mac)
		return Dev2OSRecord(self.devices_db[mac], self.dev_2_os)
	
	def keys(self):
		yield from self.devices_db.keys()
	
	def values(self):
		for device in self.devices_db.values():
			yield Dev2OSRecord(device, self.dev_2_os)
	
	def items(self):
		for mac, device in self.devices_db.values():
			yield mac, Dev2OSRecord(device, self.dev_2_os)
	
	def __contains__(self, mac):
		return mac in self.devices_db
		

#devices = Dev2OSProxy(Devices.detailed(), dev_2_os)

#devices = Devices.detailed_os()

#for device in devices.values():
#	print(device)



try:
	with Path('devices.json').open() as fp:
		devices = json.load(fp)
except FileNotFoundError:
	with Path('devices.csv').open() as devices_file:
		devices = {}
		
		for n, row in enumerate(csv.reader(devices_file)):
			if n == 0:
				continue
			
			hostname = str(hash(row[1]))
			if not hostname:
				hostname = None
			
			mac_vendor = row[2]
			if mac_vendor == "NULL":
				mac_vendor = None
			
			fingerbank_guess = row[3]
			if fingerbank_guess in ["Not found", "Empty"]:
				fingerbank_guess = None
			
			dhcp_fingerprint = row[4]
			if not dhcp_fingerprint:
				dhcp_fingerprint = None
			
			mac = ':'.join(row[5][2*i:2*i+2] for i in range(3)) + ':' + ':'.join(format((n >> (2 - i) * 8) & 0xff, '02x') for i in range(3))
			properties = {'hostname':hostname, 'mac_vendor':mac_vendor, 'fingerbank_guess':fingerbank_guess, 'dhcp_fingerprint':dhcp_fingerprint}
			for key, value in dict(properties).items():
				if value is None:
					del properties[key]
			devices[mac] = properties


generate_model(devices)


with Path('model.json').open('w') as fp:
	json.dump(save_model(), fp)

with Path('devices.json').open('w') as fp:
	json.dump(devices, fp)

with Path('opsys.json').open('w') as fp:
	json.dump(operating_systems, fp)


if __name__ == '__main__':
	app.run(debug=True)

