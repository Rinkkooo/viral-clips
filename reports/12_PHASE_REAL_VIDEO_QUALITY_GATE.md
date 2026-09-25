# Отчет Фазы 12: Real Video Quality Gate (Реальное Видеоядро без Моков)

## 1. Архитектурная Цель и Контекст
Ликвидировать все симуляции, захардкоженные таймкоды, синтетические транскрипты и статические псевдо-кропы, выявленные в ходе аудита. Перевести систему Viral Clips в режим **Real Video Quality Gate**, где на каждом этапе пайплайна работают исключительно реальные нейросетевые модели и математические алгоритмы обработки медиа.

**Аппаратное окружение:**
- GPU: NVIDIA GeForce RTX 4060 Laptop GPU (8GB GDDR6 VRAM, CUDA Compute 8.9)
- Политика параллелизма: Strict GPU concurrency = 1 (взаимное исключение ASR, Face Tracking и NVENC)
- Платформа: Windows 11, Python 3.12, FFmpeg 7.1 with `h264_nvenc`, Faster-Whisper, MediaPipe FaceMesh / OpenCV YuNet, Ollama Local LLM

---

## 2. Реализованные Компоненты и Архитектура

### 2.1. Речевой Тракт: Faster-Whisper ASR (CUDA FP16)
- **Модель:** `Systran/faster-whisper-small` (локально кэширована в `.cache/huggingface/hub`).
- **Вычисления:** Автоматический запуск на CUDA в режиме `float16` с fallback на CPU `int8`.
- **Автоопределение Языка:** Поддержка `language="auto"` (или `None`), возврат метаданных:
  - `requested_language`: Запрошенный режим (`auto`, `ru`, `en`).
  - `detected_language`: Фактически распознанный язык (например, `ru`, `en`, `ja`).
  - `language_probability`: Вероятность детекции (0.0 — 1.0).
- **Quality Gate:** Полный запрет на подстановку фейковых/захардкоженных транскриптов в dev/prod. При тишине возвращается пустой список слов, при поврежденном файле генерируется `ASRError(code="ASR_FAILED")`.
- **Артефакт:** Сохранение `transcript.json` с полным word-level таймингом и метаданными ASR.

### 2.2. Оценка Виральности: Модульный LLM Провайдер и Pydantic Structured Output
- **Архитектура Провайдеров (`viral_clips.core.llm_providers`):**
  - Абстрактный протокол `HighlightLLMProvider`.
  - `OllamaHighlightLLM`: Локальный инференс без интернета (`qwen2.5:1.5b` / `qwen2.5:7b`), автоопределение доступной модели через `/api/tags`.
  - `GeminiHighlightLLM`: Облачный провайдер Gemini Flash/Pro.
  - `OpenAIHighlightLLM`: Облачный провайдер OpenAI GPT-4o-mini.
  - `HeuristicHighlightLLM`: Быстрый локальный ранжировщик по плотности речи и ключевым словам, **строго защищенный** конфигурационным флагом `ALLOW_HEURISTIC_LLM_FALLBACK=false`.
- **Структурированный Вывод:**
  - Pydantic-модель `CandidateScore` с валидацией 7 виральных измерений по шкале 0–10:
    - `hook_strength`, `emotional_intensity`, `narrative_coherence`, `value_per_minute`, `topic_clarity`, `stand_alone_viability`, `pacing_energy`.
  - Нормированная формула композитного скора (0–100) с весами `VIRAL_WEIGHTS` (сумма = 100):
    $$\text{FinalScore} = \sum_{i=1}^{7} (\text{score}_i \times \text{weight}_i) \times 10$$
- **Сегментация и Преранжирование:**
  - Окно кандидатов: 20–90 секунд с шагом 5 секунд.
  - Heuristic pre-ranking до топ-15 кандидатов перед отправкой в LLM (экономия токенов и ускорение батча).
- **Артефакты:** Сохранение `candidates.json` и `ranking.json` с фиксацией используемого провайдера, имени модели и флага `fallback_used`.

