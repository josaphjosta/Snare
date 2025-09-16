# gen data
import ast
import json
import time
import logging
import random

from utils.chat2DeepSeek import Chat2DeepSeek
from utils.gen_prompt import Prompt
from utils.util import *
from utils.Scout import *

API_KEY = 'sk-7015d98e24c9431f9fb7fb2a4454186e'
event_sen = {}
event_sub_list = ['TRANSPORT', 'ELECT', 'START-POSITION', 'ATTACK', 'END-POSITION', 'MEET', 'MARRY', 'PHONE-WRITE', 'TRANSFER-MONEY', 'SUE']

event_dict_fn = './meta_data/event_dict_full.json'
trigger_dict_fn = './exp_data/trigger_sout_top10.json'
arguments_dict_fn = './exp_data/argument_sout_top-one-fourth.json'
arg_role_definition_fp = './meta_data/arg_roles/'

passages_per_event = 2
complex_score = 3  # not implemented
max_argument = 2
max_event = 5

weight_dict = {0: [1],
               1: [1],
               2: [0.5, 0.5],
               3: [0.2, 0.5, 0.3],
               4: [0.1, 0.2, 0.3, 0.4],
               5: [0.1, 0.1, 0.3, 0.3, 0.2]
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


def chat4data(gen_prompt, main_event, arg_role_definition, max_event, weight_dict, thread_id):
    record = gen_prompt.gen_event_record(main_event=main_event, n_event=get_n_event(max_event, weight_dict)[0])
    narrator = narrator_prompt(record, gen_prompt.event_dict)
    target_sen = {}
    s_time = time.time()
    chat = Chat2DeepSeek(api_key=API_KEY, model='deepseek-chat')
    response = chat.prompt2chat(narrator).strip()
    gen_sen = re.findall('```json(.*?)```', response, flags=re.S)[0]
    gen_sen = json.loads(gen_sen)
    if not isinstance(gen_sen['sentence'], str):
        return []
    target_sen = gen_sen
    print('thread_id: {}\tgenerated in(s):{}'.format(thread_id, time.time() - s_time))

    refiner = refiner_prompt(record, target_sen['sentence'], gen_prompt.event_dict)
    response = chat.prompt2chat(refiner).strip()
    gen_sen = re.findall('```json(.*?)```', response, flags=re.S)[0]
    trigger_list = ast.literal_eval(gen_sen)
    if not isinstance(trigger_list, list):
        return []

    add_list = []
    for e, t in trigger_list:
        for e_id, r in record.items():
            event = r['event']
            trigger = r['trigger']
            if event == e and trigger == t:
                break
        else:
            add_list.append([e, t])
    length = len(record)
    for i, e_t in enumerate(add_list):
        record['event_{}'.format(i+length)] = {
                                                'event': e_t[0],
                                                'trigger': e_t[1],
                                                'argument': {}
                                            }

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
                  thread_id = 1
                  ):
    event_sen = load_checkpoint(checkpoint)

    event_dict, trigger_dict, arguments_dict, arg_role_definition = load_meta_data(event_dict_fn, trigger_dict_fn,
                                                                                   arguments_dict_fn,
                                                                                   arg_role_definition_fp)

    gen_prompt = Prompt(
        event_dict=event_dict,
        trigger_dict=trigger_dict,
        arguments_dict=arguments_dict,
        n_event=get_n_event(max_event, weight_dict)[0],
        max_argument=max_argument,
        complex_score=complex_score,
        use_chain=False
    )

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
        while len(event_sen[event]) < passages_per_event:
            try:
                start_time = time.time()
                sen_record = chat4data(gen_prompt, event, arg_role_definition, max_event, weight_dict, thread_id)
                end_time = time.time()
                print(
                    'thread_id: {}\t{}/{} done in {} s, --  TIME {}'.format(thread_id, len(event_sen[event]),
                                                                            passages_per_event, end_time - start_time,
                                                                            get_local_time()))
                if sen_record[0]['sentence']:
                    event_sen[event].append({'sentence': sen_record[0]['sentence'], 'record': sen_record[1]})
                else:
                    print('error ', event)
                    try:
                        with open('./log/error/' + event + '_arg_{}.txt'.format(random.randrange(0, 100000)), 'w') as f:
                            f.write(json.dumps(sen_record))
                    except:
                        print('---can not save:', sen_record)
                save_json(event_sen, './history_data/data_{}_{}_{}_{}.json'.format(i, event, get_local_time(), random.randrange(0, 100000)))
                print('thread_id: {}\tTIME {} -- done save'.format(thread_id, get_local_time()))
            except Exception as e:
                print('empty:', sen_record)
                print('thread_id: {}\tTIME {} ERROR: {}'.format(thread_id, get_local_time(), e))
                time.sleep(0.5)
                continue
        end_time = time.time()
        save_json(event_sen, './data_{}_{}_{}_{}.json'.format(i, event, get_local_time(), random.randrange(0, 100000)))
        print('thread_id: {}\tTIME {} -- done save'.format(thread_id, get_local_time()))
        print('thread_id: {}\tDone processing EVENT: {}, in {} s'.format(thread_id, event, end_time - s_start_time))
        time.sleep(0.5)

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
