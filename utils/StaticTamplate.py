class StaticTamplate():
    event_definition = '''
Event Extraction Passage Generation Task

Core Definitions
    1. **Event**: An objective fact describing interactions between participants at specific time/location  
    2. **Event Type**: Classification label (e.g., ELECT) determining argument structure   
    3. **Arguments**: Core elements with semantic roles (e.g., Person/Entity/Time/Place)'''
    
    trigger_details = '''
Trigger Annotation Rules
    Key Requirements:
     Quantitative Limitation: Only one trigger per event instance
     Trigger Patterns:
      a) Main verb: "Protesters <EVENT_TYPE><trigger>clashed</trigger></EVENT_TYPE> with police"
      b) Adjective/Participle: "The <EVENT_TYPE><trigger>convicted</trigger></EVENT_TYPE> politician resigned"
      c) Nominalized: "New <EVENT_TYPE><trigger>explosions</trigger></EVENT_TYPE> rock Baghdad after dark ."
      d) Simple Present Tense verb: "Protesters <EVENT_TYPE><trigger>clash</trigger></EVENT_TYPE> with police"'''
    
    annotation_protocol = '''
Annotation Protocol:
     1.Event Trigger Tagging:
            <EVENT_TYPE><trigger>trigger_word</trigger></EVENT_TYPE>
        EVENT_TYPE = Event type from specifications
        <trigger> is a static tag
    2.Shared Triggers (Multiple Events):
            <EVENT_1><EVENT_2><trigger>shared_trigger</trigger></EVENT_2></EVENT_1>  
        Use nested tags when multiple events share the same trigger span
    3.Argument Role Tagging:
            <ROLE>argument_content</ROLE>  
        ROLE = Corresponding argument role from specifications
    4.Shared Arguments (Multiple Events):
            <ROLE>shared_argument</ROLE>
        Use nested tags when multiple events reference the same argument
    5. Arguments as Nouns:
       - Arguments must be treated as standalone nouns/noun phrases only
       - Never allow arguments to function as adjectives modifying other words
       - Example Correction:
         Incorrect: "<Attacker>Israeli</Attacker> forces conducted..." 
         Correct: "<Attacker>Israeli</Attacker> conducted..."
       - Exception: Proper nouns containing spaces (e.g., "Saddam Hussein") remain intact'''

    event_relations_rule = '''
Event Relations Rule
    When the Natural Language Form of Event Record specifies relations between events (e.g., "DELIVERS", "CAUSES", "SOMEHOW"), the generated passage must:
    1.Maintain chronological/logical flow to reflect the relation
    2.Never invent unstated relations
    Example:
        Input Relation(in Natural language): "description for TRANSPORT event, DELIVERS, description for ATTACK event"
        Valid Output: "After TRANSPORT, ATTACK occurred..."(SOMEHOW means any relation possible, even unrelated)
'''

    validation_checklist = '''
Validation Checklist
    1.Explicitly tag all arguments
    2.Arguments must be considered as noun
    3.Strictly follow event relations in the Event Record
    4.Identical argument mentions = same entity
        Example: {event_1:{Person: Obama}, event_2:{Attacker: Obama}} → Mention "Obama" once in output
    5.Omit empty role tags (e.g., <Person> in <Person> was elected)
    6.Wrap output in JSON: {"sentences":["output text"]}
    '''
    
    complexity_control = '''
Complexity Control
    Constraints:
        1.Trigger and arguments must remain unchanged (exact words/phrases provided in input).
        2.Non-restrictive Appositive is prohibited.
        3.Complexity is adjusted only through:
            Lexical: Vocabulary richness around the fixed trigger/arguments.
    Metric for Lexical Complexity:
        Description	Example (Fixed trigger: "bomb", Arguments: state, team, warplanes)
        Lexical=1:	Basic syntax, minimal modifiers.(e.g., "The state bombed the team with warplanes.")
        Lexical=2:	Moderate adjectives/adverbs, prepositional phrases.(e.g., "The state violently bombed the fleeing team using advanced warplanes.")
        Lexical=3:	Advanced diction, figurative language, or technical terms.(e.g., "The state executed a relentless bombing campaign, decimating the beleaguered team via supersonic warplanes.")
    Default Complexity Request: If unspecified, generate at Lexical=3.
    
    '''
    
    example = '''
Examples (Revised)
    Input:
        {
          "event_1": {
            "event": "ELECT",
            "trigger": "vote",
            "argument": {
              "Place": ["Ohio"],
              "Entity": ["district"]
            }
          }
        }
    Natural language form of Event Record:
		<Person> was vote a position, and the election was voted by <Entity>district</Entity> in <Place>Ohio</Place>
    Valid Output(JSON format):
         {
          "sentences": [
            "In yesterday's special election, the <Entity>district</Entity> of <Place>Ohio</Place> successfully <ELECT><trigger>voted</trigger></ELECT> to fill the congressional seat vacancy."
          ]
        }
    '''