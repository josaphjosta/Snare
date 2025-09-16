import os
import random
import copy
import json
import re
from utils import util
from collections import defaultdict, Counter

from StaticTamplate import StaticTamplate


class DataPrompt:
    def __init__(self, event_dict=None, trigger_dict=None, arguments_dict=None, n_event=None, max_argument=None, complex_score=None, use_chain = True, minimum_arg_fn = './meta_data/minimum_argument_dict.json', event_chains = './meta_data/event_chains.pkl', role_relations = './meta_data/role_relations.pkl'):
        # event_dict = {'ATTACK':[event_def, role_dict, example, exam_trigger]}
        self.event_dict = event_dict
        self.arguments_dict = arguments_dict
        self.trigger_dict = trigger_dict
        self.n_event = n_event
        self.max_argument = max_argument
        self.complex_score = complex_score
        self.use_chain = use_chain

        self.event_definition = StaticTamplate.event_definition
        self.annotation_protocol = StaticTamplate.annotation_protocol
        self.event_relations_rule = StaticTamplate.event_relations_rule
        self.validation_checklist = StaticTamplate.validation_checklist
        self.trigger_details = StaticTamplate.trigger_details
        self.complexity_control = StaticTamplate.complexity_control
        self.event_detail = ''
        self.example = StaticTamplate.example
        self.task = ''

        self.task_ins = '\nGenerate 1 compliant passage following ALL constraints(output only).'
        self.event_list = []
        self.chain = []

        self.minimum_arg_dict = util.load_json(minimum_arg_fn)
        try:
            self.rec_dict = util.load_json('./ori_data/record_dict_.json')
        except:
            pass
            # print('no orignal record')
            self.rec_dict = {}

        self.event_schema = {}
        for k in event_dict:
            self.event_schema[k] = []
            for r in event_dict[k][1]:
                self.event_schema[k].append(r)

        self.event_chains = util.load_pickle(event_chains)
        self.role_relations = util.load_pickle(role_relations)
            
    def update(self, main_event, n_event=None, max_argument=None, complex_score=None):
        
        if n_event:
            self.n_event = n_event
        if max_argument:
            self.max_argument = max_argument
        if complex_score:
            self.complex_score = complex_score
        # event_list = list(self.event_dict.keys())
        # event_list.remove(main_event)
        if len(main_event):
            self.random_event_chain(main_event)
        else:
            self.event_list = []

    def get_chains(self, main_event):
        event_chains = []
        for i in range(2, self.n_event + 1):
            for chain in self.event_chains[i]:
                if util.capitalize_event('{}:{}'.format(self.event_dict[main_event][-1], main_event)) in chain:
                    event_chains.append(chain)
        return event_chains
        
    def random_event_chain(self, main_event):
        event_list = []
        chain = []
        event_chains = self.get_chains(main_event)
        if event_chains:
            chain = random.choice(event_chains)
            event_list = chain[::2]
        if len(event_list) < self.n_event:
            event_list.extend(self.random_select_list(list(self.event_dict.keys()), self.n_event - len(event_list)))
        self.event_list = [util.skip_main_event(e) for e in event_list]
        if main_event not in self.event_list:
            self.event_list[-1] = main_event
        self.chain = [util.skip_main_event(e) for e in chain]
            
    def role_de(self, role_dict):# no skip
        role_des = ''
        for i, role in enumerate(role_dict, 1):
            if role.upper() == 'TIME':
                continue
            definition = role_dict[role][0]
            role_des += '\n\t\t{}: {}'.format(role, definition)
        return role_des

    def gen_event_detail(self):
        event_detail = '''\nEvent Specifications:'''
        event_des = ''
        for i, event in enumerate(self.event_list, 1):
            event_detail += event + ', '
            definition = self.event_dict[event][0]
            role_dict = self.event_dict[event][1]
            event_p = '\n\tDefinition for {}: {}'.format(event, definition)
            event_des = event_des + event_p + '\n\tArguments definition for {}:'.format(event) + self.role_de(role_dict)

        return event_detail + event_des
    
    def gen_complex_score(self, a, b):
        assert a < b and a > 1 and b <= 10
        return random.randint(a, b)
    
    def random_select_list(self, l, max):
        if not len(l):
            return []
        temp_l = copy.deepcopy(l)
        selected_l = []
        while max:
            if not len(temp_l):
                break
            elem = random.choice(temp_l)
            selected_l.append(elem)
            temp_l.remove(elem)
            max -= 1
        return selected_l
    
    def random_select_role(self, event, role_list, max_role):
        if self.use_chain:
            minimum_arg = self.minimum_arg_dict[event]
            diff_list = list(set(role_list).difference(set(minimum_arg))) # minimum argument roles
            if max_role > len(minimum_arg):
                random_list = (self.random_select_list(diff_list, max_role - len(minimum_arg)))
                random_list.extend(minimum_arg)
            elif max_role == 0:
                random_list = []
            else:
                random_list = minimum_arg
            return random_list
        else:
            if max_role > 0:
                random_list = self.random_select_list(role_list, max_role)
            else:
                random_list = []
            return random_list

    def event_from_ori(self, event):
        return random.choice(self.rec_dict[event])['event_1']
    
    def gen_event_record(self, event, role_list, max_role):
        trigger = random.choice(self.trigger_dict[event])

        event_record = {"event": event, "trigger": trigger}
        argument_S = {
                    }
        selected_role = self.random_select_role(event, role_list, max_role)
        for role in selected_role:
            if not role in list(self.arguments_dict[event]):
                continue
            n_arguments = self.get_n_argument(self.max_argument)
            if role.upper() == 'TIME':
                continue
                n_arguments = 1
            if role.upper() == 'PLACE':
                n_arguments = 1
            # select argument
            candidate_list = self.arguments_dict[event][role]
            arg_list = self.random_select_list(candidate_list, n_arguments)
            argument_S[role] = arg_list
        event_record["argument"] = argument_S

        return event_record

    def gen_events_record(self):
        record = {}
        for i, event in enumerate(self.event_list, 1):
            role_dict = self.event_dict[event][1]
            role_list = list(role_dict.keys())
            max_role = min(self.get_max_role(4), len(role_list))  # len(role_list) - random.randint(0, len(role_list))
            event_record = self.gen_event_record(event, role_list, max_role)
            if self.rec_dict:
                print('getting orignal record...')
                record['event_{}'.format(i)] = self.event_from_ori(event)
                continue
            record['event_{}'.format(i)] = event_record
        if self.use_chain:
            record = self.unify_arguments(record)
        return record

    def gen_complexity_score_str(self):
        complexity_score = '''\tFinally, given complexity score:
        \t  semantic = {0},
        \t  lexical = {0},
        \tAnd event record:'''.format(self.gen_complex_score(self.complex_score[0], self.complex_score[1]))

        return complexity_score

    def get_data_prompt(self):
        # argument select
        # event_dict = {'ATTACK':[event_def, role_dict, example, exam_trigger]}

        record = self.gen_events_record()
        lang = ''
        event_relations_rule = ''
        if self.use_chain:
            lang = '\n\tNatural language form of Event Record:\n\t' + self.relate_lang(record)
            event_relations_rule = self.event_relations_rule
        self.task = '\nTask Execution\n\tYour Input:\n\t' + json.dumps(record) + lang + self.task_ins

        self.event_detail = self.gen_event_detail()

        event_record_prompt = self.event_definition + self.trigger_details + self.annotation_protocol + event_relations_rule + self.validation_checklist + self.complexity_control+ self.event_detail + self.example + self.task

        return [event_record_prompt, json.dumps(record)]
    
    def get_check_rec_prompt(self):
        # argument select
        # event_dict = {'ATTACK':[event_def, role_dict, example, exam_trigger]}

        record = self.gen_events_record()
        self.task = '\nTask Execution\n\tYour Input:\n\t' + record + '\n\tdecide if the record is reasonable'

        self.event_detail = self.gen_event_detail()

        event_record_prompt ='Event Record Cheak Task' + self.event_definition.replace('Event Extraction Sentence Generation Task', '') + self.event_detail + self.trigger_details + self.task

        return [event_record_prompt, record]
    
    # def get_data_next_prompt(self):
    #     record = self.gen_events_record()
    #     self.task = record + self.task_ins
    #
    #     self.event_detail = self.gen_event_detail()
    #
    #     event_record_prompt = self.task
    #
    #     return [event_record_prompt, record]
    
        
    def get_n_argument(self, max_argument):
        weight_dict = {  1:[1],
                    2:[0.9, 0.1],
                    3:[0.9, 0.15, 0.05],
                    4:[0.9, 0.2, 0.1, 0.1]
                      }
        assert max_argument != 0
        return random.choices([ i for i in range(1, max_argument + 1)], weights=weight_dict[max_argument])[0]

    def get_max_role(self, n):
        if n == 0:
            return 0
        weight_dict = {  1:[0.1, 0.9],
                    2:[0.1, 0.5, 0.4],
                    3:[0.1, 0.3, 0.3, 0.3],
                    4:[0.1, 0.15, 0.15, 0.3, 0.2]
                      }
        return random.choices([ i for i in range(0, n + 1)], weights=weight_dict[n])[0]

    def struct2lang(self, e):

        struct2lang_map = {
        'BE-BORN': '<Person> was <trigger> in <Place>',
        'MARRY': '<Person> <trigger> in <Place>',
        'DIVORCE': '<Person> <trigger> in <Place>',
        'INJURE': '<Agent> <trigger> to <Victim> injured by <Instrument> in <Place>',
        'DIE': '<Agent> <trigger> to <Victim> died by <Instrument> in <Place>',
        'TRANSPORT': '<Artifact> was <trigger> to <Destination> from <Origin> by <Vehicle>. <Agent> was responsible for the transport',
        'TRANSFER-OWNERSHIP': '<Buyer> <trigger> <Artifact> from <Seller> in <Place>',
        'TRANSFER-MONEY': '<Giver> <trigger> <Recipient> in <Place>',
        'START-ORG': '<Agent> <trigger> <Org> in <Place>',
        'MERGE-ORG': '<Org> was <trigger>',
        'DECLARE-BANKRUPTCY': '<Org> <trigger>',
        'END-ORG': '<Org> <trigger>',
        'ATTACK': '<Attacker> <trigger> <Target> by <Instrument> in <Place>',
        'DEMONSTRATE': '<Entity> <trigger> at <Place>',
        'MEET': '<Entity> <trigger> at <Place>',
        'PHONE-WRITE': '<Entity> <trigger> at <Place>',
        'START-POSITION': '<Person> <trigger> new job and was hired by <Entity> in <Place>',
        'END-POSITION': '<Person> <trigger> working for <Entity> at <Place>',
        'NOMINATE': '<Person> was <trigger> by <Agent> to do a job',
        'ELECT': '<Person> was <trigger> a position, and the election was voted by <Entity> in <Place>',
        'ARREST-JAIL': '<Person> was <trigger> by <Agent> in <Place>',
        'RELEASE-PAROLE': '<Person> was <trigger> by <Entity> from <Place>',
        'TRIAL-HEARING': '<Defendant>, <trigger> by <Prosecutor>, faced a trial in <Place>. The hearing was judged by <Adjudicator>',
        'CHARGE-INDICT': '<Defendant> was <trigger> by <Prosecutor> in <Place>. The adjudication was judged by <Adjudicator>',
        'SUE': '<Defendant> was <trigger> by <Plaintiff> in <Place>. The adjudication was judged by <Adjudicator>',
        'CONVICT': '<Defendant> was <trigger> of a crime in <Place>. The adjudication was judged by <Adjudicator>',
        'SENTENCE': '<Defendant> was <trigger> to punishment in <Place>. The adjudication was judged by <Adjudicator>',
        'FINE': '<Entity> in <Place> was <trigger> by <Adjudicator> to pay a fine',
        'EXECUTE': '<Person> was <trigger> by <Agent> at <Place>',
        'EXTRADITE': '<Person> was <trigger> to <Destination> from <Origin>. <Agent> was responsible for the extradition',
        'ACQUIT': '<Defendant> was <trigger> of the charges by <Adjudicator>',
        'PARDON': '<Defendant> <trigger> a pardon from <Adjudicator>',
        'APPEAL': '<Plaintiff> in <Place> <trigger> the adjudication from <Adjudicator>'
        }
        
        event = e['event']
        trigger = e['trigger']
        tamplet = struct2lang_map[event]
        tamplet = re.sub('<trigger>', trigger, tamplet)
        arguments = e['argument']
        for role, args in arguments.items():
            span = ''
            for arg in args:
                if not span:
                    span += '<{0}>{1}</{0}>'.format(role, arg)
                else:
                    span += '<{0}>{1}</{0}>, '.format(role, arg)
            tamplet = re.sub('<{}>'.format(role), span, tamplet)
        
        return tamplet

    def relate_lang(self, record):
        sen = ''
        chain = [i for i in self.chain]
        print(self.chain)
        for _, r in record.items():
            replace = 0
            event = r['event']
            for j in range(len(chain)):
                if chain[j] == event:
                    chain[j] = self.struct2lang(r)
                    replace = 1
                    break
            # if not replace:
            else:
                chain.append('somehow'.upper())
                chain.append(self.struct2lang(r))
        for s in chain:
            if not sen:
                sen += s
            else:
                sen = sen + ', ' + s
        return sen

    def unify_arguments(self, event_record):
        # 创建事件记录的深拷贝以避免修改原始数据
        new_record = {eid: {'event': info['event'], 
                            'trigger': info['trigger'],
                            'argument': dict(info['argument'])} 
                     for eid, info in event_record.items()}

        for category, groups in self.role_relations.items():
            for group in groups:
                # 存储组内所有论元位置和值
                mention_cunt = {}
                
                # 收集组内所有出现的论元
                for role_pattern in group:
                    try:
                        event_type, role = role_pattern.split(':')
                    except:
                        # print(role_pattern)
                        continue
                    role = role.strip('<>')  # 移除尖括号
                    event_type = event_type.upper()  # 统一大写
                    
                    # 查找匹配的事件
                    for eid, info in new_record.items():
                        if info['event'] == event_type:
                            mention_cunt[role_pattern] = {}
                            mention_cunt[role_pattern][eid] = event_type
                            if role in info['argument']:
                                mention_cunt[role_pattern][role] = info['argument'][role][0]
                cnt = 0
                if len(mention_cunt) == len(group):
                    role = ''
                    arg = []
                    for k, v in mention_cunt.items():
                        if len(v) == 2:
                            role = list(v.keys())[-1]
                            arg.append(v[role])
                        cnt += len(v)
                    cnt = cnt / len(mention_cunt)
                    if cnt > 1:
                        mention = random.choice(arg)
                        for k, v in mention_cunt.items():
                            role = k.split(':')[-1].replace('<', '').replace('>', '')
                            v[role] = mention
                            new_record[list(v.keys())[0]]['argument'][role] = [mention]

        arg_locations = []
        all_values = []
        
        lower_chain = [c.lower() for c in self.chain]
        for eid, info in new_record.items():
            if info['event'].lower() in lower_chain and 'Place' in info['argument']:
                value = info['argument']['Place'][0]  # 取第一个论元值
                arg_locations.append((eid, 'Place'))
                all_values.append(value.lower())  # 统一小写比较
        if len(set(all_values)) > 1:
            # 找出最常见的值
            counter = Counter(all_values)
            most_common = counter.most_common(1)[0][0]
            for eid, role in arg_locations:
                new_record[eid]['argument'][role] = [most_common]
        
        # 遍历所有约束组
        for category, groups in self.role_relations.items():
            for group in groups:
                # 存储组内所有论元位置和值
                arg_locations = []
                all_values = []
                
                # 收集组内所有出现的论元
                for role_pattern in group:
                    # 解析事件类型和论元角色 (格式: "EVENT-TYPE:<Role>")
                    try:
                        event_type, role = role_pattern.split(':')
                    except:
                        # print(role_pattern)
                        continue
                    role = role.strip('<>')  # 移除尖括号
                    event_type = event_type.upper()  # 统一大写
                    
                    # 查找匹配的事件
                    for eid, info in new_record.items():
                        if info['event'] == event_type and role in info['argument']:
                            value = info['argument'][role][0]  # 取第一个论元值
                            arg_locations.append((eid, role))
                            all_values.append(value.lower())  # 统一小写比较
                
                # 如果组内有多个不同值，则进行统一
                if len(set(all_values)) > 1:
                    # 找出最常见的值
                    counter = Counter(all_values)
                    most_common = counter.most_common(1)[0][0]
                    # 统一所有论元值为最常见值
                    for eid, role in arg_locations:
                        new_record[eid]['argument'][role] = [most_common]

        for event_id in new_record:
            event = new_record[event_id]['event']
            syn_role = [role for role in new_record[event_id]['argument']]
            real_role = self.event_schema[event]
            for role in syn_role:
                if role not in real_role:
                    new_record[event_id]['argument'].pop(role)
                        
        return new_record
