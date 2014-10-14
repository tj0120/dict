#!/bin/env python

import socket
import io
import os
import csv
import re
from struct import *
from os import SEEK_SET,SEEK_CUR,SEEK_END

wordCLASS = ('n','adj','v','adv')

def getString(f, start, maxlen = 4096):
    rets = b''
    f.seek(start,SEEK_SET)
    j=maxlen
    i=0
    while True:
        val = f.read(1)  
        if (not val):
            break
        if (val==b'\x00'):
            break
        rets += val
        i += 1
        maxlen -= 1
        if (not maxlen):
            break
    #print('size=%s,read=%s' % (j,i))
    return rets;

def getValue(f, l=4):
    if (l==3):
        val,=unpack('>L',b'\x00'+f.read(3))
    elif (l==1):
        val,=unpack('B',f.read(1))
    else:
        val,=unpack('>L',f.read(4))
    return val

def getDictRecordTM(f,offset,size):
    word_1_data_1_type,word_1_data_1_data,word_1_data_2_type,word_1_data_2_data = None,None,None,None
    f.seek(offset,SEEK_SET)
    word_1_data_1_type,=unpack('B',f.read(1))
    if word_1_data_1_type:
        word_1_data_1_data = f.read(size)
    return (word_1_data_1_type,word_1_data_1_data)

def getDictRecord(f,offset,size):
    word_1_data_1_type,word_1_data_1_data,word_1_data_2_type,word_1_data_2_data = None,None,None,None
    f.seek(offset,SEEK_SET)
    word_1_data_1_type,=unpack('B',f.read(1))
    if word_1_data_1_type:
        word_1_data_1_data = getString(f,offset,size)
    return (word_1_data_1_type,word_1_data_1_data)


def getIdxRecord(f,p1):
    key,offset,size = None,None,None
    key = getString(f,p1)
    if key:
        offset = getValue(f)
        size = getValue(f)
        #print('size=%s' % size)
    return (key,offset,size)


def getIndex(fn):
    fnIdx = fn + '.idx'
    f = open(fnIdx,'rb')
    p1=0
    end = os.fstat(f.fileno()).st_size
    mydict={}
    while True:
        key,offset,size = getIdxRecord(f,p1)
        if (key):
            if key in mydict:
                #print('Multi Record!')
                mydict[key] = mydict[key]+[(offset,size)]
            else:
                mydict[key]=[(offset,size)]
        if (p1 >= end-8):
            break
        p1 += len(key) + 9
    return mydict

def getDict(fn):
    myIdx = getIndex(fn)    
    fnDict = fn + '.dict'
    myDD = {}
    fDict = open(fnDict,'rb')
    #print(os.fstat(fDict.fileno()).st_size)
    for key,val in myIdx.items():
        #print(key,'=',val)
        for i in val:
            word_1_data_1_type,word_1_data_1_data = getDictRecord(fDict,i[0],i[1])
            if key in myDD:
                v = word_1_data_1_data.decode('utf8').strip()
                v = v.split('\n')
                v = [vi.strip() for vi in v]
                v = list(filter(lambda x: x!='',v))
                s = myDD[key][1:]+v
                myDD[key]=[key.decode('utf8')] + s
                #print(myDD[key])
            else:
                v = word_1_data_1_data.decode('utf8').strip()
                v = v.split('\n')
                v = [vi.strip() for vi in v]
                v = list(filter(lambda x: x!='',v))
                myDD[key]=[key.decode('utf8')] + v
            #print(key.decode('utf8') , word_1_data_1_data.decode('utf8'))
    return myDD

def write2csv(fn,dd):
    f = open(fn+'.csv','w', newline = '')
    writer = csv.writer(f)
    for key,val in dd.items():
        writer.writerow(val)

def extraYB(v):
    rc = re.compile(r"/.*?[^<]/",re.U)
    r1 =  rc.search(v[1])
    if (r1):
        rm = r1.group()
    else:
        rm = ' '
    return rm
    
def postProcess_oxford(pdict):
    def sepYB(v):
        rc = re.compile(r"/.*?[^<]/",re.U)
        r1 =  rc.search(v[1])
        if (r1):
            rm = r1.group()
            if (';' in rm):
                v1 = rc.split(v[1])[1:]
                #print('v1=',v1)
                v1.insert(0,rm)
            else:
                v1=['']+v[1:]+['']
        else:
            v1=['']+v[1:]+['']
        return [i.strip() for i in v1]
    k1=list(pdict.keys())
    for k in k1:
        v1 = myDict1[k]
        yb = sepYB(v1)
        pdict[k] = v1[:1]+yb
    return pdict

def postProcess_fccf(pdict):
    def sepYB(v):
        rc = re.compile(u'\xe9\x9f\xb3\xe6\xa0\x87\xef\xbc\x9a\\[.*?\\]',re.U)
        r1 =  rc.search(v[1])
        if (r1):
            rm = r1.group()
            v1 = rc.split(v[1])[1:]
            print('v1=',v1)
        else:
            v1=v.insert(1,[''])
        return [i.strip() for i in v1]
        
    k1=list(pdict.keys())
    for k in k1:
        v1 = pdict[k]
        yb = sepYB(v1)
        pdict[k] = v1[:1]+yb+v1[2:]
    return pdict


def postProcess_fundset(pdict):
    def extraYB(v):
        rc = re.compile(r"\[.*?\]",re.U)
        r1 =  rc.search(v[1])
        if (r1):
            rm = r1.group()
        else:
            rm = ' '
        return rm
    fn2='quick_de-zh_CN'
    myDict2 = getDict(fn2)
    k1=list(pdict.keys())
    k2=list(myDict2.keys())
    for k in k1:
        v1 = pdict[k]
        if (k in k2):
            v2 = myDict2[k]
            yb = extraYB(v2)
            pdict[k] = v1[:1]+[yb]+v1[1:]
        else:
            pdict[k] = v1[:1]+['']+v1[1:]
    return pdict

def getSyn(fn):
    fnSyn = fn + '.syn'
    if (not os.path.exists(fnSyn)):
        return None
    f = open(fnSyn,'rb')
    p1=0
    end = os.fstat(f.fileno()).st_size
    mydict={}
    while True:
        key = getString(f,p1,256)
        if (not key):
            break
        offset = getValue(f)
        if (key in mydict):
            mydict[key] = mydict[key]+[offset]
        else:
            mydict[key] = [offset]
        if (p1 >= end-4):
            break
        p1 += len(key) + 5
    return mydict
    
def postProcess(pdict):
    return postProcess_fccf(pdict)
    #return postProcess_oxford(pdict)
    
def main(fn1):
    myDict1 = getDict(fn1)
    k1=list(myDict1.keys())
    myDict1 = postProcess(myDict1)       
    write2csv(fn1,myDict1)

if __name__ == "__main__":
    fn='fccf'
    #print(getSyn(fn))
    main(fn)


