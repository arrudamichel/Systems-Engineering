# -*- coding: utf-8 -*-
"""
Created on Mon Apr  6 19:36:59 2015

@author: Raul Sena Ferreira
"""
from pprint import pprint as pp
import ast
import logging
import time
import math
import operator
import matplotlib.pyplot as plt
from pylab import *

#globals
evaluatorLog = ''

#def main():
def executeEvaluator(path, pathVector, expectedResultsString, resultsStr, use_mode):
    begin = time.time()
    global evaluatorLog
    #logging instantiate
    logPath = path+'/Evaluator/evaluator.log'
    log('evaluator', logPath)
    evaluatorLog = logging.getLogger('evaluator')
    evaluatorLog.info('Processing Evaluator module...')
    
    expectedResults = strToDictExpectedResults(expectedResultsString)
    
    results = strToDictResults(resultsStr)
    
    relevanceList = selectRelevantDocs(expectedResults)
    
    PK={}
    F1={}
    AVP=[]
    #executing metrics
    for query in expectedResults.keys():
        if precisionK(results[query], relevanceList[query]) is not None:
            PK.update({query: precisionK(results[query], relevanceList[query])})#k=10 documents
            
        
        AVP.append(averagePrecision(results[query], relevanceList[query]))
        
        F1.update({query: f1Measure(results[query], relevanceList[query])})
    
    G11Pts=graphic11points(results, relevanceList)
    
    MAP=meanAveragePrecision(AVP)
   
    DCG=discountedCumulativeGain(results, expectedResults, range(4,8))

    NDCG=normalizedDiscountedCumulativeGain(DCG, results, expectedResults, range(4,8))
    
    writeReport(PK, MAP, DCG, NDCG, F1, use_mode, path, pathVector[3][1])
    
    writeGraphic(path+'/Searcher/'+use_mode+'/interpolated-precision-recall-11pts.pdf', G11Pts)
    writeMetricsOnFile(path, '/Searcher/'+use_mode+'/precicionk.csv', PK, use_mode)
    writeMetricsOnFile(path, '/Searcher/'+use_mode+'/mean-average-precision.csv', MAP, use_mode, False)
    writeMetricsOnFile(path, '/Searcher/'+use_mode+'/discount-cumulative-gain.csv', DCG, use_mode)
    writeMetricsOnFile(path, '/Searcher/'+use_mode+'/normalized-discount-cumulative-gain.csv', NDCG, use_mode)
    writeMetricsOnFile(path, '/Searcher/'+use_mode+'/f1-measure.csv', F1, use_mode)
    
    end = time.time() - begin
    evaluatorLog.info('End of Evaluator Module. Total of %s elapsed.' % str(end))



def graphic11points(results, relevanceList):
    globalRelevants = set()
    globalResults = []
    arrayPoints = []
    
    for k in relevanceList:
        for doc in relevanceList[k]:
            globalRelevants.add(doc)
        
    kRels = math.ceil(len(globalRelevants)/10)
    cont=kRels

    for key in results:
        for res in results[key]:
            if res[1] not in globalResults:
                globalResults.append(res[1])
    
    nDocs = 0
    nRels = 0
    vetAux = []
    arrayPoints.append(1.0)#initial precision
    
    for res in globalResults:
        nDocs+=1
        if res in globalRelevants:
            nRels+=1
            vetAux.append(nRels/nDocs)
            if nRels == cont:
                arrayPoints.append(max(vetAux))
                vetAux = []
                cont+=kRels
        
    return arrayPoints
    


def selectRelevantDocs(expectedResults, minRelevanceScore=4):
    relevantsByQuery = {}
    
    for query in expectedResults.keys():
        relevants=[]
        for doc in expectedResults[query]:
            if doc[1] >= minRelevanceScore:
                relevants.append(doc[0])
        relevantsByQuery.update({query: relevants})
    return relevantsByQuery



#measures methods
def precisionK(results, relevants, k=10):
    numDocs=k
    rels=0
    
    for doc in results:
        if k > 0:
            k-=1
            if doc[1] in relevants:
                rels+=1
        else:
            return rels/numDocs



def averagePrecision(results, relevants):
    
    relevantsOfK=[]
    total=0
    p=0
    
    for docResults in results:
        total+=1
        if docResults[1] in relevants:
            relevantsOfK.append(docResults[1])
            try: p+=precisionK(results, relevantsOfK, total)
            except TypeError: pp("")
    if len(relevantsOfK) > 0:
        p /= len(relevantsOfK)
        return p
    else:
        return 0
        
        
    
