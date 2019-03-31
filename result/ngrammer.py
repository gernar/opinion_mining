# -*- coding: utf-8 -*-
"""
Created on Fri Dec  4 13:31:04 2015

@author: aromanenko
"""

import re
import json
import numpy as np

class NGrammer(object):
    _phrase2freq = {}
    _delimiters = None
    _delimiters_regex = None
    _lengthInWords = 0
    
    def __init__(self):
        self._phrase2freq = {}
        self._delimiters = {}
        self._delimiters_regex = []
        self._lengthInWords = 0

    @property
    def delimiters(self):
        return self._delimiters
        
    @delimiters.setter
    def delimiters(self, value):
        self._delimiters = value

    @property
    def delimiters_regex(self):
        return self._delimiters_regex
        
    @delimiters_regex.setter
    def delimiters_regex(self, value):
        self._delimiters_regex = [re.compile(p) for p in value]

    @property
    def lengthInWords(self):
        return self._lengthInWords

    @lengthInWords.setter
    def lengthInWords(self, value):
        self._lengthInWords = value

    def frequentPhraseMining(self, document_list, threshhold, max_ngramm_len=10):
        """ Function for collecting phrases and its frequencies"""
        n = 1
        A = {}
        for doc_id, doc in enumerate(document_list):
            A[doc_id] = { n : range(len(doc)-1) }
            for w in doc:
                self._phrase2freq.setdefault(w,0)
                self._phrase2freq[w] += 1
        D = set(range(len(document_list)))
        while D:
            n += 1
            if n > max_ngramm_len:
                break
            to_remove = []
            for doc_id in D:
                doc = document_list[doc_id]
                A[doc_id][n] = []
                for i in A[doc_id][n-1]:
                    if n == 2:
                        flag = False
                        flag2 = False
                        if doc[i] in self._delimiters:
                            flag = True
                        for p in self._delimiters_regex:
                            if re.match(p,doc[i]):
                                flag2 = True
                                break
                        if not flag2:
                            self._lengthInWords += 1
                        if flag or flag2:
                            continue
                    ngram = u'_'.join([doc[i+j] for j in range(n-1)])
                    if self._phrase2freq.get(ngram,threshhold-1) >= threshhold:
                        A[doc_id][n] += [i]
                if A[doc_id][n]:
                    A[doc_id][n].remove(A[doc_id][n][-1])
                if not A[doc_id][n]:
                    to_remove += [doc_id]
                else:
                    for i in A[doc_id][n]:
                        if i+1 in A[doc_id][n]:
                            ngram = u'_'.join([doc[i+j] for j in range(n)])
                            self._phrase2freq.setdefault(ngram,0)
                            self._phrase2freq[ngram] += 1
            for r in to_remove:
                D.remove(r)

    def _significanceScore(self, ngramm1, ngramm2):
        mu0 = float(self._phrase2freq.get(ngramm1,0)*
                    self._phrase2freq.get(ngramm2,0))
        mu0 /= self._lengthInWords
        f12 = float(self._phrase2freq.get(ngramm1+u'_'+ngramm2,0))
        if f12:
            return (f12-mu0)/np.sqrt(f12)
        else:
            return 0
    
    def ngramm(self, token_list, threshhold, indexes=[]):
        H = []
        res = [[i] for i in range(len(token_list))]
        for i in range(len(res)-1):
            p1 = u'_'.join([token_list[w_i] for w_i in res[i]])
            p2 = u'_'.join([token_list[w_i] for w_i in res[i+1]])
            score = self._significanceScore(p1, p2)
            H += [score]
        while len(res) > 1:
            Best = max(H)
            best_ind = H.index(Best)
            if Best > threshhold:
                new_res = res[:best_ind]
                new_res += [res[best_ind]+res[best_ind+1]]
                new_res += res[best_ind+2:]
                
                if best_ind == 0:
                    new_H = []
                else:
                    new_H = H[:best_ind-1]
                    p1 = u'_'.join([token_list[w_i] for w_i in new_res[best_ind-1]])
                    p2 = u'_'.join([token_list[w_i] for w_i in new_res[best_ind]])
                    new_H += [self._significanceScore(p1,p2)]
                if best_ind != len(new_res)-1:                    
                    p1 = u'_'.join([token_list[w_i] for w_i in new_res[best_ind]])
                    p2 = u'_'.join([token_list[w_i] for w_i in new_res[best_ind+1]])
                    new_H += [self._significanceScore(p1,p2)]
                new_H += H[best_ind+2:]
                H = new_H
                res = new_res
            else:
                break
        ngrammed_doc = []
        for ngramm_ind in res:
            ngrammed_doc.append(u'_'.join([token_list[x] for x in ngramm_ind]))

        new_indexes = []
        if indexes:
            for i, ngramm_ind in enumerate(res):
                new_indexes += []
                start_ind = indexes[2*ngramm_ind[0]]
                length = indexes[2*ngramm_ind[-1]] + indexes[2*ngramm_ind[-1]+1] - start_ind
                new_indexes += (start_ind,length)

        return ngrammed_doc, new_indexes
        
    def removeDelimiters(self, ngramm_list, indexes=[]):
        new_list = []
        new_indexes = []
        for i, w in enumerate(ngramm_list):
            if w in self._delimiters:
                continue
            flag = False
            for ptrn in self._delimiters_regex:
                if re.match(ptrn,w):
                    flag = True
                    break
            if flag:
                continue
            new_list.append(w)
            if indexes:
                new_indexes += (indexes[2*i],indexes[2*i+1])
        return new_list, new_indexes
        
    def saveAsJson(self,filename, with_delimiters=False):
        to_save = {u'lengthInWords':self._lengthInWords,
                   u'phrase2freq':self._phrase2freq}
        if (with_delimiters):
            to_save[u'delimiters'] = self._delimiters
            to_save[u'delimiters_regex'] = [x.pattern for x in self._delimiters_regex]
        with open(filename,'w') as fp:
            json.dump(to_save,fp)

    def loadFromJson(self,filename, with_delimiters=False):
        with open(filename,'r') as fp:
            loaded = json.load(fp)
        self._lengthInWords = loaded[u'lengthInWords']
        self._phrase2freq = loaded[u'phrase2freq']
        if (with_delimiters):
            self._delimiters = loaded[u'delimiters']
            self._delimiters_regex = [re.compile(p) for p in loaded[u'delimiters_regex']]
            

