from flask import Flask, render_template
from flask_ask import Ask, statement, question, request, session, context, convert_errors
import maps
import requests
import os
import traceback

app = Flask(__name__)
ask = Ask(app, "/")

@ask.launch
def launch_skill():
	userid = session.user.userId
	if permissions_check():
		return question(render_template('welcome'))
	else:
		return statement(render_template('permissions_error'))

@ask.intent("GetDirections", convert={'Address':str, 'FinBusiness':str, 'FoodBusiness':str, 'LocalBusiness':str}, mapping={'dest_addr': 'Address', 'dest_fin_bus':'FinBusiness', 'dest_food_bus':'FoodBusiness', 'dest_local_bus':'LocalBusiness'})
def directions(dest_addr, dest_fin_bus, dest_local_bus, dest_food_bus):
	all_inputs=[dest_addr, dest_fin_bus, dest_local_bus, dest_food_bus]
	dest_addr = ''
	for i in all_inputs:
		if i is not None and i is not 'None':
			dest_addr += i + ' '

	if(permissions_check()):
		totals = None
		try:
			totals = maps.add_carbon(maps.find_all_directions(session.attributes['dev_address'], dest_addr))
		except ApiError:
			return question("That is not a valid address, try again!")
		except:
			traceback.print_exc()
			return question("There was an issue with your error, try again!")

		driving_carbon = totals['driving']['carbon']
		driving_carbon_str = "{:.2f}".format(driving_carbon)
		diff_driving_transit = driving_carbon-totals['transit']['carbon']
		diff_driving_transit_str = "{:.2f}".format(diff_driving_transit)

		walking_output = "You will have to walk {distance} miles, which will take about {time}, and save {carbon} pounds of carbon.\nLink: {link}".format(distance=int(totals['walking']['distance']),
																																	time=totals['walking']['time'],
																																	link=maps.encode_url(session.attributes['dev_address'],dest_addr,'walking'),
																																	carbon=totals['driving']['carbon_str'])
		driving_output = "You will drive {distance} miles, which will take about {time}, and save 0 pounds of carbon.\nLink: {link}".format(distance=int(totals['driving']['distance']),
																																	time=totals['driving']['time'],
																																	link=maps.encode_url(session.attributes['dev_address'],dest_addr,'driving'))
		biking_output = "You will have to bike {distance} miles, which will take about {time}, and save {carbon} pounds of carbon.\nLink: {link}".format(distance=int(totals['bicycling']['distance']),
																																		time=totals['bicycling']['time'],
																																		link=maps.encode_url(session.attributes['dev_address'],dest_addr,'bicycling'),
																																		carbon=totals['driving']['carbon_str'])
		transit_output = "Public transit will take about {time} to get to your destination, and save {carbon} pounds of carbon.\nLink: {link}".format(distance=int(totals['transit']['distance']),
																																	time=totals['transit']['time'],
																																	link=maps.encode_url(session.attributes['dev_address'],dest_addr,'transit'),
																																	carbon=diff_driving_transit_str)

		card_output = "{walk}\n{bike}\n{transit}\n{drive}".format(walk=walking_output, bike=biking_output, transit=transit_output, drive=driving_output)

		return statement(render_template('recommendation', address=dest_addr, drivingCarbon=driving_carbon_str, diffDrivingTransit=diff_driving_transit_str)).simple_card(title="Your Greenr Trip to {address}".format(address=dest_addr), content=card_output)

@ask.intent("AMAZON.StopIntent")
def stop():
	return statement(render_template('bye'))

@ask.intent("AMAZON.CancelIntent")
def stop():
	return statement(render_template('bye'))

@ask.intent("AMAZON.HelpIntent")
def stop():
	return statement(render_template('help'))

def get_address(deviceId, consentToken):
	url = "https://api.amazonalexa.com/v1/devices/{deviceId}/settings/address".format(deviceId=deviceId)
	head = {"Authorization": "Bearer {token}".format(token=consentToken)}
	response = requests.get(url, headers=head)
	response = response.json()

	print response

	out = []
	address = ''
	out.append(response['addressLine1'])
	out.append(response['addressLine2'])
	out.append(response['addressLine3'])
	out.append(response['city'])
	out.append(response['stateOrRegion'])
	out.append(response['postalCode'])

	for i in out:
		if i is not None:
			address += i + ', '

	return address

def permissions_check():
	deviceId = None
	consentToken = None
	try:
		deviceId = context.System.device.deviceId
		consentToken = session.user.permissions.consentToken
	except:
		print "first threw"
		traceback.print_exc()
		return False

	if(deviceId is None or consentToken is None):
		print "one was None"
		return False
	else:
		alexa_address = get_address(deviceId, consentToken)
		session.attributes['dev_address'] = alexa_address
		print "added to session"
		return True

	return False

if __name__=='__main__':
	port = int(os.environ.get("PORT", 5000))
	app.run(host='0.0.0.0', port=port)