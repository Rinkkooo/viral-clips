# Отчет Фазы 9: Безопасность, Контроль Квот, Аудит и Мониторинг (Security & Observability)

## 1. Архитектурная Цель
Обеспечить защиту видеокарты NVIDIA GeForce RTX 4060 (8 GB VRAM) от исчерпания памяти при параллельных вычислениях, ввести контроль бюджетных квот, вести неизменяемый аудит-лог действий и отдавать метрики в формате Prometheus.

## 2. Реализованные Компоненты
- **Модуль:** `viral_clips.core.security`
- **`CostGuard`:**
  - `check_video_duration`: Блокирует файлы длиннее лимита (180 минут) с генерацией `QuotaViolationError`.
  - `check_clip_count`: Защита от заказа избыточного количества клипов (макс 10 за один прогон).
  - `acquire_gpu_slot` / `release_gpu_slot`: Семафор монопольного доступа к аппаратному кодировщику NVENC на RTX 4060 (concurrency = 1).
- **`AuditLogger`:**
  - Запись всех критических событий (создание проекта, запуск конвейера, удаление, экспорт) в формате JSON Lines в `storage/audit.log`.
- **`MetricsCollector`:**
  - Сбор счетчиков задач (`queued`, `completed`, `failed`), общего объема отрендеренных секунд и текущих активных воркеров.
  - Экспорт в формате Prometheus по эндпоинту `GET /v1/metrics`.
- **`BackupManager`:**
  - Аварийное резервное копирование SQLite БД, манифестов и метаданных с расчетом контрольных сумм SHA-256 (`checksums.json`).
  - CLI команда: `python -m viral_clips.cli backup --dest backups`.

## 3. Статус: ВЫПОЛНЕНО
Все сценарии протестированы в `tests/test_storage_security_beta.py` (`test_cost_guard_quotas`, `test_audit_and_metrics`, `test_backup_manager`).
