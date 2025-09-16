# gen data

import os
import re
import json
import copy
import time
import logging
import random
import pickle

from utils.chat2DeepSeek import Chat2DeepSeek
from utils.gen_prompt import Prompt
from utils.util import parse_trigger_answer, parse_argument_answer, save_json, load_json


logging.basicConfig(filename='output.log', level=logging.INFO)
print = logging.info

#event_sub_list = ['TRANSPORT', 'ELECT', 'START-POSITION', 'ATTACK', 'END-POSITION', 'MEET', 'MARRY', 'PHONE-WRITE', 'TRANSFER-MONEY', 'SUE']

API_KEY = 'sk-7015d98e24c9431f9fb7fb2a4454186e'
event_sen = {}
#event_sen = load_json('./history_data/data_12_CHARGE-INDICT_3_23_17_31.json')
event_dict = load_json('./meta_data/event_dict_full.json') # defin from doc
trigger_dict = load_json('./meta_data/trigger_pool_ori.json')
arguments_dict = load_json('./meta_data/argument_pool_ori.json')
print('----------------------------------------------')

'''beborn = {}
for role, arg_dict in arguments_dict['BE-BORN']['BE-BORN'].items():
    beborn[role] = []
    for k, arg in arg_dict.items():
        beborn[role].extend(arg)

endpos = {}
for role, arg_dict in arguments_dict['END-POSITION']['END-POSITION'].items():
    endpos[role] = []
    for k, arg in arg_dict.items():
        endpos[role].extend(arg)

def comprase_entity_arg(j_l):
    e_d = {}
    for e in j_l:
        e_d[e] = []
        for n in j_l[e]:
            for arg in j_l[e][n]:
                e_d[e].append(arg)
    return e_d

def comprase_arg(argument_dict):
    com_argument_dict = {}
    for event in argument_dict:
        com_argument_dict[event] = comprase_entity_arg(argument_dict[event])
    return com_argument_dict

arguments_dict = comprase_arg(arguments_dict)
arguments_dict['BE-BORN'] = beborn 
arguments_dict['END-POSITION'] = endpos'''

n_trigger = 100
n_argument = 20
sentence_per_event = 50
complex_score = [5, 10] # not implemented
max_argument = 2
max_event = 2
max_refine = 3

weight_dict = {0:[1],
                1:[1],
                2:[0.9, 0.1],
                3:[0.8, 0.15, 0.05],
                4:[0.5, 0.3, 0.1, 0.1]
                  }
def get_n_event(max_event, weight_dict):
    if max_event == 0:
        return 0
    return random.choices([ i for i in range(1, max_event + 1)], weights=weight_dict[max_event])

def get_local_time():
    return str(time.localtime().tm_mon) + '_' + str(time.localtime().tm_mday) + '_' + str(time.localtime().tm_hour) + '_' + str(time.localtime().tm_min)


def is_true(ans):
    if ans.strip().startswith('```'):
        res = json.loads(re.findall(r'```json(.*?)```', ans, re.S)[0])
    else:
        res = json.loads(ans)
    if res['conclusion'].strip().upper() == 'YES':
        return True
    else:
        return False
    
def do_check_refine(chat, q):
    time.sleep(1)
    s_time = time.time()
    error = 1
    while error:
        try:
            res = chat.prompt2chat(q)
            error = 0
        except:
            print('retrying...')
            error = 1
    print('checked in {} s'.format(time.time() - s_time))
    return res

