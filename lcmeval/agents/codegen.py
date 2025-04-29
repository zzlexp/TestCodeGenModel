from dataclasses import dataclass
from typing import Optional
from lcmeval.utils import LLM

SYSTEM_PROMPT = 'You are a NumPy expert and proficient in the usage of various APIs of NumPy.'

PROMPT_TEMPLATE = """You are given a task description and you need to generate code to solve the task.

{task}

Please follow the following rules:
1. The code should be a valid Python code that can be executed by the user.
2. The code should use the given numpy APIs to solve the task.
3. The code should be surrounded by <code> and </code> tags.
4. The code should be clear and concise."""


@dataclass
class Conversation:
    prompt: str
    response: str
    code: str
    think: Optional[str] = None


class CodeGenAgent:
    def __init__(self, prompt_template=PROMPT_TEMPLATE):
        self.prompt_template = prompt_template
        self.llm = LLM(system_prompt=SYSTEM_PROMPT)
        self.history = []

    def build_prompt(self, task):
        return self.prompt_template.format(task=task)

    def generate_code(self, task):
        prompt = self.build_prompt(task)
        completion = self.llm.query(prompt)
        content = completion.choices[0].message.content
        if not content:
            raise ValueError("The LLM did not return any content.")
        response = content.strip()
        if "</think>" in content:
            think, _, response = response.partition("</think>")
            code = response.partition("<code>")[2].partition("</code>")[0].strip()
            self.history.append(Conversation(prompt, response, code, think.strip()))
        else:
            code = response.partition("<code>")[2].partition("</code>")[0].strip()
            self.history.append(Conversation(prompt, response, code))
        return code


if __name__ == "__main__":
    from lcmeval.test_generation import coverage
    from lcmeval.agents.taskgen import TaskGenAgent

    cov = coverage.CTAPICoverage.from_csv("lcmeval/crawler/numpy_apis/apis.csv", 1)
    api_names, api_details = cov.generate_api_combination()
    print(f"The selected APIS are: {api_names}")

    taskgen_agent = TaskGenAgent()
    task = taskgen_agent.generate_task(api_names, api_details)
    print(taskgen_agent.history[-1].prompt)
    print(f'The generated task is:\n\n{task}')

    codegen_agent = CodeGenAgent()
    code = codegen_agent.generate_code(task)
    print(codegen_agent.history[-1].prompt)
    print(f'\nThe generated code is:\n\n{code}')

    cov.update_coverage((api_names))
