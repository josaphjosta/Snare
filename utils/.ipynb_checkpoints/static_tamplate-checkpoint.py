class StaticTamplate():
    event_definition = '''\nEvent Definition:
        An event record is consisted with one or many events. Each event has event type、trigger word and arguments to describe it. the definitions of those elements are:
        \t1.Event: An event is an objective fact describing the interaction of specific participants (e.g., people, organizations) at a specific time and place.
        \t2.Event type: Event Type refers to a category or label assigned to an event to classify its nature, purpose, or characteristics.
        \t3.Trigger: A trigger is a word (usually a verb or nominalized verb) that explicitly indicates the occurrence of an event. It determines the event type.
        \t4.Argument: Arguments are entities or phrases that describe the core elements of an event, such as participants, time, location, etc., each assigned a specific role (argument role).'''
    
    task_requirement = '''\nTask Requirement:
        The overall task requirement that to generate a given number of English sentences containing the event trigger words and arguments based on the given event record. Note that:
        \t1.A specific event type only related to one event in the generated sentence.
        \t2.do not generate arguments of certain roles if the user explicitly provide that “the argument is None” or not provided in the given event record.
        \t3.information from multiple events should be contained in a single passage.
        \t4.If the given event record is empty, you should return a sentence which is not having any events. 
        \t5.Your answer is sentences organized in JSON format (example below). Do not return any other information not required. '''
    
    complexity_control = '''\nComplexity Control:  
       Ensure sentence complexity scores (1–10) for:  
         \tSemantic: 1 = literal, 10 = abstract (e.g., "a storm of bullets").  
         \tLexical: 1 = common words, 10 = technical terms (e.g., "hypersonic missile").  
         \tArgument Relations: 1 = isolated roles, 10 = interdependent roles (e.g., "drones breached the embassy’s defenses'''
    
    example = '''\nExample:
        \tTo generate an English sentence from event record containing the event trigger words and arguments. The example is that:
        \tGiven complexity score:
            \t  semantic = 3,
            \t  lexical = 4,
            \t  Argument relation = 2
        \tAnd event record:
        \t  {
        \t  Attack: attacked
        \t    {
        \t    Target: [civilians, population],
        \t    Attacker: [regime]
        \t    }
        \t  }
        \tPlease generate 3 English sentence as required. The format of required English sentence is JSON.
        
        \tAnswer:
        \t  {"sentences": [
        \t    {"sentence": "We get reports that these <Target>civilians</Target> especially in the ( INAUDIBLE ) <Target>population</Target> have been attacked by the Iraqi <regime>regime</regime> themselves so they can't blame the American and said look what the American doing to us"},
        \t  …]
        \t  }'''