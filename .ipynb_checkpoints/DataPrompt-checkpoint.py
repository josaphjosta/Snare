import os
import random
import copy
import json
from utils import util

from StaticTamplate import StaticTamplate


class DataPrompt:
    def __init__(self, event_dict=None, trigger_dict=None, arguments_dict=None, n_event=None, max_argument=None, complex_score=None, minimum_arg_fn = './meta_data/minimum_argument_dict.json'):
        # event_dict = {'ATTACK':[event_def, role_dict, example, exam_trigger]}
        self.event_dict = event_dict
        self.arguments_dict = arguments_dict
        self.trigger_dict = trigger_dict
        self.n_event = n_event
        self.max_argument = max_argument
        self.complex_score = complex_score

        self.event_definition = StaticTamplate.event_definition
        self.task_requirement = StaticTamplate.task_requirement
        self.trigger_details = StaticTamplate.trigger_details
        self.event_detail = ''
        self.example = StaticTamplate.example
        self.task = ''

        self.task_ins = '\nGenerate 1 compliant sentence following ALL constraints.'
        self.event_list = []

        self.minimum_arg_dict = util.load_json(minimum_arg_fn)
        try:
            self.rec_dict = util.load_json('./ori_data/record_dict_.json')
        except:
            print('no orignal record')
            self.rec_dict = {}
            
    def update(self, main_event, n_event=None, max_argument=None, complex_score=None):
        
        if n_event:
            self.n_event = n_event
        if max_argument:
            self.max_argument = max_argument
        if complex_score:
            self.complex_score = complex_score
        event_list = list(self.event_dict.keys())
        event_list.remove(main_event)
        self.event_list = self.random_select_list(event_list, self.n_event - 1)
        if len(main_event):
            self.event_list.append(main_event)
        else:
            self.event_list = []
            
    def role_de(self, role_dict):# no skip
        role_des = ''
        for i, role in enumerate(role_dict, 1):
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
        minimum_arg = self.minimum_arg_dict[event]
        diff_list = list(set(role_list).difference(set(minimum_arg)))
        if max_role > len(minimum_arg):
            random_list = (self.random_select_list(diff_list, max_role - len(minimum_arg)))
            random_list.extend(minimum_arg)
        elif max_role == 0:
            random_list = []
        else:
            random_list = minimum_arg
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
        return json.dumps(record)

    def gen_complexity_score_str(self):
        complexity_score = '''\tFinally, given complexity score:
        \t  semantic = {0},
        \t  lexical = {0},
        \t  Argument relation = {0}
        \tAnd event record:'''.format(self.gen_complex_score(self.complex_score[0], self.complex_score[1]))

        return complexity_score

    def get_data_prompt(self):
        # argument select
        # event_dict = {'ATTACK':[event_def, role_dict, example, exam_trigger]}

        record = self.gen_events_record()
        self.task = 'Task Execution\n\tYour Input:\n\t' + record + self.task_ins

        self.event_detail = self.gen_event_detail()

        event_record_prompt = self.event_definition + self.event_detail + self.trigger_details + self.task_requirement + self.example + self.task

        return [event_record_prompt, record]
    
    def get_check_rec_prompt(self):
        # argument select
        # event_dict = {'ATTACK':[event_def, role_dict, example, exam_trigger]}

        record = self.gen_events_record()
        self.task = 'Task Execution\n\tYour Input:\n\t' + record + '\n\tdecide if the record is reasonable'

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
