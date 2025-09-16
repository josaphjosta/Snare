class StaticTamplate():
    event_definition = '''
Event Extraction Sentence Generation Task

Core Definitions
1. **Event**: An objective fact describing interactions between participants at specific time/location  
2. **Event Type**: Classification label (e.g., ELECT) determining argument structure  
3. **Trigger**: Explicit event indicator (verb/nominalized verb) that **must use past tense**  
4. **Arguments**: Core elements with semantic roles (e.g., Person/Entity/Time/Place)'''
    
    trigger_details = '''
Trigger Annotation Rules
    Key Requirements:
     Quantitative Limitation: Only one trigger per sentence
     Tense Enforcement: NO future tense actions described for any events(while conditional tense is granted)
     Three Trigger Patterns:
      a) Main verb: "Protesters <trigger>clashed</trigger> with police"
      b) Adjective/Participle: "The <trigger>convicted</trigger> politician resigned"
      c) Modifier: "Newly-<trigger>elected</trigger> officials convened"
      d) Nominalized: "New <trigger>explosions</trigger> rock Baghdad after dark ."
      e) Simple Present Tense verb: "Protesters <trigger>clash</trigger> with police"'''
    
    task_requirement = '''
Annotation Protocol:
    <EVENT><trigger>won</trigger></EVENT>, where EVENT means the event given in **Event Specifications**, and <trigger></trigger> is static
    <EVENT_1><EVENT_2><trigger>won</trigger></EVENT_1></EVENT_2>, if some events has the same span of trigger
    <EVENT><ROLE>voters</ROLE></EVENT>, where EVENT means the event given in **Event Specifications**, and ROLE means the correspondent argument role for the EVENT and its arguments.
    <EVENT_1><EVENT_2><ROLE>won</trigger></ROLE></EVENT_2>, if some events has the same span of argument
    
Validation Checklist
    1.No future tense verbs present
    2.All provided arguments explicitly tagged
    3.Trigger words match past tense requirement
    4.No imaginary/hypothetical scenarios
    5.Target in your OUTPUT should be wrapped in JSON(e.g. {"sentences":["output sentences"]})
    '''
    
    complexity_control = '''
Complexity Control
    Constraints:
        1.Trigger and arguments must remain unchanged (exact words/phrases provided in input).
        2.Complexity is adjusted only through:
            Lexical: Vocabulary richness around the fixed trigger/arguments.
    
    
    Metric for Lexical Complexity:
        Description	Example (Fixed trigger: "bomb", Arguments: state, team, warplanes)
        Lexical=1:	Basic syntax, minimal modifiers.(e.g., "The state bombed the team with warplanes.")
        Lexical=2:	Moderate adjectives/adverbs, prepositional phrases.(e.g., "The state violently bombed the fleeing team using advanced warplanes.")
        Lexical=3:	Advanced diction, figurative language, or technical terms.(e.g., "The state executed a relentless bombing campaign, decimating the beleaguered team via supersonic warplanes.")
    Default Complexity Request: If unspecified, generate at Lexical=3.'''
    
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
            "In yesterday's special election, the <ELECT><Entity>district</Entity></ELECT> of <ELECT><Place>Ohio</Place></ELECT> successfully <ELECT><trigger>voted</trigger></ELECT> to fill the congressional seat vacancy."
          ]
        }
    '''