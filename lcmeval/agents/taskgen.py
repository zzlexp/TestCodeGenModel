from dataclasses import dataclass
from typing import Optional
from lcmeval.utils import LLM

SYSTEM_PROMPT = "You are a NumPy expert and proficient in the usage of various APIs of NumPy."

EXPLICIT_PROMPT_TEMPLATE = """You are given the following APIs of NumPy:

{api_details}

Your task is to generate a task that can be solved by calling these APIs.

Please follow the following rules:

1. The task should be a problem that can be solved by calling these APIs.
2. Explicitly ask the user to use numpy to solve the problem with these APIs.
3. Only include the API names in the task description.
4. Do not include any code in the task description.
5. The task should be clear and concise.
"""

IMPLICIT_PROMPT_TEMPLATE = """You are given the following APIs of NumPy:

{api_details}

Your task is to generate a task that can be solved by calling these APIs.

Please follow the following rules:

1. The task should be a problem that can be solved by calling these APIs.
2. Explicitly ask the user to use numpy to solve the problem.
3. Do not mention the APIs explicitly in the task description.
4. Do not include any code in the task description.
5. The task should be clear and concise.
"""


@dataclass
class Conversation:
    prompt: str
    response: str
    task: str
    think: Optional[str] = None


class TaskGenAgent:
    def __init__(self, prompt_template=EXPLICIT_PROMPT_TEMPLATE):
        self.prompt_template = prompt_template
        self.llm = LLM(system_prompt=SYSTEM_PROMPT)
        self.history = []

    def build_prompt(self, api_names, api_details):
        api_infos = ""
        for api_name in api_names:
            description = api_details[api_name]['description']
            parameters=api_details[api_name]["parameters"]
            api_infos += f"- {api_name}:\n  description: {description}\n  parameters: {parameters}\n"
        return self.prompt_template.format(api_details=api_infos.strip())

    def generate_task(self, api_names, api_details):
        prompt = self.build_prompt(api_names, api_details)
        completion = self.llm.query(prompt)
        content = completion.choices[0].message.content
        if not content:
            raise ValueError("The LLM did not return any content.")
        response = content.strip()
        if "</think>" in content:
            think, _, task = content.partition("</think>")
            task = task.strip()
            self.history.append(Conversation(prompt, response, task, think.strip()))
        else:
            task = content.strip()
            self.history.append(Conversation(prompt, response, task))
        return task


if __name__ == "__main__":
    from lcmeval.test_generation import coverage

    cov = coverage.CTAPICoverage.from_csv("lcmeval/crawler/numpy_apis/apis.csv", 1)
    api_names, api_details = cov.generate_api_combination()
    print(f"The selected APIS are: {api_names}")

    taskgen_agent = TaskGenAgent()
    task = taskgen_agent.generate_task(api_names, api_details)
    print(taskgen_agent.history[-1].prompt)
    print(f'The generated task is:\n\n{task}')

    cov.update_coverage((api_names))
