from typing import List, Optional
import json
import openai

def call_ai_function(function, args, description, model = "gpt-4"):
    # parse args to comma seperated string
    args = ", ".join(args)
    messages = [{"role": "system", "content": f"You are now the following python function: ```# {description}\n{function}```\n\nOnly respond with your `return` value."},{"role": "user", "content": args}]

    response = openai.ChatCompletion.create(        
        model=model,
        messages=messages,
        temperature=0
    )

    return response.choices[0].message["content"]

def summarize_goals(goal_info) -> str:
    function_string = "def summarize_goals(goal_info) -> str:"
    args = [json.dumps(goal_info)]
    description_string = """Returns a none technical and user friendly summary of the goal_info as a string."""

    result_string = call_ai_function(function_string, args, description_string)
    return result_string

def user_confirmation(userInputText) -> bool: 
    function_string = "def user_confirmation(userInputText) -> str: "
    args = [userInputText]
    description_string = """Analyzes the userInputText and returns a 'True' if the user says Yes or has confirmed. returns 'False' if the user says No or has not provided confirmation."""

    result_string = call_ai_function(function_string, args, description_string)
    if("true" in result_string.lower()):
        return True
    else:
        return False

def summarize_goals(goal_info) -> str:
    function_string = "def summarize_goals(goal_info) -> str:"
    args = [json.dumps(goal_info)]
    description_string = """Returns a none technical and user friendly summary of the goal_info as a string."""

    result_string = call_ai_function(function_string, args, description_string)
    print("summarize_goals " + result_string)
    return result_string

def get_question_to_get_more_info(goal) -> str:
    function_string = "def get_question_to_get_required_info_from_user(goal) -> str:"
    args = [goal]
    description_string = """Analyzes the goal and returns a question that asks for more information about the goal."""

    result_string = call_ai_function(function_string, args, description_string)
    print("get_question_to_get_more_info " + result_string)
    return result_string

def has_question_been_answered(question, answer) -> bool:
    function_string = "def has_question_been_answered_sufficently(question, answer) -> bool:"
    args = [question, answer]
    description_string = """Analyzes the question and returns 'True' if the question was answered by the 'answer', returns 'False' if the question was not answered."""

    result_string = call_ai_function(function_string, args, description_string)
    print("has_question_been_answered " + result_string)
    if("true" in result_string.lower()):
        return True
    else:
        return False    

def get_software_engineer_response_to_question(question) -> str:
    function_string = "def get_software_engineer_response_to_question(question) -> str:"
    args = [question]
    description_string = """Analyzes the question. Returns a short and precise answer to the 'question' from a software engineer. Never returns code, always returns an english sentence. software engineer does not deviate from the question and will provide opinionated technical answers. Example: 'You can use javascript, reactjs, html and css for programming languages and frameworks to build a website.'"""

    result_string = call_ai_function(function_string, args, description_string)
    print("get_software_engineer_response_to_question " + result_string)
    return result_string

def does_goal_require_more_info(goal) -> bool:
    function_string = "def does_goal_require_more_info_from_user(goal) -> bool:"
    args = [goal]
    description_string = """Analyzes the goal, returns 'True' if the goal is well described. returns 'False' if not."""

    result_string = call_ai_function(function_string, args, description_string)
    print("does_goal_require_more_info " + result_string)
    if("true" in result_string.lower()):
        return True
    else:
        return False

def get_goals_from_user_requirements(userInputText: str) -> List[str]:
    function_string = "def get_goals_from_user_requirements(userInputText: str) -> List[str]:"
    args = [userInputText]
    description_string = """Analyzes the userInputText and returns a list of high level steps that need to be implemented to achieve it. """

    result_string = call_ai_function(function_string, args, description_string)
    print("get_goals_from_user_requirements " + result_string)
    return json.loads(result_string)


def user_response_requires_code(userInputText: str) -> bool:
    function_string = "def user_response_requires_code(userInputText: str) -> bool"
    args = [userInputText]
    description_string = """Analyzes the userInputText and returns 'True' if this is a request to generate code, returns 'False' if not."""
    
    result_string = call_ai_function(function_string, args, description_string) # , model="gpt-3.5-turbo"

    if("true" in result_string.lower()):
        return True
    else:
        return False

### Evaluating code

def evaluate_code(code: str) -> List[str]:
    function_string = "def analyze_code(code: str) -> List[str]:"
    args = [code]
    description_string = """Analyzes the given code and returns a list of suggestions for improvements."""

    result_string = call_ai_function(function_string, args, description_string)
    return json.loads(result_string)


### Improving code

def improve_code(suggestions: List[str], code: str) -> str:
    function_string = "def generate_improved_code(suggestions: List[str], code: str) -> str:"
    args = [json.dumps(suggestions), code]
    description_string = """Improves the provided code based on the suggestions provided, making no other changes."""

    result_string = call_ai_function(function_string, args, description_string)
    return result_string


### Writing tests

def write_tests(code: str, focus: List[str]) -> str:
    function_string = "def create_test_cases(code: str, focus: Optional[str] = None) -> str:"
    args = [code, json.dumps(focus)]
    description_string = """Generates test cases for the existing code, focusing on specific areas if required."""

    result_string = call_ai_function(function_string, args, description_string)
    return result_string