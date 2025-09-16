import os
import re
import json
import copy
import time
import random
import pickle

import numpy as np

from utils.chat2DeepSeek import Chat2DeepSeek
from utils.gen_prompt import Prompt
from utils.util import *
from utils.Scout import *

API_KEY = 'sk-553325d9958b4b3ba7bf15d297abb364'


def chat4trigger(s, event_dict, thread_id=0):
    revise = "note that The most common form of event arguments is bare nouns without modification or anything  like 'the', 'a', 'after', etc. revise only the json output you just have returned."
    trigger_pool = {}
    trigger_pool['arguments_114'] = []
    s_time = time.time()
    chat = Chat2DeepSeek(api_key=API_KEY, model='deepseek-chat')
    sout_s1 = souts1_prompt(s, event_dict)
    response = chat.prompt2chat(sout_s1)
    result = {}
    a_d = re.findall('```json(.*?)```', response, flags=re.S)
    for sen in a_d[::-1]:
        try:
            sen = json.loads(sen)
            if 'events' in sen.keys():
                result = sen
        except:
            continue

    for event in result.get('events'):
        sout_s2 = souts2_promt(s, event, event_dict)
        response = chat.prompt2chat(sout_s2)
        result = {}
        a_d = re.findall('```json(.*?)```', response, flags=re.S)
        for sen in a_d[::-1]:
            try:
                result = json.loads(sen)
            except:
                continue
        for event in result:
            if not trigger_pool.get(event):
                trigger_pool[event] = []
            trigger_pool[event].extend(result[event])

            sout_s3 = souts3_promt(s, event, result[event], event_dict)
            response = chat.prompt2chat(sout_s3)
            response = chat.prompt2chat(revise)
            result = {}
            a_d = re.findall('```json(.*?)```', response, flags=re.S)
            for sen in a_d[::-1]:
                try:
                    result = json.loads(sen)
                except:
                    continue
            trigger_pool['arguments_114'].append(result)
    # print("thread id: {} time {}".format(thread_id, time.time() - s_time))
    return trigger_pool

def chat4trigger_pool_all(request_list, work_dict_fn, event_dict_fn, thread_id = 0, tpool = {}):
    work_dict = load_json(work_dict_fn)
    event_dict = load_json(event_dict_fn)
    event_tri = {}
    for i, work in enumerate(request_list, 1):
        if tpool.get(work):
            print('thread id: {} ---work {} chated'.format(thread_id, work))
            continue
        tpool[work] = {}
        s_time = time.time()
        for j, sen in enumerate(work_dict[work]):
            if not sen:
                continue
            try:
                start_time = time.time()
                pool = chat4trigger(sen, event_dict, thread_id)
                for event in pool:
                    if not event_tri.get(event):
                        event_tri[event] = []
                    event_tri[event].extend(pool[event])
                end_time = time.time()
                print('thread id: {} work: {}, {}/{}, in {} s'.format(thread_id, work, j, len(work_dict[work]), end_time - start_time))
                time.sleep(2)
            except Exception as e:
                print('thread id: {} --- error: {}'.format(thread_id, e))
                continue
        tpool[work] = event_tri
        print('thread id: {} Done processing work: {}, in {} s'.format(thread_id, work, time.time() - s_time))
        save_json(tpool, './tri_{}_{}_{}.json'.format(i, work, get_local_time()))
    return tpool
    print('ALL DONE')


def main():
    print('-------------START CHARTING------------')

    batch = load_json('./exp_data/trigger_workgroup.json')
    request_list = list(batch.keys())
    tpool = chat4trigger_pool_all(request_list, work_dict_fn = './exp_data/trigger_workgroup.json', event_dict_fn = './meta_data/event_dict_full.json', thread_id = 0)
    save_json(tpool, './scout_trigger_{}.json'.format(get_local_time()))


if __name__ == "__main__":
    main()