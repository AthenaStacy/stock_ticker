from flask import Flask,render_template,request,redirect,session
app = Flask(__name__)

import pandas as pd
import datetime
import numpy as np
from scipy import spatial

nreturn = 10 #number of similar songs to return

app.question1={}
app.question1['What is your favorite song or artist?']=('Song','Artist')

app.nquestion1=len(app.question1)

app.secret_key = 'DONTCAREWHATTHISIS'

@app.route('/')
@app.route('/index',methods=['GET', 'POST'])
def index():
	session['question1_answered'] = 0
	nquestion1=app.nquestion1
	if request.method == 'GET':
		return render_template('welcome.html',num=nquestion1)
	else:
 		return redirect('/main')

@app.route('/main')
def main():
	if session['question1_answered'] > 0:
		which_way = song_check()  ##function to check for song in database##
		if(which_way == 1):
			find_similar()   ##function to find similar songs##
			return render_template('result.html', \
							   input_artist=session['artist_name'],\
		                       input_song=session['song_name'], \
	                           input_date=session['date'], \
		                       input_sent=session['sentiment'], \
		                       input_lex=session['lexdiv'], \
							   artist=session['result']['artist_name'], \
		                       track=session['result']['track_name'], \
							   date=session['result']['date'], \
							   lyricsim=session['result']['dist3'], \
		                       sentiment=session['result']['compound_sentiment'], \
							   lexdiv=session['result']['lex_diversity'])
		if(which_way == 2):  #found no MATCHES
			return render_template('tryagain.html')
		if(which_way == 3):  #got an artist, now need to list their songs
			return redirect('/pickasong')
		if(which_way == 4):  #found multiples songs with that title
			return redirect('/disambiguate')
	else: 
		return redirect('/next')

 
@app.route('/next',methods=['GET', 'POST'])
def next(): #remember the function name does not need to match the URL
	if request.method == 'GET':
		session['song_or_artist'] = ''
		session['song_name'] = ''
		session['artist_name'] = ''
		session['question1_answered'] = 0
		#for clarity (temp variables)
		n2 = app.nquestion1 - len(app.question1) + 1
		q2 = app.question1.keys()[0] #python indexes at 0
		#this will return the answers corresponding to q
		a1, a2= app.question1.values()[0] 
		return render_template('layout2.html',num=n2,question=q2,ans1=a1,ans2=a2)
	else:    #request was a POST
		session['question1_answered'] = 1
		session['song_name'] = request.form['song_name']
		session['artist_name'] = request.form['artist_name']
		session['song_or_artist'] = request.form['answer_from_layout2']
	return redirect('/main')

 
@app.route('/pickasong',methods=['GET', 'POST'])
def pickasong(): #remember the function name does not need to match the URL
	if request.method == 'GET':
		return render_template('pickasong.html',song_list=session['song_list'])
	else:    #request was a POST
		session['song_or_artist'] = 'Both'
		session['song_name'] = session['song_list'][str(request.form['song_pick'])]
	return redirect('/main')


@app.route('/disambiguate',methods=['GET', 'POST'])
def disambiguate(): #remember the function name does not need to match th eURL
	if request.method == 'GET':
		return render_template('disambiguate.html', match_song=session['match_song'],  \
		                                            match_artist=session['match_artist'], \
		                                            match_date = session['match_date'])
	else:    #request was a POST
		session['song_or_artist'] = 'Both'
		session['song_name'] = session['match_song'][str(request.form['artist_pick'])]
		session['artist_name'] = session['match_artist'][str(request.form['artist_pick'])]
 	return redirect('/main')
 


def song_check():
	match = {}
	if(session.get('song_or_artist') == 'Both'):
		return(1)	

	#read df from pickle file
	#lyrics_df = pd.read_pickle('CleanedLyricsDF_MaxRank_100')
	lyrics_df = pd.read_pickle('LyricsDF_with_BoW_tdif_sparse')
	
	if(session.get('song_or_artist') == 'Artist'):
		artist_i_like = session['artist_name']
		match = lyrics_df[lyrics_df['artist_name']==artist_i_like]

	if(session.get('song_or_artist') == 'Song'):
		song_i_like = session['song_name']
		match = lyrics_df[lyrics_df['track_name']==song_i_like]

	if len(match)==1 and session.get('song_or_artist') == 'Song':  #Found one matching song!!
		session['artist_name'] = lyrics_df[lyrics_df['track_name']==song_i_like].artist_name.values[0]
		return(1)

	if len(match)==0:  #Found NO matches
		return(2)

	if(session['song_or_artist'] == 'Artist'): #Got an artist, now need to get their songs
		session['song_list']={}
		song_list = lyrics_df[lyrics_df['artist_name']==artist_i_like]
		song_list = song_list.reset_index()
		for x in range(len(song_list['track_name'])):
			session['song_list'][x] = song_list['track_name'][x]
		return(3)

	if len(match)>0 and session['song_or_artist'] == 'Song':  #Found multiple songs
		session['match_artist'] = {}
		session['match_song'] = {}
		session['match_date'] = {}
		match = lyrics_df[lyrics_df['track_name']==song_i_like]
		match = match.reset_index()
		match['date'] = match['date'].apply(lambda x: x.date())
		for x in range(len(match['track_name'])):
			session['match_song'][x] = match['track_name'][x]
			session['match_artist'][x] = match['artist_name'][x]
			session['match_date'][x] = match['date'][x]
		return(4)

