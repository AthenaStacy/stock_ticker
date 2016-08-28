from flask import Flask,render_template,request,redirect,session
app = Flask(__name__)

import requests
import pandas as pd
import datetime as dt
import numpy as np
import simplejson as json
import urllib2 
import urllib
from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_file
from bokeh.embed import components 

app.question1={}
app.question1['What stock do you want to know about?  \
               Please enter the ticker symbol']=('Ticker symbol')

app.nquestion1=len(app.question1)

app.question2={}
app.question2['What information about that stock would you like?']=('Opening price', \
               'Closing price')

app.question3={}
app.question3['How many previous months of prices would you like?']=('Number of months')

app.secret_key = 'DONTCAREWHATTHISIS'
my_key = 'khszD7FbY99W9haQ6ZZr' #quandl data set api key word
todays_date = dt.date.today()


@app.route('/')
@app.route('/index',methods=['GET', 'POST'])
def index():
	session['question1_answered'] = 0
	session['question2_answered'] = 0
	nquestion1=app.nquestion1
	if request.method == 'GET':
		return render_template('welcome.html',num=nquestion1)
	else:
 		return redirect('/main')

@app.route('/main')
def main():
	if session['question1_answered'] > 0: 
		script, div = get_stock_info()
		if(div != 0):
			return render_template('result.html', script=script, div=div, \
			    ticker=session['ticker_symbol'])
		else:  #found no MATCHES
			return render_template('tryagain.html')
	else:
		return redirect('/next')
 
@app.route('/next',methods=['GET', 'POST'])
def next(): #remember the function name does not need to match the URL
	if request.method == 'GET':
		session['ticker_symbol'] = ''
		session['question1_answered'] = {}
		session['closing'] = 'no'
		session['opening'] = 'no'
		session['length'] = 0

		#for clarity (temp variables)
		n2 = app.nquestion1 - len(app.question1) + 1
		q1 = app.question1.keys()[0] #python indexes at 0
		q2 = app.question2.keys()[0] #python indexes at 0
		q3 = app.question3.keys()[0]

		#this will return the answers corresponding to q
		a1, a2= app.question2.values()[0] 

		return render_template('layout.html',num=n2,question1=q1,question2=q2, \
		                question3=q3, ans1=a1,ans2=a2)
	else:	#request was a POST
		session['question1_answered'] = 1		
		session['ticker_symbol'] = request.form['ticker_symbol']
		session['number_of_months'] = request.form['number_of_months']
		
		x = request.form.getlist('which_price')
		xl = len(x)		
		session['length'] = xl
		for i in range(xl):
			print 'x[i] =', x[i]
			if x[i] == 'open':
				session['opening'] = 'yes'
			if x[i] == 'close':
				session['closing'] = 'yes'
	
		print 'number_of_months =', session['number_of_months']
		print 'session_opening =', session['opening']	
		print 'session_closing =', session['closing']
		print 'session_length =', session['length']
	
	return redirect('/main')


def get_stock_info():

	mb = 1
	try:
		mb = int(session['number_of_months'])
	except ValueError:
		pass  # do nothing!
    	
	if mb < 1:
		mb = 1
	if mb > 10000:
		mb = 10000
		
	start_date = todays_date + pd.DateOffset(months=-mb, days=-1)

	year = str(start_date.year)
	if start_date.month >=10:
		month = str(start_date.month)
	else:
		month = '0' + str(start_date.month)

	if start_date.day >=10:
		day = str(start_date.day)
	else:
		day = '0' + str(start_date.day)

	print 'start_date =', start_date

	#url = https://www.quandl.com/api/v3/datasets/WIKI/GE.json
	#?api_key=khszD7FbY99W9haQ6ZZr&start_date=2016-07-25

	url = 'https://www.quandl.com/api/v3/datasets/WIKI/' \
	       + session['ticker_symbol'] + '.json?' + 'api_key=' \
	       + my_key + '&start_date=' + year + '-' + month + '-' + day
	#print 'url =', url

	r = requests.get(url, auth=('user', 'pass'))
	blerg1, blerg2 = 0,0
	if(r.status_code == 200):
		blerg = 1
	else:
		return(blerg1,blerg2)
		
	text = r.text
	
	#print text
	
	my_df = pd.read_json(text)
	length = len(my_df['dataset']['data'][:])
	c_names = my_df.dataset['column_names']

	datelist = np.arange('1000-02-01', '2016-02-01', dtype='datetime64[D]')
	datelist = datelist[0:length]

	open_price = np.arange(length-1, dtype='float64')
	high_price = np.arange(length-1, dtype='float64')
	low_price = np.arange(length-1, dtype='float64')
	close_price = np.arange(length-1, dtype='float64')

	for i in range(length-1):
		datelist[i] = my_df['dataset']['data'][i][0]
		open_price[i] = my_df['dataset']['data'][i][1]
		high_price[i] = my_df['dataset']['data'][i][2]
		low_price[i] = my_df['dataset']['data'][i][3]
		close_price[i] = my_df['dataset']['data'][i][4]

	#print 'begin bokeh'

	TOOLS = "pan,wheel_zoom,box_zoom,reset"

	plot = figure(tools=TOOLS,
              title='Data from Quandle WIKI set',
              x_axis_label='date',
              x_axis_type='datetime',
              y_axis_label = 'price in $')

	#print 'continue bokeh'

	if(session['closing'] == 'yes'):
		plot.line(datelist, close_price, color='blue', legend = 'closing price')
	if(session['opening'] == 'yes'):
		plot.line(datelist, open_price, color='red', legend = 'opening price')
	script, div = components(plot)

	return(script, div)

if __name__ == "__main__":
	app.run(port=33507)
		