### 2.3. Интеллектуальное Кадрирование (Smart Reframe) и FFmpeg Render
- **Динамическая Траектория:**
  - Детекция лиц через MediaPipe Face Mesh / OpenCV YuNet с сохранением таймкодов и центров масс $(x_c, y_c)$.
  - Сглаживание экспоненциальным фильтром с коэффициентом $\alpha = 0.20$.
  - Зона нечувствительности (dead-zone) 12% для предотвращения дрожания камеры при микродвижениях головы.
  - Сброс сглаживания при смене планов (scene cuts), обнаруженных FFmpeg `select=gt(scene\,0.3)`.
- **Аналитическая Интерполяция в FFmpeg Filtergraph:**
  - Построение аналитического выражения с вложенными кусочно-линейными функциями `lerp(a, b, t)` непосредственно внутри фильтра `crop=w=...:h=...:x=...:y=...`.
  - Отрисовка в целевое разрешение 1080x1920 (9:16).
  - Верифицировано тестом `test_ffmpeg_vertical_render_has_real_pixel_motion`: абсолютная разность кадров в начале и середине клипа $> 0$ при панорамировании.
- **Аппаратное Ускорение:** Приоритет `h264_nvenc` с fallback на `libx264`.
- **Артефакт:** Генерация `render_manifest.json` с фиксацией кодека, разрешения, точек траектории и флага `has_dynamic_trajectory`.

### 2.4. Караоке-Субтитры
- **Пословная Синхронизация:** Точная привязка слов к границам клипа (clamping к $[0, \text{clip\_duration}]$).
- **Кастомные Шрифты:** Поддержка переопределения `font_family`, `font_size`, `primary_colour`, `outline_colour`.
- **Артефакт:** Сохранение `subtitle_manifest.json` с метаданными пресета и шрифтов.

### 2.5. Human Review Scorecard & Fast Rerender
- **Таблица БД `clip_reviews`:**
  - Поля: `framing_score` (1-5), `subtitle_score` (1-5), `hook_score` (1-5), `pacing_score` (1-5), `overall_score` (1-5), `is_publishable` (bool), `reviewer_notes` (text).
- **REST API:**
  - `POST /v1/clips/{clip_id}/review` — сохранение оценки эксперта.
  - `GET /v1/clips/{clip_id}/review` — получение аналитики оценки.
- **Быстрый Перерендер:**
  - `POST /v1/clips/{clip_id}/rerender` с возможностью изменить кадрирование или субтитры без повторного прогона ASR и LLM.

### 2.6. Modern Web UI Studio
- **Языковой селектор:** Добавлена опция `✨ Автоопределение (Auto detect)` по умолчанию.
- **Model Transparency Cards:** Виджеты в интерфейсе, наглядно отображающие используемые модели (Faster-Whisper CUDA, Ollama Qwen 2.5, Dynamic Face Mesh, NVENC) и красные предупреждающие бейджи при включении heuristic fallback.
- **Интерактивный Scorecard:** Форма оценки клипа оператором прямо в модальном окне плеера.

---

## 3. Верификация и Тестирование

### 3.1. Автоматизированный Набор Тестов
Все тесты проекта разделены на тематические сьюты и успешно проходят:
1. `tests/test_real_quality_gate.py` — **9 / 9 PASSED**
   - Проверка Faster-Whisper ASR auto-detect и структуры метаданных
   - Строгая ошибка при отсутствии речи/ASR без фейкового фоллбэка
   - Валидация Pydantic `CandidateScore` (диапазон 0–10, типы)
   - Контроль запрета / разрешения эвристического фоллбэка LLM
   - Корректность синтаксиса `lerp()` выражений в FFmpeg crop
   - Реальное смещение пикселей (динамический кроп) при вертикальном рендере
   - Проверка генерации `subtitle_manifest.json` и `render_manifest.json`
   - Интеграция API Human Review Scorecard в SQLite
2. `tests/test_audit_remediation.py` — **9 / 9 PASSED**
3. `tests/test_core_and_pipeline.py` — **8 / 8 PASSED**
4. `tests/test_storage_security_beta.py` — **7 / 7 PASSED**

**Итоговый статус автотестов:** 33 / 33 PASSED (100%).

---

## 4. Результат
Все замечания аудита от 2026-09-23 устранены. Система полностью избавлена от моков в ядре и готова к промышленной обработке реальных видеопотоков.
