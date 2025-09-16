from StaticTamplate import StaticTamplate


class GenDataPrompt:
    def __init__(self, event_dict, arguments_dict, n_event, max_argument, complex_score, trigger_dict = None):
        # event_dict = {'ATTACK':[event_def, role_dict, example, exam_trigger]}
        self.event_dict = event_dict
        self.arguments_dict = arguments_dict
        if trigger_dict:# TO DO
            self.trigger_dict = trigger_dict
        else:
            self.trigger_dict = None
        self.n_event = n_event
        self.max_argument = max_argument
        self.complex_score = complex_score

        self.event_definition = StaticTamplate.event_definition
        self.task_requirement = StaticTamplate.task_requirement
        self.complexity_control = StaticTamplate.complexity_control
        self.event_detail = ''
        self.example = StaticTamplate.example
        self.task = '\nTask:\n'
        
    def role_de(self, role_dict):
        role_des = ''
        for i, role in enumerate(role_dict, 1):
            definition = role_dict[role][0]
            role_des += '\n\t\t\t**{}: {}'.format(role, definition)
        return role_des

    def event_de(self, event_dict):
        event_des = ''
        for i, event in enumerate(event_dict, 1):
            definition = event_dict[event][0]
            role_dict = event_dict[event][1]
            event_p = '\n\t{}.{}: {}.\n\t\tArguments:'.format(i, event, definition)
            event_des = event_des + event_p + role_de(role_dict)
        return event_des

    def gen_event_detail(self, event_dict):
        event_detail = '''\nEvent Detail:
        In the generated sentence, there should be {} events. The definitions of those event type are:'''.format(n_event)
        return event_detail + self.event_de(event_dict)
    
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
    
    def random_select_role(self, role_list, max_role):
        return self.random_select_list(role_list, max_role)

    def gen_event_record(self, role_list, max_role, max_argument):
        record = {}
        event = {"event": "Attack", "trigger": "war"}
        argument_S = {
                    }
        selected_role = self.random_select_role(role_list, max_role)
        for role in selected_role:
            arguments = random.randint(1, max_argument)
            candidate_list = arguments_dict[role]
            arg_list = self.random_select_list(candidate_list, arguments)
            argument_S[role] = arg_list
        event["argument"] = argument_S
        record["event_1"] = event
        event_record = json.dumps(record)
        return event_record
        
    def gen_complexity_score_str(self, complex_score):
        complexity_score = '''\tFinally, given complexity score:
        \t  semantic = {0},
        \t  lexical = {0},
        \t  Argument relation = {0}
        \tAnd event record:'''.format(self.gen_complex_score(complex_score[0], complex_score[1]))

    # argument select
    # event_dict = {'ATTACK':[event_def, role_dict, example, exam_trigger]}
    role_dict = self.event_dict['ATTACK'][1]
    role_list = list(role_dict.keys())
    max_role = random.randint(0, min(3, len(role_list))) #len(role_list) - random.randint(0, len(role_list))
    complexity_score = gen_complexity_score_str(complex_score)
    ins_t = '\n\tPlease generate 3 English sentence as required.'
    task = task + complexity_score + self.gen_event_record(role_list, max_role, max_argument) + ins_t
    event_detail = self.gen_event_detail(event_dict)
    event_record_prompt = event_definition + task_requirement + complexity_control + event_detail + example + task
