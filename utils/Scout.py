import time
from utils.util import *


def get_local_time():
    return str(time.localtime().tm_mon) + '_' + str(time.localtime().tm_mday) + '_' + str(time.localtime().tm_hour) + '_' + str(time.localtime().tm_min)


def souts1_prompt(sen, event_dict):
    defin = ''
    event_type = []
    event_def = []

    for i, event in enumerate(event_dict, 1):
        event_type.append(event)
        event_def.append(event_dict[event][0].split('.')[0].replace(event, f'\"{event}\"'))

    events = 'Events of interests: [{}]'.format(', '.join(event_type))
    defin = '\n\t' + '\n\t'.join(event_def)
    task = '''
    Task Definition 
        You are an event detection system, looking to decide whether a sentence mentions or discusses an event from a specific list of events. 
    Full Event Ontology 
    '''

    query = '\nQuery \n\tDoes the following sentence discuss or mention any of the events of interest? \n\tsentence: \"{}\"'.format(
        sen)
    output = '\nOutPut Format: \n\toutput in json, e.g., {"events":[events sentence mentions or discusses]}'
    sout_s1 = task + events + defin + query + output
    return sout_s1


def souts2_promt(sen, event, event_dict):
    task = '''
    Task Definition 
        You are a writer, looking to extract a potential event trigger from a given sentence. Event trigger is the word that most clearly expresses the occurrence of the given event in the sentence. Event trigger is often only a single word in length. '''

    ontology = '\nRelated Event Ontology\n\tEvent of interest: \"{}\"\n\t {}'.format(event,
                                                                                     event_dict[event][0].split('.')[
                                                                                         0].replace(event,
                                                                                                    f'\"{event}\"'))

    query = '\nQuery\n\tGiven that the sentence mentions the event \"{}\", extract the trigger word in the sentence corresponding to this event type. \n\tsentence: \"{}\"'.format(
        event, sen)

    output = '\nOutPut Format: \n\toutput in json, e.g., {"{' + event + '}":[trigger words corresponding to this event type]}'

    sout_s2 = task + ontology + query + output
    return sout_s2


def souts3_promt(sen, event, trigger, event_dict):
    arg_de = ''
    for r, d in event_dict[event][1].items():
        arg_de += '\n\t\t{} means {}'.format(r, d[0])
    triggers = '" or "'.join(trigger)  # [:-6]

    record = {event: {}}
    for e, _ in event_dict[event][1].items():
        record[event][e] = ['arguments corresponding to this role']
    record = json.dumps(record, indent=1)

    task = '''
Task Definition 
        You are a writer, looking to extract potential event arguments from a given sentence. Event arguments in event extraction typically refer to entities, roles, or attributes linked to an event.  The most common form of event arguments is bare nouns without modification
'''

    ontology = '\nRelated Event Ontology\n\tEvent of interest: event:\"{}\"\n\tArguments of interest:{}'.format(event,
                                                                                                                arg_de)

    query = '\nQuery\n\tGiven that the sentence mentions the event \"{}\" triggered by \"{}\", extract all the possible event arguments in the sentence corresponding to this event type. \n\tsentence: \"{}\"'.format(
        event, triggers, sen)

    output = '\nOutPut Format: \n\toutput in json, e.g., \n{}'.format(record)

    sout_s3 = task + ontology + query + output
    return sout_s3

def narrator_prompt(event_record, event_dict):
    task = '''
Task Definition 
    You are an writer, looking to write sentences that contain specific events and event triggers. An event is a specific occurrence involving participants. An event is something that happens. An event can frequently be described as a change of state. Event trigger is the word that most clearly expresses its occurrence. Event triggers are often only a few words in length. 
    '''
    ontology = 'Related Event Ontology\n\t'
    query = '\nQuery \n\tGenerate a new sentence using '
    for e_id, r in event_record.items():
        event = r['event']
        trigger = r['trigger']
        ontology += f'\n\tA "{event}" event means: {event_dict[event][0]}'
        query += f'trigger "{trigger}" for event {event}, '
    output = '\nOutPut Format: \n\toutput in json, e.g., {"sentence": "generated sentence"}'
    return task + ontology + query[:-2] + '.' + output
    
def refiner_prompt(event_record, sen, event_dict):
    task = '''
Task Definition 
    This is an event extraction task where the goal is to extract structured events from the text. A structured event contains an event trigger word and an event type. 
Full Event Ontology'''
    ontology =  '\n\tEvents of interests:\n\t'
    for e_id, r in event_record.items():
        event = r['event']
        trigger = r['trigger']
        ontology += f'\n\tA "{event}" event means: {event_dict[event][0]}'
    query = '''
Query
    Below is a sentence from which you need to extract the events if any. Only output a list of tuples in the form [("event_type_1", "event_trigger_word_1"), ("event_type_2", "event_trigger_word_2"), ...] for each event in the sentence. 
    sentence: 
    '''
    query += f'"{sen}".'
    return task + ontology + query

