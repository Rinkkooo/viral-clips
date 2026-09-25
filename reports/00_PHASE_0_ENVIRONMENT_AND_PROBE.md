# Отчет Фазы 0: Окружение, Инфраструктура и Валидация Медиа

## 1. Обзор статуса окружения
- **Операционная система:** Windows
- **Python:** 3.13.15 (64-bit)
- **GPU:** NVIDIA GeForce RTX 4060 (8188 MiB VRAM, Compute Capability / CUDA активен)
- **Движок FFmpeg / FFprobe:**
  - Локальный бинарник развернут: `static_ffmpeg` (v8.0/v9.0 build)
  - Расположение: `%LOCALAPPDATA%\Programs\Python\Python313\Lib\site-packages\static_ffmpeg\bin\win32\`
  - Аппаратное кодирование **NVIDIA NVENC (`h264_nvenc`)**: **ПОДДЕРЖИВАЕТСЯ И АКТИВНО** (`check_nvenc_support() == True`).

## 2. Реализованные компоненты
1. **Безопасность и конфигурация (`config.py`, `.env.example`, `.gitignore`):**
   - Строгая валидация настроек через `pydantic-settings`.
   - Секретные ключи (`SecretStr`) защищены от утечек в логи и строковые дампы.
   - Жесткие ограничения безопасности:
     - `max_source_duration_minutes`: 180 мин.
     - `max_video_width`: 3840, `max_video_height`: 2160, `max_video_fps`: 60.
     - `max_file_size_bytes`: 10 GB.
     - Лимит потоков: 1 видео-поток, максимум 4 аудио-потока.
     - Лимит параллелизма на GPU: 1 воркер (оптимально для 8 GB VRAM RTX 4060).
   - `.gitignore` блокирует любые `.env`, временные файлы видео (`temp/`, `output/`, `storage/`), дампы и ключи.

2. **Детектор бинарников FFmpeg (`core/ffmpeg_utils.py`):**
   - Каскадный поиск: `static_ffmpeg` -> пользовательский конфиг -> системный PATH -> WinGet Packages -> Program Files.
   - Функция верификации аппаратного кодера `check_nvenc_support()`.

3. **Песочница валидации медиа (`core/media_probe.py`):**
   - Sandboxed запуск `ffprobe` с таймаутом (20 сек) для предотвращения zip-bomb / бесконечных дескрипторов.
   - Проверка поддерживаемых кодеков (H.264, HEVC/H.265, VP8, VP9, AV1, ProRes и др.).
   - Формирование версионированного артефакта `probe.json` (`schema_version: "1.0.0"`).

4. **CLI интерфейс (`cli.py`):**
   - Команда `env-check` для диагностики состояния системы и NVENC.
   - Команда `probe` для валидации и сохранения `probe.json`.

## 3. Критерии приемки (Gate Phase 0)
- [x] Автоматическое обнаружение `ffmpeg` и `ffprobe`.
- [x] Аппаратное ускорение NVENC обнаружено и доступно на RTX 4060.
- [x] Валидация поврежденных и валидных файлов с кодами ошибок RFC 7807 (Problem Details).
