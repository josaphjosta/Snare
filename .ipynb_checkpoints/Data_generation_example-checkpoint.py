# gen data

import time
import logging
import random

from utils.chat2DeepSeek import Chat2DeepSeek
from utils.gen_prompt import Prompt
from utils.util import *

API_KEY = 'sk-7015d98e24c9431f9fb7fb2a4454186e'
event_sen = {}
event_sub_list = ['TRANSPORT']  #

# event_dict_fn = './meta_data/event_dict_full.json'
# trigger_dict_fn = './trigger_sout.json'
# arguments_dict_fn = './meta_data/argument_pool_augmented_5_16.json'
# arg_role_definition_fp = './meta_data/arg_roles/'

passages_per_event = 1
complex_score = 3  # not implemented
max_argument = 2
max_event = 5

weight_dict = {0: [1],
               1: [1],
               2: [0.5, 0.5],
               3: [0.2, 0.5, 0.3],
               4: [0.1, 0.2, 0.3, 0.4],
               5: [0.7, 0.2, 0.05, 0.025, 0.025]
               }


def load_meta_data(event_dict_fn, trigger_dict_fn, arguments_dict_fn, arg_role_definition_fp):
    event_dict = load_json(event_dict_fn)  # defin from doc
    trigger_dict = load_json(trigger_dict_fn)
    arguments_dict = load_json(arguments_dict_fn)

    fp = arg_role_definition_fp

    arg_role_definition = {}
    for fn in os.listdir(fp):
        if not fn.endswith('.txt'):
            continue
        with open(fp + fn, 'r', encoding='utf-8') as f:
            s = f.read()
        j = json.loads(s)
        arg_role_definition.update(j)
    return event_dict, trigger_dict, arguments_dict, arg_role_definition


def load_checkpoint(checkpoint=''):
    if checkpoint:
        return load_json(checkpoint)
    else:
        return {}


def get_n_event(max_event, weight_dict):
    if max_event == 0:
        return 0
    return random.choices([i for i in range(1, max_event + 1)], weights=weight_dict[max_event])


def get_local_time():
    return str(time.localtime().tm_mon) + '_' + str(time.localtime().tm_mday) + '_' + str(
        time.localtime().tm_hour) + '_' + str(time.localtime().tm_min)


def chat4data(prompt, record, main_event, arg_role_definition, thread_id):
    target_sen = {}
    valid_output = '''
Valid Output(JSON format):
         {
          "sentences": [
            "In yesterday's special election, the <Entity>district</Entity> of <Place>Ohio</Place> successfully <ELECT><trigger>voted</trigger></ELECT> to fill the congressional seat vacancy."
          ]
        }
Note: when rewriting passage, just change what the prompt demands, DO NOT change event mentions which belong to other event. 
'''
    tail = '''
Value allowed: argument_should_not_appear: "No" OR list of the spotted untagged argument spans (e.g., ["argument_1", "argument_2"])
Note: the spotted untagged argument spans is bare nouns without modification(no special tag or modification words)
Please check the questions step by step, print out the process, then return your answer in json:
'''
    revise = "Note that The most common form of event arguments is bare nouns without modification or anything  like 'the', 'a', 'after', etc. Convert the event arguments in the json output you just have returned into bare nouns.Return the json ouput anyway."
    s_time = time.time()
    chat = Chat2DeepSeek(api_key=API_KEY, model='deepseek-chat')
    response = chat.prompt2chat(prompt).strip()
    gen_sen = re.findall('```json(.*?)```', response, flags=re.S)
    print('thread_id: {}\tgenerated in(s):{}'.format(thread_id, time.time() - s_time))
    for e_id in record:
        check_iter = 0
        ss_time = time.time()
        event_data = record[e_id]
        event_type = event_data['event']
        while check_iter < 3:
            sss_time = time.time()
            event_data = record[e_id]
            event_type = event_data['event']
            trigger = event_data['trigger']
            head = 'For the passage(in json) you just generated/revised, and for event {} triggered by {}:\n'.format(
                event_type, trigger)

            check = generate_questions(event_data, arg_role_definition, miss_only=True)
            response = chat.prompt2chat(head + check + tail).strip()
            a_d = re.findall('```json(.*?)```', response, flags=re.S)

            result = {}
            for sen in a_d[::-1]:
                try:
                    do_revise = False
                    sen = json.loads(sen)
                    if not sen.get('argument_should_not_appear'):
                        continue

                    for role, should_not_appear in sen.get('argument_should_not_appear').items():
                        if isinstance(should_not_appear, list):
                            do_revise = True
                            break

                    if do_revise:
                        response = chat.prompt2chat(revise).strip()
                        a_dl = re.findall('```json(.*?)```', response, flags=re.S)
                        for senl in a_dl[::-1]:
                            try:
                                senl = json.loads(senl)
                                if senl.get('argument_should_not_appear'):
                                    result = senl
                                    # print('{}\n{}'.format(response, result))
                                    # print()
                                    break
                            except:
                                continue
                        break
                except Exception as e:
                    print('thread_id: {}\t error: {}  discard {}:  {}'.format(thread_id, e, main_event, sen))
                    # print(response)
                    return []

            if result:
                problem_statements, event_data = generate_problem_statements(result, event_data, arg_role_definition)
                if problem_statements['tag']:
                    # print(head + '\n'.join(problem_statements['tag']) + valid_output)
                    response = chat.prompt2chat(head + '\n'.join(problem_statements['tag']) + valid_output).strip()
                    gen_sen = re.findall('```json(.*?)```', response, flags=re.S)
                    record[e_id] = event_data
                print('thread_id: {}\trevised for {} iter {} in(s): {}'.format(thread_id, event_type, check_iter,
                                                                               time.time() - sss_time))
                # if not problem_statements['rewrite']:
                #     check_iter = 3

            check_iter = 3
        print('thread_id: {}\trevised for {} completed in(s): {}'.format(thread_id, event_type, time.time() - ss_time))

        for sen in gen_sen[::-1]:
            try:
                sen = json.loads(sen)
                if 'sentences' in sen.keys():
                    if sen['sentences']:
                        target_sen = sen
                        break
            except Exception as e:
                print('thread_id: {}\t {} error json {}:  {}'.format(thread_id, e, main_event, sen))

    print('thread_id: {}\tpassage done in(s):{}'.format(thread_id, time.time() - s_time))
    if target_sen:
        return [target_sen, record]
    else:
        return []


