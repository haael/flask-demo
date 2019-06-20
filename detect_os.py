#!/usr/bin/python3
#-*- coding:utf-8 -*-


__all__ = ['set_os_list', 'generate_model', 'set_model', 'get_model', 'save_model', 'load_model', 'detect_os']


from collections import defaultdict, Counter
from fractions import Fraction
import math
from functools import reduce


'''
class Exponent(Rational):
	def __init__(self, base, exponent):
		self.base = base
		self.exponent = exponent
	
	@property
	def numerator(self):
		if self.exponent >= 0:
			return self.base.numerator ** abs(self.exponent)
		else:
			return self.base.denominator ** abs(self.exponent)
	
	@property
	def denominator(self):
		if self.exponent >= 0:
			return self.base.denominator ** abs(self.exponent)
		else:
			return self.base.numerator ** abs(self.exponent)
'''		


class Token:
	def __init__(self, literal, number=None, positive=True):
		self.txt = ('' if positive else '~') + literal + (('_' + str(number)) if (number is not None) else '')
	
	def __and__(self, other):
		return Token('&'.join((str(self), str(other))))
	
	def __or__(self, other):
		return Token('|'.join((str(self), str(other))))
	
	def __not__(self):
		return Token(''.join(('~', str(self))))
	
	def __getattr__(self, key):
		return getattr(self.txt, key)
	
	def __str__(self):
		return self.txt
	
	def __iter__(self):
		yield from self.txt
	
	def __eq__(self, other):
		return self.txt == other
	
	def __hash__(self):
		return hash(self.txt)



class Probability(defaultdict):
	numeric = float
	
	def __init__(self):
		super().__init__(lambda: self.numeric(0))
		self.cache = {}
	
	def __setitem__(self, key, value):
		if self.cache:
			self.cache = {}
		
		if not isinstance(key, str):
			key = str(key)
		
		if '|' in key:
			raise ValueError("Conditional probability can not be set directly.")
		elif '&' in key:
			super().__setitem__('&'.join(sorted(key.split('&'))), self.numeric(value))
		else:
			super().__setitem__(key, self.numeric(value))
	
	def __delitem__(self, key):
		if self.cache:
			self.cache = {}
		
		if not isinstance(key, str):
			key = str(key)
		
		if '&' in key:
			super().__delitem__('&'.join(sorted(key.split('&'))))
		else:
			super().__delitem__(key)
	
	def __getitem__(self, key):
		if not isinstance(key, str):
			key = str(key)
		
		#try:
		#	return self.cache[key]
		#except KeyError:
		#	pass
		
		if '|' in key:
			a, b = key.split('|')
			try:
				#print(b, self[b])
				result = self['&'.join((a, b))] / self[b]
				self.cache[key] = result
				return result
			except ZeroDivisionError:
				if self['&'.join((a, b))] == 0:
					result = self.numeric(0)
					self.cache[key] = result
					return result
				else:
					raise
		elif '&' in key:
			result = super().__getitem__('&'.join(sorted(key.split('&'))))
			self.cache[key] = result
			return result
		else:
			result = super().__getitem__(key)
			self.cache[key] = result
			return result
	
	def update(self, collection):
		if self.cache:
			self.cache = {}
		super().update({ str(_key) : self.numeric(_val) for (_key, _val) in collection.items() })


model = Probability()


operating_systems = {}


def get_model():
	return model


def set_os_list(os_list):
	global operating_systems
	operating_systems = os_list


def set_model(new_model):
	global model
	model = new_model




class SearchTree:
	__slots__ = ['weight', 'arcs']
	
	def __init__(self, collection=None):
		self.weight = 0
		self.arcs = {}
		if collection:
			self.update(collection)
	
	def add(self, keyword):
		st = self
		for ch in keyword:
			try:
				st = self.arcs[ch]
			except KeyError:
				st = self.arcs[ch] = self.__class__()
		st.weight += 1
	
	def update(self, collection):
		for keyword in collection:
			self.add(keyword)
	
	def __getitem__(self, keyword):
		st = self
		for ch in keyword:
			st = self.arcs[ch]
		return st.weight
	
	def __iter__(self):
		if self.weight:
			yield "", self.weight
		for key, st in self.arcs.items():
			for kw, weight in st:
				yield key + kw, weight