def meanAveragePrecision(avgPrecisionVector):
    return sum(avgPrecisionVector)/len(avgPrecisionVector)
    
    
    
def discountedCumulativeGain(results, expectedResults, relevanceScale=range(0,8)):
    arrayDCG = {}
    for query in expectedResults.keys():
        relevants={}
        
        for doc in expectedResults[query]:
            if doc[1] in relevanceScale:
                relevants.update({doc[0]: doc[1]})
        
        DCG=0
        for doc in results[query]:
            
            if doc[1] in relevants:
                rank = float(doc[0])
                if rank > 1:
                    logRank = math.log(rank, 2)
                else:
                    logRank = 1
                
                scale = float(relevants[doc[1]])
                DCG += scale/logRank
        arrayDCG.update({query: DCG})
    return arrayDCG
    
    
    
def normalizedDiscountedCumulativeGain(dcg, results, expectedResults, relevanceScale=range(0,8)):
    arrayIDCG = {}
    for query in expectedResults.keys():
        relevants={}
        
        for doc in expectedResults[query]:
            if doc[1] in relevanceScale:
                relevants.update({doc[0]: doc[1]})
        relevants=sorted(relevants.items(),key=operator.itemgetter(1), reverse=True)
        #pp(relevants) 
        DCG=0
        for doc in results[query]:
            if doc[1] in relevants:
                rank = float(doc[0])
                if rank > 1:
                    logRank = math.log(rank, 2)
                else:
                    logRank = 1
                
                scale = float(relevants[doc[1]])
                DCG += scale/logRank
        arrayIDCG.update({query: DCG})
    return arrayIDCG



def f1Measure(results, relevants):
    precision=0
    recall=0
    rel=0
    nDoc=0
    nRel=len(relevants)
    
    for doc in results:
        nDoc+=1
        if doc[1] in relevants:
            rel+=1
            
    if rel > 0:
        precision=rel/nDoc
        recall=rel/nRel
        return 2 * ((precision*recall)/(precision+recall))
    else:
        return 0

    
    
def writeMetricsOnFile(path, filename, metric, use_mode, isDict=True):
    
    f = open(path+filename, 'w+')
    if isDict == True:
        for key in metric.keys():
            f.write(key+";%s\n" % metric[key])
    else:
        f.write(";%s\n" % metric)
    f.close()



def writeReport(PK, MAP, DCG, NDCG, F1, use_mode, path, pathVector):
    evaluatorLog.info('Writing evaluator results on file report...')
    
    f = open(path+pathVector, 'w+')
    f.write("########################    REPORT OF METRICS    -    "+use_mode+" MODE    ########################\n\n\n")
    f.write("########################    Precision@10 - "+use_mode+"    ########################\n")
    for key in PK.keys():
        f.write(key+";%s\n" % PK[key])
    f.write("########################    Mean Average Precision - "+use_mode+"    ########################\n")
    f.write(";%s\n" % MAP)
    f.write("\n########################    Discounted Cumulative Gain - "+use_mode+"    ########################\n")
    for key in DCG.keys():
        f.write(key+";%s\n" % DCG[key])
    f.write("########################    Normalized Discounted Cumulative Gain - "+use_mode+"    ########################\n")
    for key in NDCG.keys():
        f.write(key+";%s\n" % NDCG[key])
    f.write("########################    F1 Measure - "+use_mode+"    ########################\n")
    for key in F1.keys():
        f.write(key+";%s\n" % F1[key])
    f.close()
    


def compareResults(results, expectedResults):
    return 0



def writeGraphic(filepath, arrayPoints):
    plt.plot(arrayPoints)
    plt.xlabel('Recall(Decil)')
    plt.ylabel('Precision')
    
    figure(1, figsize=(6,6))
    
    savefig(filepath, bbox_inches='tight')
    
    
    
#utils
def strToDictResults(resultsStr):
    results = {}
    for r in resultsStr:
        lstString = r[1].lstrip('[').rstrip(']').split('],[')
        lst=[]
        for l in lstString:
            lst.append(l.replace(' ','').split(','))
        results.update({r[0]: lst})
    return results
    
    
    
def strToDictExpectedResults(expResStr):
    expectedResults = {}
    for e in expResStr:
        expectedResults.update({e[0]: ast.literal_eval(e[1])})
    return expectedResults
    
    
    
def log(name, logFile):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    # create a file handler
    handler = logging.FileHandler(logFile)
    handler.setLevel(logging.INFO)
    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(handler)
    logger.addHandler(streamHandler)
    
    
'''    
if __name__ == '__main__':
    main()
'''
