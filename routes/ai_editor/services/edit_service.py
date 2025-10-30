import re
from ..models import ElementEditRequest, EditElementResponse
from utils.openai_client import openai_client


class EditService:
    """Сервис для редактирования элементов веб-страниц"""

    async def edit_element(self, request: ElementEditRequest) -> EditElementResponse:
        """Редактирование конкретного элемента"""
        try:
            edit_prompt = f"""
Ты - эксперт по веб-разработке и HTML/CSS.

**ЗАДАЧА:** Отредактируй элемент "{request.element_type}" в HTML коде.

**ТЕКУЩИЙ ТЕКСТ:** {request.current_text}
**ИНСТРУКЦИЯ ПО РЕДАКТИРОВАНИЮ:** {request.edit_instruction}
**ТЕКУЩИЙ HTML:** {request.html_content}

**ТРЕБОВАНИЯ:**
1. Сохрани структуру и стили
2. Примени изменения точно по инструкции
3. Убедись, что HTML остается валидным
4. Сохрани все классы и атрибуты

**ФОРМАТ ОТВЕТА:**
HTML_START
{{обновленный HTML код}}
HTML_END

RESPONSE_START
{{краткое описание изменений}}
RESPONSE_END
"""

            # Отправляем запрос к OpenAI
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты - эксперт по веб-разработке и HTML/CSS.",
                    },
                    {"role": "user", "content": edit_prompt},
                ],
                max_tokens=4000,
                temperature=0.7,
            )

            response_text = response.choices[0].message.content

            # Извлекаем HTML код из ответа
            html_match = re.search(
                r"HTML_START\s*(.*?)\s*HTML_END", response_text, re.DOTALL
            )
            response_match = re.search(
                r"RESPONSE_START\s*(.*?)\s*RESPONSE_END", response_text, re.DOTALL
            )

            if html_match:
                updated_html = html_match.group(1).strip()
                response_text = (
                    response_match.group(1).strip()
                    if response_match
                    else "Элемент успешно отредактирован."
                )

                return EditElementResponse(
                    html_content=updated_html,
                    response=response_text,
                    status="success",
                )
            else:
                return EditElementResponse(
                    html_content=request.html_content,
                    response="Не удалось извлечь обновленный HTML код.",
                    status="error",
                )

        except Exception as e:
            print(f"Ошибка редактирования элемента: {e}")
            return EditElementResponse(
                html_content=request.html_content,
                response=f"Ошибка редактирования: {str(e)}",
                status="error",
            )