def extract_features(collection, selector=lambda _x: _x):
	st = SearchTree()
	for entry in collection:
		keyword = selector(entry)
		for m in range(len(keyword) - 3):
			for n in range(m + 3, len(keyword)):
				st.add(keyword[m:n])
	for keyword, weight in sorted(st, key=lambda _k: -_k[1]):
		if weight > 1:
			yield keyword





def device_features(device):
	features = []
	
	try:
		features.append(bool(device['gateway']))
	except KeyError:
		features.append(False)

	try:
		features.append(bool(device['vpn']))
	except KeyError:
		features.append(False)
	
	try:
		hostname = device['hostname'].lower()
	except KeyError:
		hostname = ""
	features.append(hostname == "")
	features.append("air" in hostname)
	features.append("iphone" in hostname)
	features.append("iphone6" in hostname)
	features.append("ipad" in hostname)
	features.append("ipad3" in hostname)
	features.append("mac" in hostname)
	features.append("imac" in hostname)
	features.append("mbp" in hostname)
	features.append("macbook" in hostname)
	features.append("apple" in hostname)
	features.append("tv" in hostname)
	features.append("pad" in hostname)
	features.append("amazon" in hostname)
	features.append("android" in hostname)
	features.append("desktop" in hostname)
	features.append("laptop" in hostname)
	features.append("lenovo" in hostname)
	features.append("pc" in hostname)
	features.append("samsung" in hostname)
	features.append("tivo" in hostname)
	features.append("sonos" in hostname)
	features.append("phone" in hostname)
	features.append("windows" in hostname)
	features.append("galaxy" in hostname)
	features.append("netpicket" in hostname)
	features.append("printer" in hostname)
	features.append("ubuntu" in hostname)
	features.append("-phone" in hostname)
	features.append("lap" in hostname)
	features.append("epson" in hostname)
	features.append("xbox" in hostname)
	features.append("pro" in hostname)
	features.append("ideapad" in hostname)
	features.append("note8" in hostname)
	features.append("kindle" in hostname)
	features.append("blackberry" in hostname)
	features.append("phone" in hostname)
	features.append("humax" in hostname)
	features.append("sec" in hostname)
	features.append("one" in hostname)
	features.append("onep" in hostname)
	features.append("oneplus" in hostname)
	features.append("polycom" in hostname)
	features.append("redmi" in hostname)
	features.append("@lujam" in hostname)
	features.append("hp" in hostname)
	features.append("ipod" in hostname)
	features.append("watch" in hostname)
	features.append("aple" in hostname)
	features.append("touch" in hostname)
	features.append("huawei" in hostname)
	features.append("bitv" in hostname)
	features.append("bit" in hostname)
	features.append("notebook" in hostname)
	features.append("spin" in hostname)
	features.append("router" in hostname)
	features.append("kindle" in hostname)
	features.append("*" in hostname)
	features.append("@" in hostname)
	features.append("asus" in hostname)
	features.append("chrome" in hostname)
	features.append("chromecast" in hostname)
	features.append("netbook" in hostname)
	features.append("tablet" in hostname)
	features.append("sm" in hostname)
	features.append("tivo" in hostname)
	features.append("com" in hostname)
	features.append("mid" in hostname)
	features.append("surface" in hostname)
	features.append("bt" in hostname)
	features.append("ex" in hostname)
	features.append("thinkpad" in hostname)
	features.append("honor" in hostname)
	features.append("sip" in hostname)
	features.append("harmony" in hostname)
	features.append("hub" in hostname)
	features.append("ps4" in hostname)
	features.append("top" in hostname)
	features.append("geminilake" in hostname)
	features.append("lt" in hostname)
	features.append("audio" in hostname)
	features.append("sound" in hostname)
	features.append("windows" in hostname)
	features.append("win" in hostname)
	features.append("nas" in hostname)
	features.append("localhost" in hostname)
	
	try:
		fingerbank = device['fingerbank_guess']
	except KeyError:
		fingerbank = ""
	features.append(fingerbank == "")
	features.append("Windows" in fingerbank)
	features.append("Linux" in fingerbank)
	features.append("Android" in fingerbank)
	features.append("Google" in fingerbank)
	features.append("Solaris" in fingerbank)
	features.append("OpenSolaris" in fingerbank)
	features.append("Microsoft" in fingerbank)
	features.append("Router" in fingerbank)
	features.append("Netgear" in fingerbank)
	features.append("Apple" in fingerbank)
	features.append("Audio" in fingerbank)
	features.append("Video" in fingerbank)
	features.append("Panasonic" in fingerbank)
	features.append("Linksys" in fingerbank)
	features.append("Debian" in fingerbank)
	features.append("Tizen" in fingerbank)
	features.append("Xbox" in fingerbank)
	features.append("iOS" in fingerbank)
	features.append("Gaming" in fingerbank)
	features.append("Console" in fingerbank)
	features.append("Access Point" in fingerbank)
	features.append("Printer" in fingerbank)
	features.append("Scanner" in fingerbank)
	features.append("Microsoft Windows Kernel 10.0" in fingerbank)
	features.append("VoIP" in fingerbank)
	features.append("Polycom" in fingerbank)
	features.append("Chrome" in fingerbank)
	
	try:
		mac_vendor = device['mac_vendor'].lower()
	except KeyError:
		mac_vendor = ""
	features.append("apple" in mac_vendor)
	features.append("amazon" in mac_vendor)
	features.append("samsung" in mac_vendor)
	features.append("samsung electronics" in mac_vendor)
	features.append("samsung electro-mechanics" in mac_vendor)
	features.append("humax" in mac_vendor)
	features.append("canon" in mac_vendor)
	features.append("intel" in mac_vendor)
	features.append("liteon" in mac_vendor)
	features.append("hon hai" in mac_vendor)
	features.append("azurewave" in mac_vendor)
	features.append("arris" in mac_vendor)
	features.append("sonos" in mac_vendor)
	features.append("askey" in mac_vendor)
	features.append("sony" in mac_vendor)
	features.append("xiaomi" in mac_vendor)
	features.append("sychip" in mac_vendor)
	features.append("htc" in mac_vendor)
	features.append("netgear" in mac_vendor)
	features.append("huawei" in mac_vendor)
	features.append("panasonic" in mac_vendor)
	features.append("rebound" in mac_vendor)
	features.append("motorola" in mac_vendor)
	features.append("nokia" in mac_vendor)
	features.append("zyxel" in mac_vendor)
	features.append("flextronics" in mac_vendor)
	features.append("lg" in mac_vendor)
	features.append("mobile" in mac_vendor)
	features.append("mobility" in mac_vendor)
	features.append("chiun mai" in mac_vendor)
	features.append("lenovo" in mac_vendor)
	features.append("oneplus" in mac_vendor)
	features.append("murata" in mac_vendor)
	features.append("lujam" in mac_vendor)
	features.append("rivet" in mac_vendor)
	features.append("hewlett packard" in mac_vendor)
	features.append("asus" in mac_vendor)
	features.append("raspberry pi" in mac_vendor)
	features.append("zhejiang dahua" in mac_vendor)
	features.append("tp-link" in mac_vendor)
	features.append("dell" in mac_vendor)
	features.append("seiko" in mac_vendor)
	features.append("epson" in mac_vendor)
	features.append("microsoft" in mac_vendor)
	features.append("blackberry" in mac_vendor)
	features.append("arcadyan" in mac_vendor)
	features.append("sagem" in mac_vendor)
	features.append("polycom" in mac_vendor)
	features.append("nest" in mac_vendor)
	features.append("vmware" in mac_vendor)
	features.append("bskyb" in mac_vendor)
	features.append("d-link" in mac_vendor)
	features.append("cisco" in mac_vendor)
	features.append("linksys" in mac_vendor)
	features.append("arris" in mac_vendor)
	features.append("ubiquiti" in mac_vendor)
	features.append("slim" in mac_vendor)
	features.append("nintendo" in mac_vendor)
	features.append("open mesh" in mac_vendor)
	features.append("quanta" in mac_vendor)
	features.append("microsoft mobile oy" in mac_vendor)
	features.append("qemu" in mac_vendor)
	features.append("xensource" in mac_vendor)
	features.append("buffalo" in mac_vendor)
	
	try:
		bonjour_name = device['bonjour_name'].lower()
	except KeyError:
		bonjour_name = ""
	features.append(bonjour_name == "")
	features.append("imac" in bonjour_name)
	features.append("mac" in bonjour_name)
	features.append("macbook" in bonjour_name)
	features.append("air" in bonjour_name)
	features.append("yv" in bonjour_name)
	features.append("sonos" in bonjour_name)
	features.append("samsung" in bonjour_name)
	features.append("galaxy" in bonjour_name)
	features.append("laptop" in bonjour_name)
	features.append("pad" in bonjour_name)
	features.append("pc" in bonjour_name)
	features.append("ps4" in bonjour_name)

	#try:
	#	bonjour_model = device['bonjour_model']
	#except KeyError:
	#	bonjour_model = ""
	#features.append(bonjour_model == "")

	try:
		bonjour_services = device['bonjour_services'].split(",")
	except KeyError:
		bonjour_services = []
	features.append(bonjour_services == [])
	features.append("gamecenter" in bonjour_services)
	features.append("companion-link" in bonjour_services)
	features.append("airplay" in bonjour_services)
	features.append("appletv-v2" in bonjour_services)
	features.append("raop" in bonjour_services)
	features.append("sleep-proxy" in bonjour_services)
	features.append("touch-able" in bonjour_services)
	features.append("tw-multipeer" in bonjour_services)
	features.append("airdrop" in bonjour_services)
	features.append("smb" in bonjour_services)
	features.append("http" in bonjour_services)
	features.append("ipp" in bonjour_services)
	features.append("ipps" in bonjour_services)
	features.append("pdl-datastream" in bonjour_services)
	features.append("printer" in bonjour_services)
	features.append("privet" in bonjour_services)
	features.append("scanner" in bonjour_services)
	features.append("spotify-connect" in bonjour_services)
	features.append("teamviewer" in bonjour_services)
	features.append("sftp" in bonjour_services)
	features.append("ssh" in bonjour_services)
	features.append("afpovertcp" in bonjour_services)
	features.append("cba8" in bonjour_services)
	features.append("msgsys" in bonjour_services)
	features.append("pds" in bonjour_services)
	features.append(any(_tivo in bonjour_services for _tivo in ("tivo-device", "tivo-mindrpc", "tivo-remote", "tivo-videostream", "tivo-xcode")))
	features.append("yv-bridge" in bonjour_services)
	features.append(any(_pulse in bonjour_services for _pulse in ("pulse-server", "pulse-sink", "pulse-source")))
	features.append("afpovertcp" in bonjour_services)
	features.append("atc" in bonjour_services)
	features.append("daap" in bonjour_services)
	features.append("nvstrea" in bonjour_services)
	features.append("canon-bjnp1" in bonjour_services)
	features.append("workstation" in bonjour_services)

