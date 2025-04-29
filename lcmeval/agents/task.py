from lcmeval.utils import LLM
from lcmeval.test_generation import coverage

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


class TaskAgent:
    def __init__(self, prompt_template=EXPLICIT_PROMPT_TEMPLATE):
        self.prompt_template = prompt_template
        self.llm = LLM(system_prompt=SYSTEM_PROMPT)

    def build_prompt(self, api_names, api_details):
        api_infos = ""
        for api_name in api_names:
            description = api_details[api_name]['description']
            parameters=api_details[api_name]["parameters"]
            api_infos += f"- {api_name}:\n  description: {description}\n  parameters: {parameters}\n"
        return self.prompt_template.format(api_details=api_infos)

    def generate_task(self, api_names, api_details):
        prompt = self.build_prompt(api_names, api_details)
        print(prompt)
        completion = self.llm.query(prompt)
        content = completion.choices[0].message.content
        task = content.split("</think>")[1].strip() if "</think>" in content else content.strip()
        return task


if __name__ == "__main__":
    cov = coverage.CTAPICoverage.from_csv("lcmeval/crawler/numpy_apis/apis.csv", 1)
    api_names, api_details = cov.generate_api_combination()
    print(f"The selected APIS are: {api_names}")
    task_agent = TaskAgent()
    task = task_agent.generate_task(api_names, api_details)
    print(f'The generated task is:\n\n{task}')
    cov.update_coverage((api_names))
