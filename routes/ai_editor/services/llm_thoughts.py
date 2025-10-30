from typing import Dict, List
from datetime import datetime
from ..models import LLMThought


class LLMThoughtsManager:
    """Управление мыслями LLM для отслеживания прогресса генерации"""

    def __init__(self, max_thoughts: int = 20):
        self._thoughts: Dict[str, List[LLMThought]] = {}
        self._max_thoughts = max_thoughts

    def add_thought(self, conversation_id: str, icon: str, text: str):
        """Добавляет новую мысль для беседы"""
        if conversation_id not in self._thoughts:
            self._thoughts[conversation_id] = []

        thought = LLMThought(
            icon=icon,
            text=text,
            timestamp=datetime.now().isoformat()
        )

        self._thoughts[conversation_id].append(thought)

        # Ограничиваем количество мыслей
        if len(self._thoughts[conversation_id]) > self._max_thoughts:
            self._thoughts[conversation_id] = self._thoughts[conversation_id][-self._max_thoughts:]

    def get_thoughts(self, conversation_id: str) -> List[LLMThought]:
        """Получает все мысли для беседы"""
        return self._thoughts.get(conversation_id, [])

    def clear_thoughts(self, conversation_id: str):
        """Очищает мысли для беседы"""
        if conversation_id in self._thoughts:
            del self._thoughts[conversation_id]

    def cleanup_old_conversations(self, max_age_hours: int = 24):
        """Удаляет старые беседы (старше max_age_hours часов)"""
        current_time = datetime.now()
        conversations_to_remove = []

        for conversation_id, thoughts in self._thoughts.items():
            if thoughts:
                # Проверяем время последней мысли
                last_thought_time = datetime.fromisoformat(thoughts[-1].timestamp)
                age_hours = (current_time - last_thought_time).total_seconds() / 3600

                if age_hours > max_age_hours:
                    conversations_to_remove.append(conversation_id)

        for conversation_id in conversations_to_remove:
            del self._thoughts[conversation_id]


# Глобальный экземпляр менеджера мыслей
llm_thoughts_manager = LLMThoughtsManager()


async def send_llm_thought(conversation_id: str, icon: str, text: str):
    """Отправляет мысль LLM (для обратной совместимости)"""
    llm_thoughts_manager.add_thought(conversation_id, icon, text)

