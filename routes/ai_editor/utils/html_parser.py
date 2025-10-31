import re
from typing import Dict


def extract_from_html(html: str) -> Dict[str, str]:
    """Возвращает body, styles, scripts из HTML части, удаляя дубликаты оболочек."""
    if not html:
        return {"body": "", "styles": "", "scripts": ""}

    text = html.strip()

    # Удаляем возможный DOCTYPE и обертки html/head
    text = re.sub(r"<!DOCTYPE[^>]*>", "", text, flags=re.IGNORECASE)

    # Собираем стили
    styles = "\n".join(
        m.group(1).strip()
        for m in re.finditer(r"<style[^>]*>([\s\S]*?)</style>", text, flags=re.IGNORECASE)
    )

    # Собираем скрипты (только JS, без type проверки для простоты)
    scripts = "\n".join(
        m.group(1).strip()
        for m in re.finditer(r"<script[^>]*>([\s\S]*?)</script>", text, flags=re.IGNORECASE)
    )

    # Вырезаем style/script из фрагмента
    text_wo_assets = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
    text_wo_assets = re.sub(r"<script[\s\S]*?</script>", "", text_wo_assets, flags=re.IGNORECASE)

    # Достаем содержимое body если есть
    body_match = re.search(r"<body[^>]*>([\s\S]*?)</body>", text_wo_assets, flags=re.IGNORECASE)
    if body_match:
        body = body_match.group(1).strip()
    else:
        # Если нет body, пробуем убрать <html>/<head>
        tmp = re.sub(r"<head[\s\S]*?</head>", "", text_wo_assets, flags=re.IGNORECASE)
        tmp = re.sub(r"</?html[^>]*>", "", tmp, flags=re.IGNORECASE)
        body = tmp.strip()

    return {"body": body, "styles": styles, "scripts": scripts}

