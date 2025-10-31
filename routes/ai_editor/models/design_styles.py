from typing import List
from pydantic import BaseModel, validator


class DesignStyle(BaseModel):
    name: str
    colors: List[str]
    gradients: List[str]
    effects: List[str]


class PlanStep(BaseModel):
    id: int
    name: str
    description: str
    code_type: str  # "html" | "css" | "javascript"
    priority: str   # "high" | "medium" | "low"
    dependencies: List[int]

    @validator('code_type')
    def validate_code_type(cls, v):
        if v not in ['html', 'css', 'javascript']:
            raise ValueError('code_type must be html, css, or javascript')
        return v

    @validator('priority')
    def validate_priority(cls, v):
        if v not in ['high', 'medium', 'low']:
            raise ValueError('priority must be high, medium, or low')
        return v


class ArchitectPlan(BaseModel):
    analysis: str
    steps: List[PlanStep]
    final_structure: str


# Design styles library for variety
DESIGN_STYLES = {
    "modern_minimalist": DesignStyle(
        name="Современный минимализм",
        colors=["#ffffff", "#f8f9fa", "#6c757d", "#343a40"],
        gradients=["linear-gradient(135deg, #667eea 0%, #764ba2 100%)"],
        effects=["чистые линии", "много белого пространства", "минималистичная типографика"]
    ),
    "dark_futuristic": DesignStyle(
        name="Темный футуризм",
        colors=["#0a0a0a", "#1a1a1a", "#00ff88", "#0088ff"],
        gradients=["linear-gradient(45deg, #0a0a0a 0%, #1a1a1a 50%, #0a0a0a 100%)"],
        effects=["неоновые акценты", "темная тема", "голографические эффекты"]
    ),
    "vibrant_creative": DesignStyle(
        name="Яркий креатив",
        colors=["#ff6b6b", "#4ecdc4", "#45b7d1", "#f9ca24"],
        gradients=["linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #f9ca24)"],
        effects=["яркие цвета", "игривые анимации", "креативные формы"]
    ),
    "elegant_luxury": DesignStyle(
        name="Элегантная роскошь",
        colors=["#2c3e50", "#34495e", "#e74c3c", "#f39c12"],
        gradients=["linear-gradient(135deg, #2c3e50 0%, #34495e 100%)"],
        effects=["золотые акценты", "элегантная типографика", "роскошные тени"]
    ),
    "nature_organic": DesignStyle(
        name="Природная органика",
        colors=["#27ae60", "#2ecc71", "#16a085", "#f1c40f"],
        gradients=["linear-gradient(135deg, #27ae60 0%, #2ecc71 100%)"],
        effects=["органические формы", "природные цвета", "мягкие переходы"]
    ),
    "tech_cyberpunk": DesignStyle(
        name="Техно-киберпанк",
        colors=["#000000", "#ff0080", "#00ffff", "#ffff00"],
        gradients=["linear-gradient(45deg, #000000 0%, #ff0080 50%, #00ffff 100%)"],
        effects=["киберпанк-эстетика", "неоновые эффекты", "технологичные элементы"]
    )
}


def get_design_style_variation():
    """Возвращает случайный стиль дизайна для разнообразия"""
    import random
    style_key = random.choice(list(DESIGN_STYLES.keys()))
    return DESIGN_STYLES[style_key]
