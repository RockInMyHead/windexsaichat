import re
from typing import List
from ..models import PlanStep, CodePart
from ..prompts.developer_prompts import DeveloperPromptBuilder
from utils.openai_client import openai_client


class DeveloperService:
    """Сервис для генерации кода конкретных задач"""

    def __init__(self, prompt_builder: DeveloperPromptBuilder = None):
        self.prompt_builder = prompt_builder or DeveloperPromptBuilder()

    async def generate_code(self, task: PlanStep, mode: str, context: str = "") -> CodePart:
        """Генерирует код для конкретной задачи"""
        print(f"👨‍💻 Developer LLM: Generating {task.code_type} for task '{task.name}'")

        # Создаем промпт
        prompt = self.prompt_builder.build_prompt(task, mode, context)

        try:
            # Вызываем LLM
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Сгенерируй {task.code_type} код для: {task.description}"}
                ],
                temperature=0.8
            )

            code = response.choices[0].message.content.strip()

            # Очищаем код от markdown-разметки
            code = self._clean_markdown_formatting(code, task.code_type)

            print(f"👨‍💻 Developer generated {len(code)} characters of {task.code_type} code")
            print(f"👨‍💻 Developer response preview: {code[:100]}...")
            print(f"👨‍💻 Task '{task.name}' completed successfully")

            return CodePart(
                type=task.code_type,
                code=code,
                step_name=task.name
            )

        except Exception as e:
            print(f"❌ Developer LLM error: {e}")
            return self._get_error_fallback(task.code_type, task.name)

    def _clean_markdown_formatting(self, code: str, code_type: str) -> str:
        """Очищает код от markdown-разметки"""
        # Универсальная очистка от всех видов markdown-разметки
        patterns_to_remove = [
            rf'^```{code_type}\s*',  # ```javascript, ```css, ```html
            rf'^```js\s*',           # ```js
            rf'^```\s*',             # ```
            rf'\s*```$',             # ``` в конце
        ]

        for pattern in patterns_to_remove:
            code = re.sub(pattern, '', code, flags=re.MULTILINE | re.IGNORECASE)

        # Убираем лишние пробелы и переносы строк
        code = code.strip()

        print(f"🧹 Cleaned {code_type} code from markdown formatting")

        return code

    def _get_error_fallback(self, code_type: str, step_name: str = "Unknown") -> CodePart:
        """Возвращает fallback код при ошибке"""
        fallbacks = {
            "html": "<!-- Error generating html code -->",
            "css": "/* Error generating css code */",
            "javascript": "// Error generating javascript code"
        }
        return CodePart(
            type=code_type,
            code=fallbacks.get(code_type, f"<!-- Error generating {code_type} code -->"),
            step_name=step_name
        )
