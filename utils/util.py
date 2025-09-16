import os
import re
import json
import pickle


def parse_trigger_answer(answer):
    try:
        s = re.findall(r'triggers\s*=\s*(\[.*?\])', answer)[0]
        l = json.loads(s)
        assert type(l) == type([])
        return l
    except:
        print('error processing trigger answer -- ', answer)
        return []


def parse_argument_answer(answer):
    try:
        s = re.findall(r'arguments\s*=\s*({.*?})', answer)[0]
        l = json.loads(s)
        assert type(l) == type({})
        return l
    except:
        print('error processing argument answer -- ', answer)
        return {}


def save_pickle(event_obj, fn):
    with open(fn, 'wb') as f:
        pickle.dump(event_obj, f)


def load_pickle(fn):
    with open(fn, 'rb') as f:
        event_obj = pickle.load(f)
    return event_obj


def save_json(event_obj, fn):
    with open(fn, 'w', encoding='utf-8') as f:
        json.dump(event_obj, f)


def load_json(fn):
    with open(fn, 'r', encoding='utf-8') as f:
        event_obj = json.load(f)
    return event_obj


def capitalize_event(s):
    s_l = s.strip().split(':')
    f_e = s_l[0].capitalize()
    s_ee = ''
    for s_e in s_l[1].split('-'):
        s_ee += s_e.capitalize() + '-'
    return f_e + ':' + s_ee[:-1]


def skip_main_event(s):
    s_l = s.strip().split(':')
    s_ee = ''
    for s_e in s_l[-1].split('-'):
        s_ee += s_e.upper() + '-'
    return s_ee[:-1]


def generate_result_json(event_data, event_definitions, miss_only):
    results = {}

    event_type = event_data['event']
    trigger = event_data['trigger']
    arguments = event_data['argument']

    # Get roles from event definition
    definition_roles = event_definitions.get(event_type, {})
    simplified_roles = [role.split('-')[0] for role in definition_roles.keys()]

    # 1. Build mention_exist
    mention_exist = {trigger: "Yes"}
    for role, mentions in arguments.items():
        for mention in mentions:
            mention_exist[mention + '_of_' + role] = "Yes"

    # 2. trigger_initiate_occurrence
    trigger_initiate_occurrence = "Yes"

    # 3. argument_describing_event
    argument_describing_event = {}
    argument_describing_event[trigger] = 'Yes'
    for role, mentions in arguments.items():
        for mention in mentions:
            argument_describing_event[mention + '_of_' + role] = 'Yes'

            # 4. argument_should_not_appear
    argument_should_not_appear = {}
    for role in simplified_roles:
        if role not in arguments.keys():
            argument_should_not_appear[role] = '"No" OR the spotted untagged argument spans'

    # Build final result structure
    results = {
        "mention_exist": mention_exist,
        "trigger_initiate_occurrence": trigger_initiate_occurrence,
        "argument_describing_event": argument_describing_event,
        "argument_should_not_appear": argument_should_not_appear
    }
    if miss_only:
        argument_should_not_appear = {}
        for role in simplified_roles:
            argument_should_not_appear[role] = '"No" OR the spotted untagged argument spans'
        results = {
            "argument_should_not_appear": argument_should_not_appear
        }
    return results


def generate_questions(event_data, arg_role_definition, miss_only=False):
    """Generate validation questions for an event record"""
    questions = []
    event_type = event_data['event']
    trigger = event_data['trigger']
    arguments = event_data['argument']

    # Extract and simplify role names from definition
    roles = list(arg_role_definition[event_type].keys())
    simple_roles = [role.split('-')[0] for role in roles]
    if not miss_only:
    # Base questions about trigger
        questions.extend([
            f"is the trigger mention '{trigger}' a subsequence of the passage?",
            f"is the trigger '{trigger}' used to semantically initiate occurrence '{event_type}'?"
        ])
        for role in arguments:
            for arg in arguments[role]:
                questions.append(
                    f"Is '{arg}' a argument of role '{role}' describing the event '{event_type}' triggered by '{trigger}'?", )
        # Role-specific questions
        for role in simple_roles:
            if role not in arguments.keys():
                questions.append(
                    f"is the passage containing tagged or not tagged span that could serve as an argument '{role}' for event triggered by '{trigger}' but should not appear?"
                )
    else:
        for role in simple_roles:
            # if role not in arguments.keys():
            questions.append(
                f"is the passage containing tagged or not tagged span that could serve as an argument '{role}' for event triggered by '{trigger}' but should not appear?"
            )
    q = 'for event {} triggered by {}\n'.format(event_type, trigger)
    q += '\n'.join(questions)

    result_json = generate_result_json(event_data, arg_role_definition, miss_only=miss_only)
    q += "\nCheck the list upon, return your answer with this dict in json:\n"
    q += json.dumps(result_json, indent=4)

    return q


def generate_problem_statements(result, event_data, arg_role_definition):
    problem_statements = {'rewrite': [],
                          'tag': []}
    event_type = event_data['event']
    trigger = event_data['trigger']
    arguments = event_data['argument']

    # Special trigger validation isinstance(event_sen.get(event), list)
    if isinstance(result.get("trigger_initiate_occurrence"), str):
        if result["trigger_initiate_occurrence"].upper() == "No".upper():
            problem_statements['rewrite'].append(
                f"event '{event_type}' is not properly triggered by '{trigger}', rewrite passage to ensure '{trigger}' correctly initiates occurrence '{event_type}'"
            )
    if isinstance(result.get("mention_exist"), dict):
        for arg_role, mention_exist in result["mention_exist"].items():
            if mention_exist.upper() == "No".upper() and len(arg_role.split('_of_')) == 2:
                arg, role = arg_role.split('_of_')
                for role_, args in arguments.items():
                    if arg in args:
                        role = role_
                problem_statements['rewrite'].append(
                    f"missing mention '{arg}' for event '{event_type}' triggered by '{trigger}', add this mention '{arg}' tagged as <{role}>{arg}</{role}> and appropriate content"
                )
    if isinstance(result.get("argument_describing_event"), dict):
        for arg_role, describing_event in result["argument_describing_event"].items():
            if arg_role == trigger and describing_event.upper() == "No".upper():
                problem_statements['rewrite'].append(
                    f"event '{event_type}' is missing trigger '{trigger}', rewrite passage to ensure '{trigger}' correctly initiates occurrence '{event_type}'"
                )

            if describing_event.upper() == "No".upper() and len(arg_role.split('_of_')) == 2:
                arg, role = arg_role.split('_of_')
                problem_statements['rewrite'].append(
                    f"'{event_type}' argument '{arg}' is not describing the event triggered by '{trigger}', rewrite passage to ensure '{arg}' correctly describes occurrence '{event_type}' triggered by '{trigger}'"
                )

    # Check for hallucinated arguments
    if isinstance(result.get("argument_should_not_appear"), dict):
        for role, should_not_appear in result["argument_should_not_appear"].items():
            if not isinstance(should_not_appear, list):
                continue

            for arg in should_not_appear:
                if arg.upper() != "No".upper():
                    problem_statements['tag'].append(
                        f"tag span \"{arg}\" with mere <{role}></{role}>  as an argument '{role}' for event '{event_type}' triggered by '{trigger}'"
                    )
                    if not event_data["argument"].get(role):
                        event_data["argument"][role] = []
                    event_data["argument"][role].append(arg)

    return problem_statements, event_data