#HippoRemote,KeynoteControl,OZOmniFocus2,afpovertcp,bttremote,companion-link,http,ipp,ipps,nfs,omnistate,smb,textexpander,udisks-ssh,ptService,workstation
#arxcontrol,canon-bjnp1,http,ipp,ipps,printer,privet,scanner,uscan

	
	#try:
	#	bonjour_txt = device['bonjour_txt']
	#except KeyError:
	#	bonjour_txt = ""
	#features.append(bonjour_txt == "")

	return features


def opsys_features(opsys):
	features = []
	
	try:
		kernel_family = opsys['kernel_family']
	except KeyError:
		kernel_family = ""
	features.append(kernel_family == "")
	features.append(kernel_family == "Microsoft")
	features.append(kernel_family == "Apple")
	features.append(kernel_family == "Linux")
	features.append(kernel_family == "Embedded")
	features.append(kernel_family == "Tizen")
	features.append(kernel_family == "Blackberry")
	features.append(kernel_family == "Chrome")
	
	try:
		platform = opsys['platform']
	except KeyError:
		platform = ""
	features.append(platform == "")
	features.append("virtual" == platform)
	features.append("vpn" == platform)
	features.append("computer/" in platform)
	features.append("mobile/" in platform)
	features.append("iot/" in platform)
	features.append("network/" in platform)
	features.append("computer/laptop" == platform)
	features.append("computer/desktop" == platform)
	features.append("computer/console" == platform)
	features.append("mobile/phone" == platform)
	features.append("mobile/pad" == platform)
	features.append("mobile/watch" == platform)
	features.append("iot/tv" == platform)
	features.append("iot/assistant" == platform)
	features.append("iot/device" == platform)
	features.append("iot/printer" == platform)
	features.append("iot/phone" == platform)
	features.append("iot/speakers" == platform)
	features.append("network/scanner" == platform)
	features.append("network/router" == platform)

	try:
		flavor = opsys['flavor']
	except KeyError:
		flavor = ""
	features.append(flavor == "")
	features.append(flavor == "Android")
	features.append(flavor == "LuJam")
	features.append(flavor == "Raspberry Pi")
	features.append(flavor == "Nokia")
	features.append(flavor == "Windows")
	features.append(flavor == "Surface")
	features.append(flavor == "WiFi")
	features.append(flavor == "iPod")
	features.append(flavor == "Kindle")
	features.append(flavor == "Sonos")
	features.append(flavor == "Polycomm")
	
	return features


