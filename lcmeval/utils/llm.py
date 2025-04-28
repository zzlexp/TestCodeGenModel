import os
import yaml
from dataclasses import dataclass
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI, APITimeoutError
from openai.types import CompletionUsage
from openai.types.chat.chat_completion import ChatCompletion as Completion
from .config import CONFIG

__all__ = [
    'Completion',
    'APITimeoutError',
    'LLM',
    'Usage',
    'dump_completion',
]


class LLM:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.load_dotenv()
        self.client = OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=os.environ["OPENAI_API_BASE"],
            max_retries=CONFIG["max_retries"],
        )

    def load_dotenv(self):
        key_missing = "OPENAI_API_KEY" not in os.environ
        base_missing = "OPENAI_API_BASE" not in os.environ
        model_missing = "MODEL_ID" not in os.environ
        if key_missing or base_missing or model_missing:
            current_dir = os.getcwd()
            env_path = os.path.join(current_dir, '.env')
            if not os.path.exists(env_path):
                env_path = find_dotenv()
            load_dotenv(dotenv_path=env_path)

    def query(self, prompt: str) -> Completion:
        return self.client.chat.completions.create(
            model=os.environ["MODEL_ID"],
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            timeout=CONFIG["timeout"],
            max_completion_tokens=CONFIG["max_tokens"],
        )


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def __iadd__(self, other: 'Usage'):
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_tokens += other.total_tokens
        return self

    @classmethod
    def of(cls, usage: CompletionUsage) -> 'Usage':
        return cls(
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
        )

    def __str__(self) -> str:
        return f'input_toks: {self.prompt_tokens}, output_toks: {self.completion_tokens}, total_toks: {self.total_tokens}'


def dump_completion(file_path: str, completion: Completion, index: int):
    with open(file_path, 'a') as file:
        data = [{
            "index": index,
            "completion": completion.to_dict()
        }]
        file.write(yaml.dump(data, sort_keys=False))
