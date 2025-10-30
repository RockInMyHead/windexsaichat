import json
from typing import Dict
from ..models import ArchitectPlan, DesignStyle, PlanStep, get_design_style_variation
from ..prompts.architect_prompts import ArchitectPromptBuilder
from utils.openai_client import openai_client


class ArchitectService:
    """Сервис для создания архитектурных планов веб-сайтов"""

    def __init__(self, prompt_builder: ArchitectPromptBuilder = None):
        self.prompt_builder = prompt_builder or ArchitectPromptBuilder()

    async def create_plan(self, user_request: str, mode: str) -> ArchitectPlan:
        """Создает план разработки для пользовательского запроса"""
        print(f"🏗️ Architect LLM: Planning architecture for mode '{mode}'")

        # Получаем случайный стиль дизайна для разнообразия
        design_style = get_design_style_variation()
        print(f"🎨 Selected design style: {design_style.name}")

        # Создаем промпт
        prompt = self.prompt_builder.build_prompt(design_style, user_request, mode)

        try:
            # Вызываем LLM
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_request}
                ],
                temperature=0.9
            )

            content = response.choices[0].message.content
            print(f"🏗️ Architect response: {content[:200]}...")
            print(f"🏗️ Full architect response length: {len(content)} characters")

            # Парсим JSON ответ
            plan_data = json.loads(content)
            plan = ArchitectPlan(**plan_data)

            print(f"🏗️ Successfully parsed architect plan with {len(plan.steps)} steps")
            for i, step in enumerate(plan.steps, 1):
                print(f"🏗️ Step {i}: {step.name} ({step.code_type})")

            return plan

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse architect response: {e}")
            return self._create_fallback_plan(user_request, mode)
        except Exception as e:
            print(f"❌ Architect LLM error: {e}")
            return self._create_fallback_plan(user_request, mode)

    def _create_fallback_plan(self, user_request: str, mode: str) -> ArchitectPlan:
        """Создает базовый план при ошибке LLM"""
        fallback_steps = [
            PlanStep(
                id=1,
                name="Создание хедера с навигацией",
                description="Создать шапку сайта с логотипом и меню навигации",
                code_type="html",
                priority="high",
                dependencies=[]
            ),
            PlanStep(
                id=2,
                name="Создание hero-секции",
                description="Создать главную секцию с заголовком и призывом к действию",
                code_type="html",
                priority="high",
                dependencies=[1]
            ),
            PlanStep(
                id=3,
                name="Создание основного контента",
                description="Создать секции с основным контентом сайта",
                code_type="html",
                priority="high",
                dependencies=[2]
            ),
            PlanStep(
                id=4,
                name="Создание футера",
                description="Создать подвал сайта с контактной информацией",
                code_type="html",
                priority="medium",
                dependencies=[3]
            ),
            PlanStep(
                id=5,
                name="Добавление стилей",
                description="Добавить CSS стили для всех секций",
                code_type="css",
                priority="high",
                dependencies=[4]
            ),
            PlanStep(
                id=6,
                name="Добавление интерактивности",
                description="Добавить JavaScript для интерактивных элементов",
                code_type="javascript",
                priority="medium",
                dependencies=[5]
            )
        ]

        return ArchitectPlan(
            analysis=f"Создание {mode} проекта по запросу: {user_request}",
            steps=fallback_steps,
            final_structure="Единый HTML файл с встроенными CSS и JavaScript"
        )

