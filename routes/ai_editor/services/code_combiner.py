from typing import Dict, List
import re
from ..models import CodePart, CombinedCodeResult
from ..utils.html_parser import extract_from_html


class CodeCombiner:
    """Сервис для объединения частей кода в единый файл"""

    def __init__(self):
        self.base_css = self._get_base_css()
        self.base_html_template = self._get_base_html_template()

    async def combine_parts(self, parts: List[CodePart], mode: str) -> CombinedCodeResult:
        """Объединяет части кода в единый файл"""
        print(f"🔧 Combining {len(parts)} code parts for {mode} mode")

        if mode == "lite":
            content = await self._combine_lite_mode(parts)
            return CombinedCodeResult(
                content=content,
                parts_count=len(parts),
                total_length=len(content)
            )
        elif mode == "pro":
            content = await self._combine_pro_mode(parts)
            return CombinedCodeResult(
                content=content,
                parts_count=len(parts),
                total_length=len(content)
            )
        else:
            raise ValueError(f"Unsupported mode: {mode}")

    async def _combine_lite_mode(self, parts: List[CodePart]) -> str:
        """Объединяет части в единый HTML файл для lite режима"""
        html_body_fragments: List[str] = []
        css_parts: List[str] = []
        js_parts: List[str] = []

        for part in parts:
            print(f"🔧 Processing part: {part.type} - {len(part.code)} chars")
            if part.type == 'html':
                extracted = extract_from_html(part.code)
                if extracted['styles']:
                    css_parts.append(extracted['styles'])
                if extracted['scripts']:
                    js_parts.append(extracted['scripts'])
                html_body_fragments.append(extracted['body'])
            elif part.type == 'css':
                css_parts.append(part.code)
            elif part.type == 'javascript':
                # Иногда в ответ попадают мусорные маркеры 'css'/'html' — чистим
                code = re.sub(r"^\s*(html|css)\s*$", "", part.code, flags=re.IGNORECASE | re.MULTILINE)
                js_parts.append(code)

        print(f"🔧 Parts summary: {len(html_body_fragments)} HTML bodies, {len(css_parts)} CSS, {len(js_parts)} JS")

        # Объединяем в единый HTML файл
        html_content = ("\n".join(f for f in html_body_fragments if f)) or "<!-- Error generating html code -->"
        css_content = ("\n".join(c for c in css_parts if c)) or "/* No CSS generated */"
        js_content = ("\n".join(j for j in js_parts if j)) or "// No JavaScript generated"

        return self.base_html_template.format(
            css_content=self.base_css + "\n\n/* Combined CSS from generated parts */\n" + css_content,
            html_content=html_content,
            js_content=js_content
        )

    async def _combine_pro_mode(self, parts: List[CodePart]) -> str:
        """Объединяет части для pro режима (Next.js)"""
        # TODO: Implement Next.js project generation
        raise NotImplementedError("Pro mode not implemented yet")

    def _get_base_css(self) -> str:
        """Возвращает базовые CSS стили"""
        return """/* Modern CSS Reset */
*, *::before, *::after {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

/* CSS Variables for consistent design */
:root {
    --primary-color: #3b82f6;
    --secondary-color: #1e40af;
    --accent-color: #f59e0b;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --error-color: #ef4444;
    --text-color: #1f2937;
    --text-light: #6b7280;
    --text-muted: #9ca3af;
    --bg-color: #ffffff;
    --bg-light: #f9fafb;
    --bg-dark: #111827;
    --border-color: #e5e7eb;
    --border-light: #f3f4f6;
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    --border-radius: 8px;
    --border-radius-lg: 12px;
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    --transition-fast: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Base typography */
html {
    font-size: 16px;
    scroll-behavior: smooth;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--bg-color);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* Typography scale */
h1, h2, h3, h4, h5, h6 {
    font-weight: 600;
    line-height: 1.2;
    margin-bottom: 0.5em;
}

h1 { font-size: 2.5rem; }
h2 { font-size: 2rem; }
h3 { font-size: 1.5rem; }
h4 { font-size: 1.25rem; }
h5 { font-size: 1.125rem; }
h6 { font-size: 1rem; }

p {
    margin-bottom: 1rem;
}

/* Modern button styles */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    font-weight: 500;
    border-radius: var(--border-radius);
    border: none;
    cursor: pointer;
    transition: var(--transition);
    text-decoration: none;
    white-space: nowrap;
}

.btn-primary {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: white;
    box-shadow: var(--shadow);
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}

.btn-secondary {
    background: var(--bg-light);
    color: var(--text-color);
    border: 1px solid var(--border-color);
}

.btn-secondary:hover {
    background: var(--border-light);
    transform: translateY(-1px);
}

/* Container and layout */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1rem;
}

.section {
    padding: 4rem 0;
}

/* Card component */
.card {
    background: var(--bg-color);
    border-radius: var(--border-radius-lg);
    box-shadow: var(--shadow);
    padding: 2rem;
    transition: var(--transition);
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-xl);
}

/* Grid system */
.grid {
    display: grid;
    gap: 2rem;
}

.grid-2 { grid-template-columns: repeat(2, 1fr); }
.grid-3 { grid-template-columns: repeat(3, 1fr); }
.grid-4 { grid-template-columns: repeat(4, 1fr); }

/* Flex utilities */
.flex {
    display: flex;
}

.flex-center {
    display: flex;
    align-items: center;
    justify-content: center;
}

.flex-between {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* Spacing utilities */
.mb-1 { margin-bottom: 0.25rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-3 { margin-bottom: 0.75rem; }
.mb-4 { margin-bottom: 1rem; }
.mb-6 { margin-bottom: 1.5rem; }
.mb-8 { margin-bottom: 2rem; }

.mt-1 { margin-top: 0.25rem; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 0.75rem; }
.mt-4 { margin-top: 1rem; }
.mt-6 { margin-top: 1.5rem; }
.mt-8 { margin-top: 2rem; }

/* Text utilities */
.text-center { text-align: center; }
.text-left { text-align: left; }
.text-right { text-align: right; }

.text-primary { color: var(--primary-color); }
.text-secondary { color: var(--secondary-color); }
.text-muted { color: var(--text-muted); }"""

    def _get_base_html_template(self) -> str:
        """Возвращает базовый HTML шаблон"""
        return """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Website</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@300;400;500;600;700&family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        {css_content}

        /* Responsive design */
        @media (max-width: 1024px) {{
            .grid-4 {{ grid-template-columns: repeat(2, 1fr); }}
            .grid-3 {{ grid-template-columns: repeat(2, 1fr); }}
        }}

        @media (max-width: 768px) {{
            .container {{
                padding: 0 1rem;
            }}

            .grid-4, .grid-3, .grid-2 {{
                grid-template-columns: 1fr;
            }}

            h1 {{ font-size: 2rem; }}
            h2 {{ font-size: 1.75rem; }}
            h3 {{ font-size: 1.5rem; }}

            .section {{
                padding: 2rem 0;
            }}

            .card {{
                padding: 1.5rem;
            }}
        }}

        @media (max-width: 480px) {{
            .btn {{
                padding: 0.625rem 1.25rem;
                font-size: 0.875rem;
            }}

            h1 {{ font-size: 1.75rem; }}
            h2 {{ font-size: 1.5rem; }}
        }}
    </style>
</head>
<body>
    <!-- Combined HTML -->
    {html_content}

    <script>
        // Combined JavaScript
        {js_content}
    </script>
</body>
</html>"""