def generate_model(devices):
	global model, operating_systems
	
	os_p = Probability()
	os_l = 0
	for os in operating_systems.values():
		try:
			os_w = math.exp(float(os['osweight']))
		except (KeyError, ValueError):
			os_w = 1

		os_l += os_w
	
	for os in operating_systems.values():
		try:
			os_w = math.exp(float(os['osweight']))
		except (KeyError, ValueError):
			os_w = 1
		
		for m_of in enumerate(opsys_features(os)):
			os_p[Token('M', *m_of)] += os_w / os_l
	
	dev2os_p = Probability()
	dev_l = 0
	for device in devices.values():
		try:
			opsys = operating_systems[device['operating_system']]
		except KeyError:
			continue

		try:
			dev_w = math.exp(float(device['devweight']))
		except (KeyError, ValueError):
			dev_w = 1
		
		dev_l += dev_w
	
	for device in devices.values():
		try:
			opsys = operating_systems[device['operating_system']]
		except KeyError:
			continue
		
		try:
			dev_w = math.exp(float(device['devweight']))
		except (KeyError, ValueError):
			dev_w = 1
		
		for n_df in enumerate(device_features(device)):
			dev2os_p[Token('N', *n_df)] += dev_w / dev_l
	
	dev_l = 0	
	for device in devices.values():
		try:
			opsys = operating_systems[device['operating_system']]
		except KeyError:
			continue
		
		try:
			dev_w = math.exp(float(device['devweight']))
		except (KeyError, ValueError):
			dev_w = 1
		
		dev_l += dev_w
	
	for device in devices.values():
		try:
			opsys = operating_systems[device['operating_system']]
		except KeyError:
			continue
		
		try:
			dev_w = math.exp(float(device['devweight']))
		except (KeyError, ValueError):
			dev_w = 1
		
		for m_of in enumerate(opsys_features(opsys)):
			dev2os_p[Token('M', *m_of)] += dev_w / dev_l
			for n_df in enumerate(device_features(device)):
				dev2os_p[Token('M', *m_of) & Token('N', *n_df)] += dev_w / dev_l
	
	#for key, value in dev2os_p.items():
	#	if value > 1
	#		dev2os_p[key] = 1

	assert(all(0 <= _p <= 1.0000001 for _p in os_p.values()))
	assert(all(0 <= _p <= 1.0000001 for _p in dev2os_p.values()))
	
	
	#os_p = defaultdict((lambda: 0), ((_key, float(_value)) for (_key, _value) in os_p.items()))
	#dev2os_p = defaultdict((lambda: 0), ((_key, float(_value)) for (_key, _value) in dev2os_p.items()))
	
	model = os_p, dev2os_p
	
	return os_p, dev2os_p


