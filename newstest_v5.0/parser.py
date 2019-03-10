#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
import requests
from bs4 import BeautifulSoup as bs
import os
import codecs
import sys
import subprocess
import pymorphy2
def Lemm(word):
	morph = pymorphy2.MorphAnalyzer()
	p = morph.parse(word)[0]
	return p.normal_form


def GetTriplets(data_path, target_folder):
	file_list = [file for file in os.listdir(data_path) if os.path.isfile(data_path + '/' + file)]
	for file in file_list:
		#print file
		processed_centencens = []
		sentence = []
		with codecs.open(target_folder + '/' + file[0:-6] + '.txt', 'w', 'utf-8') as f:
			for line in codecs.open(data_path + '/' + file, 'r', 'utf-8'):
				if len(line) == 1:
					processed_centencens.append(sentence)
					sentence = []
				else:
					word = line.split("\t")
					sentence.append(word)

			deps = []
			for sentence in processed_centencens:
				s = u''
				for line in sentence:
					s += u"\t".join(line) + u'\n'
				deps.append(s)

			for sent_dep in deps:
				verbs = {}
				appos = {}
				adjects = {}
				sent_dep = [line for line in sent_dep.split('\n') if line]
				for t in sent_dep:
					#print t
					splt = t.split('\t')
					if splt[3] == 'VERB':
						verbs[splt[0]] = ['0', Lemm(splt[1]), '0']
					elif splt[3] == 'ADJ':
						#print('***' + deps[7] + '***')
						if sent_dep[int(splt[6])-1].split('\t')[3] == 'NOUN':
							adjects[splt[0]] = [Lemm(sent_dep[int(splt[6])-1].split('\t')[1]), '0', Lemm(splt[1])]

				for t in sent_dep:
					splt = t.split('\t')
					if splt[7] == 'nsubj':
						if splt[6] in verbs:
							verbs[splt[6]][0] = Lemm(splt[1])
					elif splt[7] == 'dobj':
						if splt[6] in verbs:
							verbs[splt[6]][2] = Lemm(splt[1])
					elif splt[7] == 'appos':
						appos[splt[0]] = [Lemm(splt[1]), '0', Lemm(sent_dep[int(splt[6])-1].split('\t')[1])]

				for key in verbs:
					f.write(' '.join(verbs[key]) + '\n')
				for key in appos:
					f.write(' '.join(appos[key]) + '\n')
				for key in adjects:
					f.write(' '.join(adjects[key]) + '\n')


def DocksToUCI(data_path):
	from BagOfWordsModel import BagOfWordsModel as BOW
	file_list = [file for file in os.listdir(data_path) if os.path.isfile(data_path + '/' + file)]
	my_dict = {}
	for i, file in enumerate(file_list):
		f = codecs.open(data_path + '/' + file, mode = 'r', encoding = 'utf-8')
		my_dict[file] = f.readline()
		f.close()
	bow = BOW(my_dict)
	bow.to_uci()

def PackToUCI(file_txt):
	from BagOfWordsModel import BagOfWordsModel as BOW
	my_dict = {}
	my_file = codecs.open(file_txt, mode ='r', encoding = 'utf-8')
	file_text = my_file.read().splitlines()
	file_text = [i for i in file_text if (i and '|mark' not in i)]
	#print file_text[0].split('"')[1]
	for i,state in enumerate(file_text):
		my_dict[str(i)] = state[state.find('"') : ]
		#my_dict[str(i)] = file_text[i].split('"')[0]
	my_file.close()
	bow = BOW(my_dict)
	bow.to_uci()

def ClearDocksToTriplets(cdf, tdf):
	file_list = [file for file in os.listdir(cdf) if os.path.isfile('data' + '/' + file)]
	for file in file_list:
		command = 'cat ' + cdf + '/' + file + '|docker run --rm -i inemo/syntaxnet_rus > ' + tdf + '/' +  file[0:-4] +'.conll'
		#subprocess.call('cd /home/gernar', shell = True)
		subprocess.call(command, shell = True)
		#print command

