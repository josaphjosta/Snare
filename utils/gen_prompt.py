import os
import re
import pickle

from DataPrompt import DataPrompt


class Prompt:
    def __init__(self, event_dict=None, arguments_dict=None, n_event=None, max_argument=None, complex_score=None, trigger_dict=None, use_chain=True):
        self.data_prompt = DataPrompt(event_dict = event_dict,
                                      arguments_dict = arguments_dict,
                                      trigger_dict = trigger_dict,
                                      n_event = n_event, 
                                      max_argument = max_argument, 
                                      complex_score = complex_score,
                                      use_chain=use_chain)
        self.event_dict = self.data_prompt.event_dict

    def gen_trigger_prompt(self, n_trigger, event_type, event_def, example, exam_trigger):
        return '''\tAn Event’s Trigger is the word (in its scope) that most clearly expresses its occurrence. 
        \tPlease generate at last {0} trigger words for event type {1}. Here is the definition of event Type {1} and example of a passage which contains a trigger word.
        \n\tDefinition: {2}
        \n\tExample: \'{3}\'. The trigger for event type {1} in this sentence is {4}.
        \n\tNote that:
        \n\t\t1. The generated trigger can only be a single word.
        \n\t\t2. More trigger words were generated that did not begin with a capital letter (non-special words, specific names of people, places, etc.) than others.

        \n\tThe data format of your answer should be organized as JSON (e.g. {{"triggers": [\"trigger_1\", \"trigger_2\", …]}})'''.format(
            n_trigger, event_type, event_def, example, exam_trigger)

    def gen_argument_promt(self, n_argument, event_type, event_def, role_dict):
        event = '\tGiven event type {0} and its definition:\n\t{0}: {1}'.format(event_type, event_def)
        task = '\n\tPlease generate arguments corresponding to the event type {0} and the definitions of each argument role given below (argument should be classified to one argument role only). That is, to answer those questions:'.format(
            event_type)
        task_ins = '''\n\tNote that:
        \t1. Try to generate more one-word arguments than others.\n\t2. More arguments were generated that did not begin with a capital letter (non-special words, specific names of people, places, etc.) than others.\n\t3.The data format of your answer should be organized as JSON (e.g. {"Attacker": {"sub_role_1":["someone_1", "someone_2", …], …}, "Target": {"sub_role_1":["something_1", "something_2", …],…}, …})\n\t4.''' + 'Each sub-role(marked as <sub_roles>sub_role_1/sub_role_2</sub_roles>) of an argument role should have at last {0} arguments.'.format(n_argument)
        prompt = event + task
        for i, role in enumerate(role_dict, 1):
            definition = role_dict[role][0]
            entities = role_dict[role][1]
            prompt += '\n\t{0}.Given the definition of {1} argument role as ‘{2}’, what are some possible names of <sub_roles>{3}</sub_roles> that can be used as {1}?'.format(
                i, role, definition, entities)
        prompt += task_ins

        return prompt

    def gen_chat_prompt(self, n, type='T'):
        '''
        T for trigger,
        A for argument
        '''
        if type == 'T':
            return 'Give me other {} trigger words. please aovid any duplicates'.format(n)
        elif type == 'A':
            return 'Give me other {} arguments per argument role. please aovid any duplicates'.format(n)
        return ''

    def gen_data_prompt(self, main_event, update=True, n_event=None, max_argument=None, complex_score=None):
        if update:
            self.data_prompt.update(main_event, n_event, max_argument, complex_score)
        return self.data_prompt.get_data_prompt()

    def gen_event_record(self, main_event, update=True, n_event=None, max_argument=None, complex_score=None):
        if update:
            self.data_prompt.update(main_event, n_event, max_argument, complex_score)
        return self.data_prompt.gen_events_record()