if __name__ == "__main__":
    
    def loadFileAsStringArray(filename, empty_strings=False):
        content = []
        f = open(filename,'r')
        for line in f:
            line = line.strip('\r\n\0')
            if not empty_strings and len(line) == 0:
                continue
            content.append(line)
        f.close()
        return content
    
    corpora = []
#    filename = './../postnauka/lemm_comparison/pymorphy/pn_.unigram.txt'
#    filename = './../mup/data/stemm_lemm/stemm/balanced/mup.ru.txt'
    filename = '/home/aromanenko/smaug/home/python/multilang/mup/data_ngramm/pymorphy/balanced/mup.ru.txt'
    for l in loadFileAsStringArray(filename):
        corpora += [l.decode('utf-8').split(' ')]
    
    delimiters = {}
    for w in loadFileAsStringArray('../tests/Stopwords-ru.txt'):
        delimiters.setdefault(w.decode('utf-8'),1)
    delimiters_regex = [u'[^a-zа-яё ]+']
    
    ng = NGrammer()
    ng.delimiters = delimiters
    ng.delimiters_regex = delimiters_regex
    ng.frequentPhraseMining(corpora,3,10)
    
    ngramm_freq = {}
    for doc in corpora:
        res = ng.removeDelimiters(ng.ngramm(doc,3.1))
        for ngramm in res:
            l = ngramm.count(u' ') + 1
            ngramm_freq.setdefault(l,{})
            ngramm_freq[l].setdefault(ngramm,0)
            ngramm_freq[l][ngramm] += 1
            
    with open('freq_mup.txt','w') as f:
        for n in ngramm_freq:
            f.write(str(n)+'-gramm\n')
            for el in sorted(ngramm_freq[n].items(),key=lambda x: x[1])[::-1]:
                f.write('{:<16} {}\n'.format(el[1],el[0].encode('utf-8')))
    ng.saveAsJson('ngrammer_mup.txt',True)
    
    doc = corpora[310]
    doc = ng.ngramm(doc,2)
    doc = ng.removeDelimiters(doc)
#    doc = ng.removeDelimiters(doc)
