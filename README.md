# Viral Clips AI - Автоматическая Нарезка Длинных Видео в Шортсы

Сервис на базе AI для превращения горизонтальных длинных видео (подкасты, стримы, интервью) в вирусные вертикальные клипы 9:16 (Shorts, Reels, TikTok) с пословными караоке-субтитрами в стиле Алекса Хормози, автокадрированием и аппаратным ускорением на GPU.

---

## Быстрый Старт

### 1. Запуск Web UI Студии (в браузере)
```bash
# Установка переменной PYTHONPATH и запуск сервера
$env:PYTHONPATH="src"
python -m viral_clips.cli server --port 8000
```
После запуска откройте в браузере: **[http://localhost:8000](http://localhost:8000)**

Вам откроется темный дашборд студии (Linear/Vercel style), где можно:
- Создать проект и загрузить видео перетаскиванием (drag-and-drop).
- Выбрать пресеты кадрирования (Active Speaker / Blur Background) и стиль субтитров (Hormozi Gold / Green Pop / Minimal Box).
- Наблюдать за прогрессом обработки в реальном времени через Server-Sent Events (0–100%).
- Просматривать готовые ролики во встроенном вертикальном плеере 9:16 с радаром факторов виральности и скачивать их в 1 клик.

---

### 2. Запуск через CLI (Терминал)

#### Проверка окружения и GPU:
```bash
$env:PYTHONPATH="src"
python -m viral_clips.cli env-check
```

#### Валидация медиафайла (Probe):
```bash
python -m viral_clips.cli probe samples/sample_podcast.mp4
```

#### Полная нарезка видео в 9:16 клипы:
```bash
python -m viral_clips.cli process samples/sample_podcast.mp4 --clips 3 --framing blurred_background --subtitles bold_karaoke
```

---

### 3. Запуск Тестов (End-to-End)
```bash
$env:PYTHONPATH="src"
pytest tests/test_core_and_pipeline.py -v
```

---

## Архитектура и Отчеты по Фазам
Все подробные технические отчеты по каждой фазе реализации находятся в папке `reports/`:
- `reports/00_PHASE_0_ENVIRONMENT_AND_PROBE.md` — Окружение, обнаружение FFmpeg и NVENC на RTX 4060.
- `reports/01_PHASE_1_ASR_TRANSCRIPTION.md` — Извлечение звука 16 кГц и распознавание речи со словными таймкодами.
- `reports/02_PHASE_2_HIGHLIGHT_DETECTION.md` — Поиск кульминаций по 7 факторам виральности и диверсификация.
- `reports/03_PHASE_3_RENDER_AND_SUBTITLES.md` — Однопроходный рендер в 1080x1920 и генерация ASS субтитров Hormozi.
- `reports/04_PHASE_4_SMART_REFRAME.md` — Компьютерное зрение OpenCV и алгоритмы трекинга лица.
- `reports/05_PHASE_5_DATABASE_PERSISTENCE.md` — SQLite база данных, схема и кэширование артефактов.
- `reports/06_PHASE_6_API_AND_WORKER.md` — FastAPI сервер, фоновый пул воркеров и SSE стриминг.
- `reports/07_PHASE_7_WEB_UI.md` — 4 экрана интерфейса: Дашборд, Мастер, Окно ожидания, Студия результатов.
- `reports/08_PHASE_8_END_TO_END_VERIFICATION.md` — Итоговые результаты сквозного тестирования (8/8 тестов пройдено).
