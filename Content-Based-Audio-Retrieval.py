import os
from fnmatch import fnmatch

import pymongo
from pymongo import MongoClient

from bson.binary import Binary
import pickle 
import numpy as np
import json

from PIL import Image
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
import os
from werkzeug.utils import secure_filename
from io import BytesIO

import matplotlib.pyplot as plt
import librosa
import librosa.display



app = Flask(__name__)


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR=ROOT_DIR+"/static"
COLLECTION_NAME='/audios'
COLLECTION_PATH=STATIC_DIR+COLLECTION_NAME
WAVEFORM_PATH = '/waves/waveplot/'
MFCC_PATH = '/waves/mfcc/'



@app.route("/collection")
def build_colllection():

	pattern = "*.mp3"
	client = MongoClient('localhost', 27017)
	mydb = client['cbar-db']
	audio_collection = mydb["audio-collection-mp3"]
	print('COLLECTION_PATH: ', COLLECTION_PATH)
	counter =0
	for path, subdirs, files in os.walk(COLLECTION_PATH):
		for name in files:
			if fnmatch(name, pattern):
				rel_dir = os.path.relpath(path, COLLECTION_PATH)
				filePath = os.path.join(rel_dir, name)
				print('reldir: ', path)
				print('name: ', name)
				print('build_colllection, filepath: ', filePath)
				fileName = name
				fileUrl='r'+filePath
				print('fileANme: ', fileName)
				print('fileUrl: ', fileUrl)
				query = { "name": fileName}

				if mydb.audio_collection.find(query).count() == 0:
			
					print('--------------------------')
					data, sr = librosa.load(COLLECTION_PATH+'/'+fileName, offset=30, duration=5)
					mfccs=librosa.feature.mfcc(y=data, sr=sr)
					plt.figure(figsize=(12, 4))
					librosa.display.waveplot(data, sr=sr)
					plt.savefig(STATIC_DIR+WAVEFORM_PATH+os.path.splitext(fileName)[0]+'.png')

					plt.figure(figsize=(10, 4))
					librosa.display.specshow(mfccs, x_axis='time')
					plt.colorbar()
					plt.title('MFCC')
					plt.tight_layout()
					# plt.show()
					plt.savefig(STATIC_DIR+MFCC_PATH+os.path.splitext(fileName)[0]+'.png')

					print('------------------------')

					record = {"name": fileName,
					"path" : filePath}

					record['mfccs'] = Binary(pickle.dumps(mfccs, protocol=2), subtype=128 )
					record_id = mydb.audio_collection.insert_one(record)
					
					counter +=1
		print('----len---')
	print(counter)
	return 'collected documents: ' + str(counter)



# UPLOAD_FOLDER = '/home/arj/Downloads'
# ALLOWED_EXTENSIONS = set([ 'mp3'])
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def match(query, testMfcc, topN):
	COLLECTION_DIR = 'audios'
	client = MongoClient('localhost', 27017)
	mydb = client['cbar-db']
	audio_collection = mydb["audio-collection-mp3"]
	distance_list=[]
	for x in mydb.audio_collection.find():
		distance_dict=dict()
		dist = np.linalg.norm(testMfcc- pickle.loads(x['mfccs']))
		print('dist: ', dist)
		distance_dict['distance']=dist
		distance_dict['name']=x['name']
		distance_dict['path']=  '/static' + COLLECTION_NAME+ '/'+(x['name'].split('./')[0])
		distance_dict['waveform']=  '/static' +WAVEFORM_PATH+'/'+ os.path.splitext(x['name'])[0]+'.png'
		distance_dict['mfcc']=  '/static' +MFCC_PATH+'/'+ os.path.splitext(x['name'])[0]+'.png'
		distance_list.append(distance_dict)
	distance_list_sorted = sorted(distance_list, key = lambda i: i['distance'])
	print('---------sorted list ----')
	print(distance_list_sorted)
	if topN < len(distance_list_sorted):
		sorted_subset = [x for _, x in zip(range(15), distance_list_sorted)]
	else:
		sorted_subset=distance_list_sorted
	sorted_subset.append(query)
	return sorted_subset


@app.route('/search', methods=['POST'])
def search():
	file = request.files.get('fileUploaded')
	 # This is your Project Root
	print('rootdir')
	print(ROOT_DIR)
	filename = request.files['fileUploaded'].filename
	filepath = os.path.join(STATIC_DIR+"/tmp/", filename)
	file.save(filepath)
	file.stream.seek(0) # seek to the beginning of file


	data, sr = librosa.load(filepath, offset=30, duration=5)

	plt.figure(figsize=(12, 4))
	librosa.display.waveplot(data, sr=sr)
	file = os.path.splitext(filename)[0]
	# plt.show()
	waveform = STATIC_DIR+"/tmp/"+file+'-waveform.png'

	plt.savefig(waveform)

	mfccs=librosa.feature.mfcc(y=data, sr=sr)

	plt.figure(figsize=(10, 4))
	librosa.display.specshow(mfccs, x_axis='time')
	plt.colorbar()
	plt.title('MFCC')
	plt.tight_layout()
	# # plt.show()
	mfcc = STATIC_DIR+"/tmp/"+file+'-mfcc.png'
	plt.savefig(mfcc)

	query = dict()
	query['name']= filename
	query['path'] = "/static"+"/tmp/"+filename

	query['mfcc']= "/static"+"/tmp/"+file+'-mfcc.png'
	query['waveform'] = "/static"+"/tmp/"+file+'-waveform.png'
	
	sorted_matches = match(query, mfccs, 15)

	print('results without dumps')
	print(len(sorted_matches))
	print('sorted_subset: ', len(sorted_matches))
	print('=======================sorted subset============')
	print(sorted_matches)
	return render_template("searchresults.html", sorted_matches = sorted_matches, mimetype="application/json")
      


@app.route("/")
def index():
	return render_template('index.html')
 
if __name__ == "__main__":
	app.run()