def bit_2_int(bits):
	result = 0
	for bit in bits:
		if bit:
			result |= 1
		result <<= 1
	return result


def combine0(qs):
	return sum(qs) / len(qs)


def combine1(qs):
	return 1 - reduce((lambda _x, _y: _x * (1 - _y)), qs, 1)


def combine2(qs):
	if any(_q == 0 for _q in qs):
		return 0
	else:
		return math.exp(sum(math.log(_q) for _q in qs))

def combine3(qs):
	return max(*qs)


def os_dev_weight(opsys, device):
	os_p, dev_p = model
	
	ms = []
	for m_of in enumerate(opsys_features(opsys)):
		ns = []
		for n_df in enumerate(device_features(device)):
			p = (1 - os_p[Token('M', *m_of)]) * dev_p[Token('M', *m_of) | Token('N', *n_df)]
			assert -0.0000001 <= p <= 1.0000001, "P({}) = {}; P({}) = {}; P({}) = {}; P({}) = {};".format(Token('M', *m_of), repr(os_p[Token('M', *m_of)]), Token('N', *n_df), repr(dev_p[Token('N', *n_df)]), Token('M', *m_of) & Token('N', *n_df), repr(dev_p[Token('M', *m_of) & Token('N', *n_df)]), Token('M', *m_of) | Token('N', *n_df), repr(dev_p[Token('M', *m_of) | Token('N', *n_df)]))
			ns.append(p)
		q = combine3(ns)
		ms.append(q)
	r = combine0(ms)
	
	return float(r)


