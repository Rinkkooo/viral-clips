"""
Long-Form Science Script Generator powered by Qwen 2.5 7B.
Generates an 8-10 minute (~1200-1500 word) documentary script with 7 dramatic chapters,
deep suspense, escalations, open loops, and visual cues.
"""

import json
import urllib.request
from dataclasses import dataclass
from typing import List, Dict, Any
from loguru import logger


@dataclass
class DocumentaryChapter:
    chapter_num: int
    title: str
    target_duration_s: float
    visual_theme: str
    narration_text: str


@dataclass
class LongFormDocumentary:
    title: str
    total_words: int
    chapters: List[DocumentaryChapter]
    full_text: str


SYSTEM_PROMPT = """Ты — ведущий сценарист и научный консультант мирового уровня для документальных научно-популярных фильмов (в стиле Kurzgesagt, Veritasium, Discovery, AdMe и Топлес).
Твоя задача — написать фундаментальный, захватывающий сценарий на русском языке для 8-10 минутного видео на тему:
"Что произойдет, если швейная игла врежется в Землю на скорости света?"

ПРАВИЛА И СТИЛЬ:
1. Язык: богатый, литературный, эмоциональный и научно безупречный русский язык.
2. Никаких детских клише и примитивных фраз. Используй кинематографичные метафоры, создавай саспенс и напряжение.
3. Каждая глава должна заканчиваться интригующим переходом (open loop), заставляющим зрителя затаить дыхание.
4. Разбей сценарий строго на 7 глав:
   Глава 1: Иллюзия безобидности (Швейная игла 5 мг. Почему интуиция нас обманывает?)
   Глава 2: Ловушка масштабов (Сравнение скоростей: пуля 1000 м/с, метеорит 20 км/с, и непостижимые 300 000 км/с)
   Глава 3: Проклятие Эйнштейна: Девятки после запятой (Фактор Лоренца, релятивистский рост массы, частица Oh-My-God)
   Глава 4: Атмосферный коллайдер (Столкновение с воздухом. Почему игла не коснется земли? Ядерный распад и плазменный вакуумный клин)
   Глава 5: Судный день в стратосфере (Масштабы детонации: Хиросима, Царь-Бомба, астероид Чикшулуб. Сейсмический удар и выжженный озон)
   Глава 6: Точка сингулярности: Что если ровно 100% c? (Бесконечная масса, гравитационный коллапс, гибель причинности и времени)
   Глава 7: Космический брандмауэр (Философский катарсис: скорость света как главный защитник Вселенной от самоуничтожения)

ФОРМАТ ОТВЕТА:
Верни строго валидный JSON со следующей структурой:
{
  "title": "...",
  "chapters": [
    {
      "chapter_num": 1,
      "title": "...",
      "visual_theme": "space_needle",
      "narration_text": "Текст диктора для этой главы..."
    },
    ...
  ]
}
Только JSON, без лишнего вступительного и заключительного текста."""


def generate_documentary_script_with_qwen7b(
    ollama_url: str = "http://localhost:11434/api/generate",
    model: str = "qwen2.5:7b"
) -> LongFormDocumentary:
    """
    Invokes Qwen 2.5 7B to generate a comprehensive 7-chapter documentary script.
    """
    logger.info(f"Querying {model} via Ollama for 8-10 min documentary script...")
    
    user_prompt = (
        "Напиши полный, подробный и глубокий сценарий для 8-10 минутного фильма (примерно 1200-1400 слов текста диктора). "
        "В тексте каждой главы подробно объясняй физику, приводи точные числа и сравнения, держи зрителя в сильном напряжении. "
        "Верни строго JSON."
    )
    
    payload = {
        "model": model,
        "prompt": f"{SYSTEM_PROMPT}\n\nПользовательский запрос:\n{user_prompt}",
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 4096,
            "num_ctx": 8192
        }
    }
    
    req = urllib.request.Request(
        ollama_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    with urllib.request.urlopen(req, timeout=300) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        raw_text = res.get("response", "{}")
        
    data = json.loads(raw_text)
    
    chapters: List[DocumentaryChapter] = []
    full_paragraphs = []
    
    for ch in data.get("chapters", []):
        chapter = DocumentaryChapter(
            chapter_num=ch.get("chapter_num", len(chapters) + 1),
            title=ch.get("title", f"Глава {len(chapters) + 1}"),
            target_duration_s=75.0,  # ~1.25 min per chapter
            visual_theme=ch.get("visual_theme", "space_needle"),
            narration_text=ch.get("narration_text", "").strip()
        )
        chapters.append(chapter)
        full_paragraphs.append(chapter.narration_text)
        
    full_text = "\n\n".join(full_paragraphs)
    total_words = len(full_text.split())
    
    logger.success(f"Documentary script successfully generated! Chapters: {len(chapters)}, Total Words: {total_words}")
    return LongFormDocumentary(
        title=data.get("title", "Игла на скорости света: Анатомия невозможной катастрофы"),
        total_words=total_words,
        chapters=chapters,
        full_text=full_text
    )


if __name__ == "__main__":
    doc = generate_documentary_script_with_qwen7b()
    print("TITLE:", doc.title)
    print("TOTAL WORDS:", doc.total_words)
    for c in doc.chapters:
        print(f"[{c.chapter_num}] {c.title} ({len(c.narration_text.split())} words)")