def GetStates(sites):
	rf = open(sites, 'r')
	lines = rf.read().splitlines() 
	for i, line in enumerate(lines):
		#print line
		url = line
		html = requests.get(url).text
		soup = bs(html, 'html.parser')
		bodies = soup.find_all('div', class_ = ['story-body__inner', 'GeneralMaterial-article', 'body-content'])
		#print type(body)
		for body in bodies:
			tags = body.find_all(['p', 'h1', 'h2', 'h3'])
			wf = open('data/' + str(i)+'.txt', 'w')
			text = ''
			for tag in tags:
				text+=tag.text
		#print text
		wf.write(text.encode('utf-8'))

		wf.close()
	rf.close()

#PackToUCI('data/lnr_dnr_labelled.txt')

def PackToDocks(file_txt, target_folder):
	my_file = codecs.open(file_txt, mode ='r', encoding = 'utf-8')
	file_text = my_file.read().splitlines()
	text = [i for i in file_text if (i and '|mark' not in i)]
	#print file_text[0].split('"')[1]
	class_list = [int(i[6:]) for i in file_text if '|mark' in i]
	#print class_list
	for i,state in enumerate(text):
		f = codecs.open(target_folder + '/d_' + str(i) + '.txt', mode='w', encoding = 'utf-8')
		f.write(state[state.find('text')+5:])
		f.close()

	my_file.close()
	return class_list

def ClearText(df, cdf):
	file_list = [file for file in os.listdir(df) if os.path.isfile(df + '/' + file)]
	for file in file_list:
		f = codecs.open(df + '/' + file, 'r', 'utf-8')
		text = f.read()
		text = text.replace('. ', '.\n').replace('.', ' .')
		text = text.replace('! ', '!\n').replace('!', ' !')
		text = text.replace(',', ' ,')
		text = text.replace(':', ' :')
		text = text.replace('(', '( ')
		text = text.replace(')', ' )')
		text = text.replace('; ', ' ;\n')

		text = text.replace('"', ' " ')
		text = text.replace('\'',' \' ')

		text = text.replace(u'—', u' — ')
		f.close()
		f = codecs.open(cdf + '/' + file, 'w', 'utf-8')
		f.write(text)
		f.close()

def TripletsToVW(data_path, vw_file):
    file_list = [file for file in os.listdir(data_path) if os.path.isfile(data_path + '/' + file)]
    wf = codecs.open(vw_file, 'w', 'utf-8')
    file_list.sort(key = lambda x: int(x[2:-4]))
    for file in file_list:
        objects = {}
        subjects = {}
        with codecs.open(data_path + '/' + file, 'r', 'utf-8') as f:
            lines = f.read().splitlines()
            for line in lines:
                line = line.split(' ')
                if line[0] in subjects:
                    subjects[line[0]] += 1
                else:
                    subjects[line[0]] = 1
                if line[2] in objects:
                    objects[line[2]] += 1
                else:
                    objects[line[2]] = 1
        subj = [key + ':' + str(subjects[key]) for key in subjects if key != '0']
        obj = [key + ':' + str(objects[key]) for key in objects if key != '0']
        string = u'{0} |@subjects {1} |@objects {2}'.format(file[2:-4], u' '.join(subj), u' '.join(obj))
        wf.write(string + '\n')
        #print string
    wf.close()



#MakeUCI('data')
#class_list = PackToDocks('trump_labelled.txt', 'data')
'''ClearText(df = 'data', cdf = "clear_data")
ClearDocksToTriplets('clear_data', 'processed_data')
GetTriplets( data_path = 'processed_data', target_folder ='triplets')'''
#TripletsToVW('triplets', 'artm_model/vw.trip.txt')


'''with open('artm_model/msg.txt', 'r') as f:
	cluster_list = list(map(int, f.read().splitlines()))

PW = 0
counter = 0
for i, x in enumerate(class_list):
	for j, y in enumerate(class_list):
		if x == y:
			counter += 1
			PW += int(cluster_list[i] == cluster_list[j])

print PW/counter

print cluster_list
print '********************************************************************'
print class_list'''
