"""Problem generator that uses an LLM to craft NumPy-centric tasks."""

from dataclasses import dataclass
from typing import Tuple
from lcmeval.utils import LLM, extract_xml

SYSTEM_PROMPT = "You are a NumPy expert and proficient in the usage of various APIs of NumPy."

EXPLICIT_CRITERIA = """
1. The task should be a problem that can be solved by calling these APIs.
2. Explicitly ask the user to use numpy to solve the problem with these APIs.
3. Only include the API names in the task description.
4. Do not include any code in the task description.
5. The task should be clear and concise."""

IMPLICIT_CRITERIA = """
1. The task should be a problem that can be solved by calling these APIs.
2. Explicitly ask the user to use numpy to solve the problem.
3. Do not mention the APIs explicitly in the task description.
4. Do not include any code in the task description.
5. The task should be clear and concise."""

GENERATOR_PROMPT = """
Your goal is to generate a problem based on <apis>. If there are feedback from your previous generations, you should reflect on them to improve your solution.

Output your answer concisely in the following format:

<thoughts>
[Your understanding of the task and feedback and how you plan to improve]
</thoughts>

<response>
[Your generated problem description here]
</response>

Given the following NumPy APIs:
<apis>
{api_infos}
</apis>

Please follow the following criteria in your generation:
<criteria>
{criteria}
</criteria>"""

EVALUATOR_PROMPT = """
Evaluate the following problem description and determine if it meets the criteria of the original task.

{problem_description}

You should be evaluating only and not attemping to solve the problem.
Only output "PASS" if all criteria are met and you have no further suggestions for improvements.
Output your evaluation concisely in the following format.

<evaluation>PASS, NEEDS_IMPROVEMENT, or FAIL</evaluation>
<feedback>
What needs improvement and why.
</feedback>

Original task:
{task}
"""


class ProbGen:
    def __init__(self, system_prompt=SYSTEM_PROMPT, generator_prompt=GENERATOR_PROMPT, evaluator_prompt=EVALUATOR_PROMPT):
        self.generator_prompt = generator_prompt
        self.evaluator_prompt = evaluator_prompt
        self.llm = LLM(system_prompt=system_prompt)
        self.history = []

    def build_prompt(self, api_names, api_details):
        api_info_template = "- api_name: {api_name}\n  description: {description}\n  parameters: {parameters}"
        api_infos = []
        for api_name in api_names:
            api_infos.append(api_info_template.format(
                api_name=api_name,
                description=api_details[api_name]['description'],
                parameters=api_details[api_name]["parameters"],
            ))
        return self.generator_prompt.format(api_infos="".join(api_infos), criteria=EXPLICIT_CRITERIA)

    def generate_problem_description(self, task: str) -> Tuple[str, str]:
        completion = self.llm.query(task)
        response = completion.choices[0].message.content
        if not response:
            raise ValueError("The LLM did not return any content.")
        response = response.strip()
        thoughts = extract_xml(response, "thoughts")
        problem_description = extract_xml(response, "response")

        print("\n=== GENERATION START ===")
        print(f"Thoughts:\n{thoughts}\n")
        print(f"Generated:\n{problem_description}")
        print("=== GENERATION END ===\n")

        return thoughts, problem_description

    def evaluate_problem_description(self, task: str, problem_description: str) -> Tuple[str, str]:
        evaluator_prompt = self.evaluator_prompt.format(task=task, problem_description=problem_description)
        completion = self.llm.query(evaluator_prompt)
        response = completion.choices[0].message.content
        if not response:
            raise ValueError("The LLM did not return any content.")
        evaluation = extract_xml(response, "evaluation")
        feedback = extract_xml(response, "feedback")

        print("=== EVALUATION START ===")
        print(f"Status: {evaluation}")
        print(f"Feedback: {feedback}")
        print("=== EVALUATION END ===\n")

        return evaluation, feedback

    def generate(self, api_names, api_details):
        memory = []
        chain_of_thought = []

        task_prompt = self.build_prompt(api_names, api_details)
        context = ""

        thoughts, problem = self.generate_problem_description(task_prompt)
        memory.append(problem)
        chain_of_thought.append({"thoughts": thoughts, "result": problem})

        while True:
            evaluation, feedback = self.evaluate_problem_description(f"{task_prompt}\n\n{context}", problem)
            if evaluation == "PASS":
                return problem

            context = "\n".join([
                "Previous attempts:",
                *[f"- {m}" for m in memory],
                f"\nFeedback: {feedback}",
            ])
            thoughts, problem = self.generate_problem_description(f"{task_prompt}\n\n{context}")
            memory.append(problem)
            chain_of_thought.append({"thoughts": thoughts, "result": problem})


if __name__ == "__main__":
    from lcmeval.test_generation import coverage

    cov = coverage.CTAPICoverage.from_csv("lcmeval/crawler/numpy_apis/apis.csv", 1)
    api_names, api_details = cov.generate_api_combination()
    if not api_names:
        raise ValueError("No API names were generated.")
    api_names = list(api_names)
    print("Selected APIs:")
    print("\n".join(f"- {api_name}" for api_name in api_names))

    probgen = ProbGen()
    problem = probgen.generate(api_names, api_details)
    print(f"The generated problem is: {problem}")
    cov.update_coverage(tuple(api_names))