def chat4data_all(event_sub_list, passages_per_event,
                  event_dict_fn, trigger_dict_fn, arguments_dict_fn, arg_role_definition_fp,
                  max_argument,
                  max_event,
                  weight_dict,
                  complex_score,
                  checkpoint='',
                  thread_id=1
                  ):
    event_sen = load_checkpoint(checkpoint)

    event_dict, trigger_dict, arguments_dict, arg_role_definition = load_meta_data(event_dict_fn, trigger_dict_fn,
                                                                                   arguments_dict_fn,
                                                                                   arg_role_definition_fp)

    data4chat = load_pickle('./exp_data/event_batch_record-refine_withexam10.pkl')

    for i, event in enumerate(event_dict, 1):
        if not event in event_sub_list:
            continue

        if event_sen.get(event) and len(event_sen[event]) >= passages_per_event:
            print('thread_id: {}\t---EVENT {} chated'.format(thread_id, event))
            continue

        s_start_time = time.time()
        print('thread_id: {}\tTIME {} -- chating for EVENT {}'.format(thread_id, get_local_time(), event))
        sen_record = []
        if not event_sen.get(event):
            event_sen[event] = []
        for prompt, record in data4chat[event]:
            try:
                start_time = time.time()
                sen_record = chat4data(prompt, record, event, arg_role_definition, thread_id)
                end_time = time.time()
                print(
                    'thread_id: {}\t{}/{} done in {} s, --  TIME {}'.format(thread_id, len(event_sen[event]),
                                                                            passages_per_event, end_time - start_time,
                                                                            get_local_time()))
                if sen_record[0]['sentences']:
                    event_sen[event].append({'sentence': sen_record[0], 'record': sen_record[1]})
                else:
                    print('error ', event)
                    try:
                        with open('./log/error/' + event + '_arg_{}.txt'.format(random.randrange(0, 100000)), 'w') as f:
                            f.write(json.dumps(sen_record))
                    except:
                        print('---can not save:', sen_record)
                save_json(event_sen, './history_data/data_{}_{}_{}_{}.json'.format(i, event, get_local_time(),
                                                                                   random.randrange(0, 100000)))
                print('thread_id: {}\tTIME {} -- done save'.format(thread_id, get_local_time()))
            except Exception as e:
                print('empty:', sen_record)
                print('thread_id: {}\tTIME {} ERROR: {}'.format(thread_id, get_local_time(), e))
                time.sleep(5)
                continue
            if len(event_sen[event]) >= passages_per_event:
                break
        end_time = time.time()
        save_json(event_sen, './data_{}_{}_{}_{}.json'.format(i, event, get_local_time(), random.randrange(0, 100000)))
        print('thread_id: {}\tTIME {} -- done save'.format(thread_id, get_local_time()))
        print('thread_id: {}\tDone processing EVENT: {}, in {} s'.format(thread_id, event, end_time - s_start_time))
        time.sleep(2)

    return event_sen


def main():
    print('-------------START CHARTING------------')
    event_sen = chat4data_all(event_sub_list, passages_per_event,
                              event_dict_fn, trigger_dict_fn, arguments_dict_fn, arg_role_definition_fp,
                              max_argument,
                              max_event,
                              weight_dict,
                              complex_score
                              )
    save_json(event_sen, './data_sen_{}.json'.format(get_local_time()))


if __name__ == "__main__":
    main()