def find_similar():
	#lyrics_df = pd.read_pickle('CleanedLyricsDF_MaxRank_100')
	lyrics_df = pd.read_pickle('LyricsDF_with_BoW_tdif_sparse')
		
	CosDis2 = pd.read_pickle('CosDis_tfidf_reduced')
	CosDis2 = CosDis2.as_matrix()
	
	song_i_like = session['song_name']
	artist_i_like = session['artist_name']
	
	#get date of inputted song
	input_date=lyrics_df[lyrics_df['track_name']==song_i_like].date.values[0]
	#input_date = input_date.astype('datetime64[D]')
	session['date'] = datetime.datetime.strptime(str(input_date).split('.',1)[0],'%Y-%m-%dT%H:%M:%S')

	#find songs with similar sentiment
	sentiment = lyrics_df[lyrics_df['track_name']==song_i_like].compound_sentiment.values[0]
	lyrics_df['dist1'] = lyrics_df.compound_sentiment.map((lambda x: abs(sentiment - x)))	
	session['sentiment'] = sentiment
	
	#define similarity as diff between your song's lexical diversity & that of other songs
	lex = lyrics_df[lyrics_df['track_name']==song_i_like].lex_diversity.values[0]
	lyrics_df['dist2'] = lyrics_df.lex_diversity.map((lambda x: abs(lex - x)))
	session['lexdiv'] = lex

	pd.options.mode.chained_assignment = None  # default='warn'

	#determine which recent song has most similarity in lyrics
	lyrics_recent = lyrics_df[lyrics_df['date']>datetime.date(2013,1,1)]
	lyrics_recent = lyrics_recent.reset_index()
	del lyrics_recent['index']
	
	my_pick = lyrics_df[lyrics_df['track_name']==song_i_like]
	index1 =  my_pick[my_pick['artist_name']==artist_i_like].index

	lyrics_recent['dist3'] = 2.0
	num_recent_songs = len(lyrics_recent)
	for j in range(num_recent_songs):
		lyrics_recent['dist3'].iloc[j] = CosDis2[index1, j]

 	lyrics_recent['dist_tot'] = lyrics_recent['dist1'] + lyrics_recent['dist2'] + lyrics_recent['dist3']
 	
	#recommend nreturn songs based on sum of cosine dist, sentiment dist, and  lexical density dist
	result = lyrics_recent.sort_values('dist_tot')[:nreturn]
 	result = result.reset_index()
 
 	result['date'] = result['date'].apply(lambda x: x.date())
	
	resulto = {'artist_name':{}, 'track_name':{}, 'date':{}, 'dist3':{}, 'compound_sentiment':{}, 'lex_diversity':{}}
	for x in range(0,nreturn):
 		resulto['artist_name'][x] = result['artist_name'][x]
 		resulto['track_name'][x] = result['track_name'][x]
 		resulto['date'][x] = result['date'][x]
 		resulto['dist3'][x] = 1-result['dist3'][x]
 		resulto['compound_sentiment'][x] = result['compound_sentiment'][x]
 		resulto['lex_diversity'][x] = result['lex_diversity'][x]
	session['result'] = resulto