def detect_os_unsorted(device):
	global operating_systems
	for name, opsys in operating_systems.items():
		weight = os_dev_weight(opsys, device)
		if weight:
			yield name, weight


def detect_os(device):
	#result = sorted(detect_os_unsorted(device), key=lambda k: -k[1])
	#print("detected os:", device, result)
	return "???", 1.0


def save_model():
	global model
	
	os_p, dev_p = model
	
	os_pd = {}
	for key, val in os_p.items():
		f = Fraction(val).limit_denominator()
		os_pd[str(key)] = (f.numerator, f.denominator)

	dev_pd = {}
	for key, val in dev_p.items():
		f = Fraction(val).limit_denominator()
		dev_pd[str(key)] = (f.numerator, f.denominator)
	
	return os_pd, dev_pd


def load_model(data):
	global model
	
	os_p, dev_p = data
	
	os_pp = Probability()
	os_pp.update(dict((Token(_key), Fraction(*_val)) for (_key, _val) in os_p.items()))
	
	dev_pp = Probability()
	dev_pp.update(dict((Token(_key), Fraction(*_val)) for (_key, _val) in dev_p.items()))
	
	model = os_pp, dev_pp




if __name__ == '__main__':
	from pathlib import Path
	import json
	
	with Path('model.json').open('r') as fp:
		load_model(json.load(fp))
	
	with Path('opsys.json').open('r') as fp:
		set_os_list(json.load(fp))
	
	device = {'hostname':'android-01'}
	
	print(detect_os(device)[0][0])