def chat4refine(chat, r, event_dict, max_refine):
    t_time = time.time()
    p_check = 'Based on the sentence you just gennerated, please answer:'
    end = '\nAnd return reason about your answer.And conclude your answer in one word: yes/no.'
    refine = '\nAnd please correct/refine the generated sentences based on your answer(DO NOT change/delete/add any event mentions(e.g. their triggers or arguments) in the sentence, but you can try changing the form of trigger(e.g. noun -> verb) first, if that can not solve,then try replace a new trigger(some trigger could be both noun and verb). And do follow the JSON format asked before).'
    answer_format = '''\nAnswer format:{"reason": "1. All mentions are valid spans. 2. 'Accredited' typically denotes certification, not initiating a START-POSITION event (common triggers: 'appointed', 'hired'). 3. 'Organization' as Entity and 'technician/administrator' as Position align with roles if properly tagged. 4. No extraneous roles (e.g., Attacker) are present. Final answer is 'No' due to invalid trigger.",
        "conclusion": "No",
        "sentences": [
        "We get reports that these <ATTACK><Target>civilians</Target></ATTACK> especially in the ( INAUDIBLE ) <ATTACK><Target>population</Target></ATTACK> have been <ATTACK>attacked</ATTACK> by the Iraqi <ATTACK><regime>regime</regime></ATTACK> themselves so they can't blame the American and said look what the American doing to us"]
        }'''
    for e in r:
        p = ''
        event = r[e]['event']
        start = '\n  For event {}, please answer:'.format(event)
        roles = [role for role in r[e]['argument']]
        role_dict = event_dict[event][1]
        args = []
        for role in r[e]['argument']:
            args.extend(r[e]['argument'][role])

        trg_arg = r[e]['trigger'] + ' and ' + ' and '.join(args)
        q_1 = '\n\t1.whether each mention: {} is a subsequence(span) of the passage;'.format(trg_arg)
        p += q_1


        q_2 = '\n\t2.whether trigger {} is used to initiate an occurrence;'.format(r[e]['trigger']) 
        p += q_2

        q_3_head = '\n\t3.for roles and arguments:'
        p += q_3_head
        for role in roles:
            args = r[e]['argument'][role]
            arg = ' and '.join(args)
            q_3 = '\n\t\twhether {0} is used as an event participant or attribute of the specific {1};\nwhether {0} is serving the required argument role {2}.'.format(arg, event, role)
            q_5 = '\n\t\twhether <{0}></{0}> tags of the {1} mention in the passage context match the provided one:{0}.'.format(role, arg)
            q_3 = q_3 + q_5
            p += q_3

        ex_roles = []
        for role in role_dict:
            if role not in roles:
                ex_roles.append(role)

        q_4 = '\n\t4.whether the passage not contains information that could serve as an argument of argument role {} that should not appear.'.format(' and '.join(ex_roles))
        p += q_4
        p_check += (start + p + '\n')
    #     refine_res = chat.prompt2chat(start + p + end + refine + answer_format)
    p_check += end + refine + answer_format

    # refine_res = chat.prompt2chat(p_check)
    refine_res = do_check_refine(chat, p_check)

    i = 1
    while not is_true(refine_res) and i < max_refine:
        refine_res = do_check_refine(chat, p_check)
        i += 1

    if not is_true(refine_res):
        refine_res = ''
    print(time.time() - t_time)
    return refine_res

def chat4data(gen_prompt, main_event, event_dict, max_refine):
    prompt, record = gen_prompt.gen_data_prompt(main_event=main_event, n_event=get_n_event(max_event, weight_dict)[0])
    chat = Chat2DeepSeek(api_key=API_KEY)
    response = chat.prompt2chat(prompt).strip()
    #response = chat4refine(chat, json.loads(record), event_dict, max_refine)
    a_d = re.sub('^```json', '', response, flags=re.I)
    a_d = re.sub('```$', '', a_d, flags=re.I)
    try:
        return [json.loads(a_d), json.loads(record)]
    except:
        return [a_d]
    
def chat4data_all(event_dict, gen_prompt, max_refine):
    for i, event in enumerate(event_dict, 1):
        #if not event in event_sub_list:
        #    continue
        # event_dict = {'ATTACK':[event_def, role_dict, example, exam_trigger]}
        if event_sen.get(event) and len(event_sen[event]) >= 50:
            print('---EVENT {} chated'.format(event))
            continue

        s_start_time = time.time()
        print('TIME {} -- chating for EVENT {}'.format(get_local_time(), event))
        if not event_sen.get(event):
            event_sen[event] = []
        while len(event_sen[event]) < 50: 
            try:
                start_time = time.time()
                sen_record = chat4data(gen_prompt, event, event_dict, max_refine)
                end_time = time.time()
                print('TIME {} -- done {}/50, in {} s'.format(get_local_time(), len(event_sen[event]), end_time - start_time))
                if type(sen_record[0]) == type({}):
                    event_sen[event].append({'sentence':sen_record[0], 'record':sen_record[1]})
                else:
                    print('error ', event)
                    try:
                        with open('./log/error/' + event + '_arg.txt', 'w') as f:
                            f.write(sen_record)
                    except:
                        print('---can not save:', sen_record)
                save_json(event_sen, './history_data/data_{}_{}_{}.json'.format(i, event, get_local_time()))
                print('TIME {} -- done save'.format(get_local_time()))
            except:
                continue
    
        save_json(event_sen, './data_{}_{}_{}.json'.format(i, event, get_local_time()))
        print('TIME {} -- done save'.format(get_local_time()))
        print('Done processing EVENT: {}, in {} s'.format(event, end_time - s_start_time))
        time.sleep(5)
        
gen_prompt = Prompt(
    event_dict = event_dict, 
    trigger_dict = trigger_dict, 
    arguments_dict = arguments_dict, 
    n_event = get_n_event(max_event, weight_dict)[0], 
    max_argument = max_argument,
    complex_score = complex_score)

print('-------------START CHARTING------------')
chat4data_all(event_dict, gen_prompt, max_refine)
save_json(event_sen, './data_sen_{}.json'.format(get_local_time()))