def find_similar_sentiment():
    #lyrics_df = pd.read_pickle('CleanedLyricsDF_MaxRank_100')
    lyrics_df = pd.read_pickle('LyricsDF_with_BoW_tdif_sparse')

    song_i_like = session['song_name']
    artist_i_like = session['artist_name']

    #get date of inputted song
    input_date=lyrics_df[lyrics_df['track_name']==song_i_like].date.values[0]
    input_date = input_date.astype('datetime64[D]')
    session['date'] = datetime.datetime.strptime(str(input_date).split('.',1)[0],'%Y-%m-%dT%H:%M:%S')

    #find songs with similar sentiment
    sentiment = lyrics_df[lyrics_df['track_name']==song_i_like].compound_sentiment.values[0]
    session['sentiment'] = sentiment

    #define similarity as diff between your song's lexical diversity & that of other songs
    lex = lyrics_df[lyrics_df['track_name']==song_i_like].lex_diversity.values[0]
    session['lexdiv'] = lex

    pd.options.mode.chained_assignment = None  # default='warn'
    
    
    # now get the euclidean distance between
    point = np.atleast_2d([lex,sentiment])
    feat_array = lyrics_df.as_matrix(columns=['lex_diversity','compound_sentiment'])
    a = feat_array #(note can make this 3d if want to add lyrical similarity)
    b = point #(note can make this 3d if want to add lyrical similarity)
    dist = spatial.distance.cdist(a,b) # pick the appropriate distance metric
    lyrics_df['dist_total'] = dist
    
    #determine which recent song has most similarity in lyrics
    lyrics_recent = lyrics_df[lyrics_df['date']>datetime.date(2013,1,1)]
    lyrics_recent = lyrics_recent.reset_index()
    del lyrics_recent['index']
    
    my_pick = lyrics_df[lyrics_df['track_name']==song_i_like]
    index1 =  my_pick[my_pick['artist_name']==artist_i_like].index


    #recommend nreturn songs based on distance in 2d (sentiment & lexical density) space
    result = lyrics_recent.sort_values('dist_total')[:nreturn]
    result = result.reset_index()
    #lyrics_df[['lex_diversity','compound_sentiment','euc_dist12']].head()
    #result2[['track_name','artist_name','euc_dist12',\
    #    'dist1','dist2']]

    result['date'] = result['date'].apply(lambda x: x.date())

    resulto = {'artist_name':{}, 'track_name':{}, 'date':{}, 'dist_total':{}, 'compound_sentiment':{}, 'lex_diversity':{}}
    for x in range(0,nreturn):
        resulto['artist_name'][x] = result['artist_name'][x]
        resulto['track_name'][x] = result['track_name'][x]
        resulto['date'][x] = result['date'][x]
        resulto['dist_total'][x] = result['dist_total'][x]
        resulto['compound_sentiment'][x] = result['compound_sentiment'][x]
        resulto['lex_diversity'][x] = result['lex_diversity'][x]
    session['result'] = resulto
    #return resulto

def find_similar_words():
    #lyrics_df = pd.read_pickle('CleanedLyricsDF_MaxRank_100')
    lyrics_df = pd.read_pickle('LyricsDF_with_BoW_tdif_sparse')

    CosDis2 = pd.read_pickle('CosDis_tfidf_reduced')
    CosDis2 = CosDis2.as_matrix()

    song_i_like = session['song_name']
    artist_i_like = session['artist_name']
    
    #get date of inputted song
    input_date=lyrics_df[lyrics_df['track_name']==song_i_like].date.values[0]
    input_date = input_date.astype('datetime64[D]')
    session['date'] = datetime.datetime.strptime(str(input_date).split('.',1)[0],'%Y-%m-%dT%H:%M:%S')

    pd.options.mode.chained_assignment = None  # default='warn'

    #determine which recent song has most similarity in lyrics
    lyrics_recent = lyrics_df[lyrics_df['date']>datetime.date(2013,1,1)]
    lyrics_recent = lyrics_recent.reset_index()
    del lyrics_recent['index']

    my_pick = lyrics_df[lyrics_df['track_name']==song_i_like]
    index1 =  my_pick[my_pick['artist_name']==artist_i_like].index

    lyrics_recent['dist3'] = 2.0
    num_recent_songs = len(lyrics_recent)
    for j in range(num_recent_songs):
        lyrics_recent['dist3'].iloc[j] = CosDis2[index1, j]

    #recommend nreturn songs based on sum of cosine dist, sentiment dist, and  lexical density dist
    result = lyrics_recent.sort_values('dist3')[:nreturn]
    result = result.reset_index()

    result['date'] = result['date'].apply(lambda x: x.date())

    resulto = {'artist_name':{}, 'track_name':{}, 'date':{}, 'dist3':{}}
    for x in range(0,nreturn):
        resulto['artist_name'][x] = result['artist_name'][x]
        resulto['track_name'][x] = result['track_name'][x]
        resulto['date'][x] = result['date'][x]
        resulto['dist3'][x] = 1-result['dist3'][x]
    session['result'] = resulto
    #return resulto

 
if __name__ == "__main__":
	app.run(port=33508)
		