if False and __debug__ and __name__ == '__main__':
	operating_systems = {}
	operating_systems['Android'] = {'kernel_family':'Linux'}
	operating_systems['iOS'] = {'kernel_family':'Apple'}
	
	set_os_list(operating_systems)
	
	devices = {}
	devices['00'] = {'hostname':'android-01', 'operating_system':'Android'}
	devices['01'] = {'hostname':'android-02'}
	devices['02'] = {'hostname':'Samsung', 'operating_system':'Android'}
	devices['03'] = {'hostname':'yolo'}
	devices['04'] = {'hostname':'Ann-iPhone', 'operating_system':'iOS'}
	devices['05'] = {'hostname':'Bob-iPad'}
	devices['06'] = {'hostname':'Celina-iPad', 'operating_system':'iOS'}
	devices['07'] = {'hostname':'Dean-MBP', 'operating_system':'iOS'}
	devices['08'] = {'hostname':'android-xx'}
	devices['09'] = {'hostname':'android-yy'}
	devices['10'] = {'hostname':'Samsung643'}
	devices['11'] = {'hostname':''}
	devices['12'] = {'hostname':'Eduard-iPhone'}
	devices['13'] = {'hostname':'Fred-iPad'}
	devices['14'] = {'hostname':'Gigi-iPad'}
	devices['15'] = {'hostname':'Hannah-MBP'}
	
	generate_model(devices)
	
	os_p, dev_p = model
	
	'''
	print()
	print("dev_p:")
	for key, value in dev_p.items():
		print(key, str(value))
	
	print()
	print("os_p:")
	for key, value in os_p.items():
		print(key, str(value))
	'''
	
	print()
	
	device = {'hostname':'Samsung skdlj'}
	#device = {'hostname':'android-jlkj'}
	#device = {'hostname':'iPad-sdfsdf'}
	
	print(hex(bit_2_int(device_features(device))))
	print(hex(bit_2_int(opsys_features(operating_systems['Android']))))
	print(hex(bit_2_int(opsys_features(operating_systems['iOS']))))
	
	def leading_space(s, n):
		return " " * max(n - len(s), 0) + s

	'''
	for n_df in enumerate(device_features(device)):
		print(leading_space(str(dev_p[Token('N', *n_df)]), 5), end=", ")
	print()
	
	for m_of in enumerate(opsys_features(operating_systems['iOS'])):
		print(leading_space(str(1 - os_p[Token('M', *m_of)]), 5), end=", ")
	print()
	'''

	#for n_df in enumerate(device_features(device)):
	#	for m_of in enumerate(opsys_features(operating_systems['iOS'])):
	#		print(leading_space(str(dev_p[Token('N', *n_df) & Token('M', *m_of)]), 5), end=" ")
	#	print()
	
	#quit()
	print()
	
	opsys = operating_systems['Android']
	ms = []
	for m_of in enumerate(opsys_features(opsys)):
		#print(m_of)
		ns = []
		for n_df in enumerate(device_features(device)):
			p = (1 - os_p[Token('M', *m_of)]) * dev_p[Token('M', *m_of) | Token('N', *n_df)]
			#print(os_p[Token('M', *m_of)], dev_p[Token('M', *m_of) | Token('N', *n_df)])
			ns.append(p)
		#print([str(_n) for _n in ns])
		q = combine3(ns)
		ms.append(q)
	#print([float(_m) for _m in ms])
	r = combine0(ms)
	print('Android', float(r))
	
	opsys = operating_systems['iOS']
	ms = []
	for m_of in enumerate(opsys_features(opsys)):
		#print(m_of)
		ns = []
		for n_df in enumerate(device_features(device)):
			p = (1 - os_p[Token('M', *m_of)]) * dev_p[Token('M', *m_of) | Token('N', *n_df)]
			#print(os_p[Token('M', *m_of)], dev_p[Token('M', *m_of) | Token('N', *n_df)])
			ns.append(p)
		#print([str(_n) for _n in ns])
		q = combine3(ns)
		ms.append(q)
	#print([float(_m) for _m in ms])
	r = combine0(ms)
	print('iOS', float(r))



	#print([(_name, float(_weight)) for (_name, _weight) in detect_os({'hostname':'android-zz'})])



'''
if __name__ == '__main__':
	import sys
	from pathlib import Path
	import json
	import csv
	
	if len(sys.argv) == 1:
		print("Usage:", "cat", "sample.csv", "|", sys.argv[0], "model.json", "opsys.json")
		print("sample.csv format:", "\"mac\",\"mac_vendor\",\"dhcp_fingerprint\",\"fingerbank_guess\",\"hostname\"")
		quit()
	
	with Path(sys.argv[1]).open() as fp:
		model = json.load(fp)
		model = tuple(Counter(_entry) for _entry in model)
	
	with Path(sys.argv[2]).open() as fp:
		operating_systems = json.load(fp)

	for (mac, mac_vendor, dhcp_fingerprint, fingerbank_guess, hostname) in csv.reader(sys.stdin):
		device = {'mac_vendor':mac_vendor, 'dhcp_fingerprint':dhcp_fingerprint, 'fingerbank_guess':fingerbank_guess, 'hostname':hostname}
		print(', '.join(os + ':' + format(p, '.4f') for (os, p) in detect_os(device)))
		print(device)
'''

