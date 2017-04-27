#api key: AIzaSyCx4ShGYf1BPioZGW1nNPEMKmHpmrggx_w

import googlemaps as maps
from datetime import datetime
import urllib
import requests
import json

api_key= 'AIzaSyCx4ShGYf1BPioZGW1nNPEMKmHpmrggx_w'
gmaps = maps.Client(key=api_key)

def encode_url(start_addr, dest_addr, transp_mode):
	possible_modes = {"driving":'d', "walking":'w', "transit":'r', "bicycling":'b'}

	if not possible_modes.has_key(transp_mode):
		raise TypeError


	options={"saddr": start_addr, "daddr": dest_addr, "dirflg": possible_modes[transp_mode]}
	encoded_options = urllib.urlencode(options)
	url = "https://www.google.com/maps?"+encoded_options
	return short_url(url);

def find_all_directions(start_addr, dest_addr):
	print "start: " + start_addr
	print "dest: " + dest_addr
	possible_modes = ["transit", "driving", "walking", "bicycling"]
	totals = {}
	for i in possible_modes:
		print "mode: " + i
		r = gmaps.directions(start_addr, dest_addr, mode=i)
		meters = r[0]['legs'][0]['distance']['value']
		miles = meters/1609.34
		time = r[0]['legs'][0]['duration']['text']
		totals[i] = {'distance':miles, 'time':time}

	return totals

	# tr = gmaps.directions(start_addr, dest_addr, mode="transit")
	# dr = gmaps.directions(start_addr, dest_addr, mode="driving")
	# wr = gmaps.directions(start_addr, dest_addr, mode="walking")
	# br = gmaps.directions(start_addr, dest_addr, mode="bicycling")

def add_carbon(totals):
	for i in totals:
		totals[i]['carbon'] = carbon_footprint(i, totals[i]['distance'])

	for i in totals:
		totals[i]['carbon_str'] = "{:.2f}".format(totals[i]['carbon'])

	return totals

def carbon_footprint(type, distance_miles):
	outputs = {'driving':0.96, 'transit':0.64, 'walking':0.00, 'bicycling':0.00}
	return outputs[type]*distance_miles

def short_url(long_url):
	url = 'https://www.googleapis.com/urlshortener/v1/url'
	head = {'Content-type':'application/json'}
	parameters = {'key':api_key}
	data = {'longUrl':long_url}
	data = json.dumps(data)

	response = requests.post(url, params=parameters,headers=head, data=data)
	response = response.json()

	return response['id']