import random
import redis
from django.conf import settings
import json
import pandas as pd
import numpy as np
import collections
from competition.ndcg import ndcg_at_k
from django.utils.translation import ugettext as _
import math
import sys,os 

SUBMISSION_QUEUE_KEY = "submission_queue"

redis_pool = redis.ConnectionPool(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)


def enqueue_submission(submission):
    redis_conn = redis.Redis(connection_pool=redis_pool)
    info = {
        'Pk': submission.pk,
        'CompetitionPk': submission.competition.pk,
        'Path': submission.content.name
    }
    redis_conn.rpush(SUBMISSION_QUEUE_KEY, json.dumps(info))


def AUC(filename):
    return random.random()


Result = collections.namedtuple("Result", ["score", "message"])


def SMP_score(submission_path, truth_path):
    try:
        sub = pd.read_csv(submission_path, encoding='utf-8')
        truth = pd.read_csv(truth_path, encoding='utf-8')
        if len(set(sub['uid'])) != len(sub['uid']):
            return Result(-1, _("Duplicated uid"))
        if len(sub['uid']) != len(truth['uid']):
            return Result(-1, _("length incorrect"))
        
        all = pd.merge(sub, truth, on='uid', how='right', suffixes=['_sub', '_truth'])

        age_acc = np.average(all['age_sub'] == all['age_truth'])
        gender_acc = np.average(all['gender_sub'] == all['gender_truth'])
        province_acc = np.average(all['province_sub'] == all['province_truth'])

        score = age_acc * 0.3 + gender_acc * 0.2 + province_acc * 0.5
        return Result(score, None)
    except Exception as e:
        return Result(-1, _("Wrong format"))
        

#calculate NDCG_score
def ndcg4dataset(mapping, ques2user, k):
    def _map_gt(ques, user_score, mapping):
        return [mapping[(ques,user)] for user,score in user_score]

    for ques in ques2user:
        ques2user[ques].sort(key = lambda x: x[1], reverse=True)

    scores  = [ndcg_at_k(_map_gt(ques, ques2user[ques], mapping), \
               k, method = 1) \
               for ques in ques2user if k <= len(ques2user[ques])]
    evaluated_num = len(scores)
    ndcg_r_score = sum(scores)/evaluated_num
    return ndcg_r_score

def NDCG_score(submission_path, truth_path):
    try:
        sub = pd.read_csv(submission_path, encoding='utf-8')
        truth = pd.read_csv(truth_path, encoding='utf-8')
        
        if len(sub['uid']) != len(truth['uid']):
            return Result(-1, _("Line number of submission is not correct")) 
            
        #read truth_file
        mapping = {}
        for record_index,record in truth.iterrows(): 
            qid = record['qid']
            uid = record['uid']
            label = record['label']
            mapping[(qid, uid)] = int(label)

        #read submission_file
        ques2user = {}
        for record_index,record in sub.iterrows(): 
            qid = record['qid']
            uid = record['uid']
            label = record['label']
            if qid not in ques2user:
                ques2user[qid] = []
            ques2user[qid].append((uid, float(label)))  

        ndcg_r_score5 = ndcg4dataset(mapping,ques2user,5)
        ndcg_r_score10 = ndcg4dataset(mapping,ques2user,10)

        score = ndcg_r_score5 * 0.5 + ndcg_r_score10 * 0.5
        return Result(score, None)
    except Exception as e:
        return Result(-1, _("Wrong format"))

sohu_truth = {1:'matchingInfo0.txt', 2:'matchingInfo1.txt', 3:'matchingInfo2.txt', 4:'matchingInfo3.txt', 5:'matchingInfo4.txt', 6:'matchingInfo5.txt'}
def SOHU_score(resPath, groundTruthPath, sohu_week):
    score = 0.0
    try:
        resReader = open(resPath, 'r', encoding='utf-8')
        truth_path = "/var/www/dc/truth/"+str(groundTruthPath)
        if sohu_week > 0:
            truth_path = "/var/www/dc/truth/sohu_6/"+sohu_truth[sohu_week]
        groundTruthReader = open(truth_path, 'r', encoding='utf-8')

        #read truth_file
        groundTruthMap = {}        
        for line in groundTruthReader:  
            tmp = line.replace("\n", "").split('\t')
            groundTruthMap[tmp[1]] = tmp[0]
            
        #read submission_file
        resMap = {}
        for line in resReader:
            tmp = line.replace("\n", "").split(",")
            if tmp.__len__() != 11:
                return Result(-1, _("Column of submission is not correct"))
            value = []
            for i in range(1, 11):
                value.append(tmp[i])
            resMap[tmp[0]] = value

        for tmp in resMap:
            key = tmp
            groudTruth = groundTruthMap[key]
            if groudTruth is None:
                return Result(-1, _("Wrong format"))
            value = resMap[key]
            dcg = 0.0
            for i in range(0, 10):
                if value[i].lower() == groudTruth.lower():
                    dcg += (math.pow(2, 1) - 1.0) * (math.log(2) / math.log(i + 2))/ 4.543559338088345
            score += dcg

        resReader.close()
        groundTruthReader.close()
        score = score / float(len(groundTruthMap))

        return Result(score, None)
    except Exception as e:
        return Result(-1, _("Wrong format"))

def ML3_score(submission_path, groundTruthPath):
    try:
        truth_path = "/var/www/dc/truth/"+str(groundTruthPath)
        id2citation_truth = {}
        with open(truth_path) as f:
            for line in f:
                line = line.strip().split('\t')
                id2citation_truth[line[0]] = int(line[1])
    
        id2citation_sub = {}
        with open(submission_path) as f:
            for line in f:
                line = line.strip().split('\t')
                id2citation_sub[line[0]] = eval(line[1])
    
        if len(id2citation_sub) != len(id2citation_truth):
            return Result(-1, _("length incorrect"))
    
        score = 0
        for k,v in id2citation_truth.items():
            v1 = id2citation_sub.get(k, None)
            if v1 == None:
                return Result(-1, _("Wrong format"))
            score += (v1- v)**2
    
        score = np.sqrt(score/len(id2citation_truth))
        return Result(score, None)
    except Exception as e:
        return Result(-1, _("Wrong format"))
