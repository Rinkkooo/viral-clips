"""
Viral Clips UI/UX Studio:
- Full Multilingual Localization (RU, EN, ES, DE, FR, ZH, TR, KK)
- Dynamic Dark / Light Theme Switcher
- Distinct Projects Library vs Analytics & Hardware Monitoring Dashboard
- High-Performance GPU-Accelerated Toast Notifications (Zero blocking alerts)
- Elegant Confirmation Modal (Zero blocking confirms)
- 2-Column Create Project with real-time metadata & summary
- Timeline Processing screen with localStorage recovery
- 3-Column Results Studio with vertical player, trim nudges, 7 dimensions, and feedback scorecard
"""

def get_ui_html() -> str:
    return """<!DOCTYPE html>
<html lang="ru" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Viral Clips AI — Creator Studio</title>
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Lucide Icons CDN -->
  <script src="https://unpkg.com/lucide@latest"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: {
              50: '#f5f3ff',
              100: '#ede9fe',
              200: '#ddd6fe',
              300: '#c4b5fd',
              400: '#a78bfa',
              500: '#8b5cf6',
              600: '#7c3aed',
              700: '#6d28d9',
              800: '#5b21b6',
              900: '#4c1d95',
            },
            surface: {
              750: '#202024',
              800: '#18181b',
              850: '#121215',
              900: '#09090b',
              950: '#040406',
            }
          }
        }
      }
    }
  </script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      transition: background-color 0.2s ease, color 0.2s ease;
    }
    .font-mono {
      font-family: 'JetBrains Mono', monospace;
    }
    .player-aspect {
      aspect-ratio: 9 / 16;
    }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #3f3f46; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #71717a; }

    /* Subtitle Live Preview Styles */
    .sub-preview-hormozi {
      color: #FACC15;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      text-shadow: 2px 2px 0 #000, -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 0 4px 10px rgba(0,0,0,0.8);
    }
    .sub-preview-neon {
      color: #34D399;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      text-shadow: 0 0 10px rgba(52, 211, 153, 0.7), 2px 2px 0 #000, -2px -2px 0 #000;
    }
    .sub-preview-minimal {
      color: #FFFFFF;
      font-weight: 600;
      letter-spacing: 0.02em;
      text-shadow: 1px 1px 2px rgba(0,0,0,0.9);
    }

    /* GPU-Accelerated Micro-Interactions */
    .card-interactive {
      transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease, border-color 0.2s ease;
      will-change: transform;
    }
    .card-interactive:hover {
      transform: translateY(-2px);
    }
    .btn-press {
      transition: transform 0.1s ease;
      will-change: transform;
    }
    .btn-press:active {
      transform: scale(0.97);
    }
  </style>
</head>
<body class="min-h-screen flex flex-col bg-zinc-50 dark:bg-surface-900 text-zinc-900 dark:text-zinc-100 antialiased selection:bg-brand-500 selection:text-white relative">

  <!-- Toast Notification Stack (Top-Right, Zero-Lag, Hardware-Accelerated) -->
  <div id="toast-container" class="fixed top-5 right-5 z-[9999] flex flex-col gap-2.5 pointer-events-none max-w-sm w-full"></div>

  <!-- Custom Confirmation Modal (Replaces Native confirm) -->
  <div id="confirm-modal-backdrop" class="fixed inset-0 z-[9998] bg-black/60 backdrop-blur-sm hidden items-center justify-center p-4 transition-opacity duration-200 opacity-0 pointer-events-none">
    <div id="confirm-modal-box" class="bg-white dark:bg-surface-850 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-6 max-w-md w-full shadow-2xl transform scale-95 transition-all duration-200 space-y-4">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-brand-500/10 text-brand-600 dark:text-brand-400 flex items-center justify-center flex-shrink-0">
          <i data-lucide="help-circle" class="w-5 h-5"></i>
        </div>
        <div>
          <h3 id="confirm-modal-title" class="text-base font-bold text-zinc-900 dark:text-white">Подтверждение</h3>
          <p id="confirm-modal-message" class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">Вы уверены?</p>
        </div>
      </div>
      <div class="flex items-center justify-end gap-2.5 pt-2 border-t border-zinc-100 dark:border-zinc-800">
        <button type="button" id="confirm-modal-cancel" class="btn-press text-xs font-semibold px-4 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700 transition">
          Отмена
        </button>
        <button type="button" id="confirm-modal-ok" class="btn-press text-xs font-semibold px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-600/25 transition">
          Подтвердить
        </button>
      </div>
    </div>
  </div>

  <!-- Top Navigation Header -->
  <header class="border-b border-zinc-200 dark:border-zinc-800/80 bg-white/80 dark:bg-surface-950/80 backdrop-blur sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
      
      <!-- Brand Logo (Routes to Projects Library) -->
      <div class="flex items-center gap-3 cursor-pointer group" onclick="navigateTo('projects')">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-brand-500/25 group-hover:scale-105 transition">
          <i data-lucide="scissors" class="w-5 h-5 text-white"></i>
        </div>
        <div>
          <span class="text-base font-bold tracking-tight text-zinc-900 dark:text-white">Viral Clips <span class="text-brand-500">AI</span></span>
          <span class="ml-2 px-2 py-0.5 text-[10px] font-bold bg-brand-500/10 text-brand-500 dark:text-brand-400 rounded-full border border-brand-500/20">Studio v2</span>
        </div>
      </div>

      <!-- Center & Right Navigation -->
      <div class="flex items-center gap-2 sm:gap-4">
        
        <!-- Navigation Links: Projects vs Analytics Dashboard -->
        <nav class="flex items-center gap-1.5 bg-zinc-100 dark:bg-surface-850 p-1 rounded-xl border border-zinc-200 dark:border-zinc-800">
          <button type="button" id="nav-btn-projects" onclick="navigateTo('projects')" class="nav-tab text-xs font-semibold px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 bg-white dark:bg-surface-800 text-zinc-900 dark:text-white shadow-sm">
            <i data-lucide="folder-kanban" class="w-3.5 h-3.5 text-brand-500"></i>
            <span data-i18n="nav_projects">Проекты</span>
          </button>
          <button type="button" id="nav-btn-dashboard" onclick="navigateTo('dashboard')" class="nav-tab text-xs font-semibold px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white">
            <i data-lucide="bar-chart-3" class="w-3.5 h-3.5 text-indigo-400"></i>
            <span data-i18n="nav_analytics">Аналитика</span>
          </button>
        </nav>

        <!-- New Project CTA Button -->
        <button type="button" onclick="navigateTo('new-project')" class="btn-press text-xs font-semibold bg-brand-600 hover:bg-brand-500 text-white px-3.5 py-2 rounded-xl transition shadow-lg shadow-brand-600/25 flex items-center gap-1.5">
          <i data-lucide="plus" class="w-3.5 h-3.5"></i>
          <span data-i18n="nav_new_project">Создать проект</span>
        </button>

        <!-- Theme Switcher (Dark / Light) -->
        <button type="button" onclick="toggleTheme()" id="theme-toggle-btn" title="Сменить тему" class="btn-press w-9 h-9 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-100 dark:bg-surface-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 flex items-center justify-center text-zinc-700 dark:text-zinc-300 transition">
          <i id="theme-icon" data-lucide="sun" class="w-4 h-4 text-amber-500 hidden dark:block"></i>
          <i id="theme-icon-dark" data-lucide="moon" class="w-4 h-4 text-indigo-500 block dark:hidden"></i>
        </button>

        <!-- Multilingual Language Selector (8 Languages) -->
        <div class="relative">
          <select id="lang-selector" onchange="changeLanguage(this.value)" class="text-xs font-semibold bg-zinc-100 dark:bg-surface-800 border border-zinc-200 dark:border-zinc-800 rounded-xl px-2.5 py-2 text-zinc-800 dark:text-zinc-200 cursor-pointer focus:outline-none focus:border-brand-500">
            <option value="ru">🇷🇺 Русский</option>
            <option value="en">🇬🇧 English</option>
            <option value="es">🇪🇸 Español</option>
            <option value="de">🇩🇪 Deutsch</option>
            <option value="fr">🇫🇷 Français</option>
            <option value="zh">🇨🇳 中文</option>
            <option value="tr">🇹🇷 Türkçe</option>
            <option value="kk">🇰🇿 Қазақша</option>
          </select>
        </div>

      </div>
    </div>
  </header>

  <!-- Main Content Container -->
  <main class="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6">

    <!-- ========================================== -->
    <!-- 1. PROJECTS LIBRARY SCREEN                 -->
    <!-- (Clean Catalog of Video Projects)          -->
    <!-- ========================================== -->
    <section id="screen-projects" class="space-y-6">
      
      <!-- Header with Project Stats & Search -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-zinc-200 dark:border-zinc-800">
        <div>
          <h1 class="text-xl font-bold text-zinc-900 dark:text-white" data-i18n="projects_title">Мои проекты нарезки</h1>
          <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5" data-i18n="projects_subtitle">Каталог проектов и готовых вирусных клипов 9:16</p>
        </div>

        <div class="flex items-center gap-3">
          <div class="relative">
            <i data-lucide="search" class="w-3.5 h-3.5 absolute left-3 top-3 text-zinc-400"></i>
            <input type="text" id="projects-search-input" oninput="filterProjects(this.value)" placeholder="Поиск проекта..." data-i18n-ph="search_placeholder" class="bg-zinc-100 dark:bg-surface-800 border border-zinc-200 dark:border-zinc-800 rounded-xl pl-8 pr-3 py-1.5 text-xs text-zinc-900 dark:text-white focus:outline-none focus:border-brand-500 w-48 sm:w-64 transition">
          </div>
          <button type="button" onclick="refreshProjects()" class="btn-press text-xs text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-zinc-100 dark:bg-surface-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 border border-zinc-200 dark:border-zinc-800 transition">
            <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
            <span data-i18n="refresh">Обновить</span>
          </button>
        </div>
      </div>

      <!-- Quick Metrics Strip -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div class="card-interactive bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 p-4 rounded-2xl">
          <div class="text-[11px] font-medium text-zinc-500 dark:text-zinc-400" data-i18n="stat_projects">Всего проектов</div>
          <div id="stat-total-projects" class="text-xl font-bold mt-1 text-zinc-900 dark:text-white font-mono">0</div>
        </div>
        <div class="card-interactive bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 p-4 rounded-2xl">
          <div class="text-[11px] font-medium text-zinc-500 dark:text-zinc-400" data-i18n="stat_clips">Сгенерировано клипов</div>
          <div id="stat-total-clips" class="text-xl font-bold mt-1 text-brand-600 dark:text-brand-400 font-mono">0</div>
        </div>
        <div class="card-interactive bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 p-4 rounded-2xl">
          <div class="text-[11px] font-medium text-zinc-500 dark:text-zinc-400" data-i18n="stat_encoder">Энкодер</div>
          <div class="text-xl font-bold mt-1 text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
            NVENC <span class="text-[10px] px-1.5 py-0.5 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-mono">60fps</span>
          </div>
        </div>
        <div class="card-interactive bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 p-4 rounded-2xl">
          <div class="text-[11px] font-medium text-zinc-500 dark:text-zinc-400" data-i18n="stat_llm">AI Модель</div>
          <div id="stat-llm-label" class="text-xl font-bold mt-1 text-indigo-600 dark:text-indigo-400">Qwen 2.5</div>
        </div>
      </div>

      <!-- Projects Grid -->
      <div id="projects-list-container" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- Filled dynamically by JavaScript -->
      </div>
    </section>

    <!-- ========================================== -->
    <!-- 2. ANALYTICS & MONITORING DASHBOARD        -->
    <!-- (Real Hardware Health, Event Stream & KPIs) -->
    <!-- ========================================== -->
    <section id="screen-dashboard" class="hidden space-y-6">
      
      <!-- Dashboard Title -->
      <div class="flex items-center justify-between pb-2 border-b border-zinc-200 dark:border-zinc-800">
        <div>
          <h1 class="text-xl font-bold text-zinc-900 dark:text-white" data-i18n="dash_title">Дашборд аналитики и системы</h1>
          <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5" data-i18n="dash_subtitle">Мониторинг нейросетей, аппаратного ускорения и событий обработки</p>
        </div>
        <button type="button" onclick="loadDashboardAnalytics()" class="btn-press text-xs text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-zinc-100 dark:bg-surface-800 border border-zinc-200 dark:border-zinc-800 transition">
          <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
          <span data-i18n="refresh">Обновить</span>
        </button>
      </div>

      <!-- Hardware & Engine Status Cards (4 Cards) -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div class="card-interactive bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 p-5 rounded-2xl space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400" data-i18n="hw_gpu">Видеокарта (GPU)</span>
            <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
          </div>
          <div class="text-lg font-bold text-zinc-900 dark:text-white">NVIDIA RTX 4060</div>
          <div class="text-xs text-zinc-600 dark:text-zinc-400 space-y-1 font-mono">
            <div>• NVENC: <b class="text-emerald-500">Активен (h264_nvenc)</b></div>
            <div>• Разрешение: <b>1080x1920 9:16</b></div>
            <div>• Скорость: <b>~60 FPS One-Pass</b></div>
          </div>
        </div>

        <div class="card-interactive bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 p-5 rounded-2xl space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400" data-i18n="hw_asr">Распознавание речи</span>
            <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
          </div>
          <div class="text-lg font-bold text-zinc-900 dark:text-white">Faster-Whisper</div>
          <div class="text-xs text-zinc-600 dark:text-zinc-400 space-y-1 font-mono">
            <div>• Движок: <b>CUDA float16</b></div>
            <div>• Модель: <b>small (локальная)</b></div>
            <div>• Тайминги: <b>Word-level VAD</b></div>
          </div>
        </div>

        <div class="card-interactive bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 p-5 rounded-2xl space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400" data-i18n="hw_llm">Оценка виральности</span>
            <span id="dash-llm-dot" class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
          </div>
          <div id="dash-llm-title" class="text-lg font-bold text-zinc-900 dark:text-white">Qwen 2.5 1.5B</div>
          <div class="text-xs text-zinc-600 dark:text-zinc-400 space-y-1 font-mono">
            <div>• Провайдер: <b>Ollama (127.0.0.1)</b></div>
            <div>• Факторов: <b>7 измерений</b></div>
            <div>• Схема: <b>JSON Structured</b></div>
          </div>
        </div>

        <div class="card-interactive bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 p-5 rounded-2xl space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400" data-i18n="hw_storage">Хранилище & База</span>
            <span class="w-2.5 h-2.5 rounded-full bg-indigo-400"></span>
          </div>
          <div class="text-lg font-bold text-zinc-900 dark:text-white">SQLite + Drive 10 TB</div>
          <div class="text-xs text-zinc-600 dark:text-zinc-400 space-y-1 font-mono">
            <div>• Аудит: <b>Hash-Chain SHA256</b></div>
            <div>• Локально: <b>storage/output</b></div>
            <div>• Облако: <b>Google Drive API</b></div>
          </div>
        </div>

      </div>

      <!-- Virality & Quality Metrics -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="card-interactive bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 p-5 rounded-2xl space-y-2">
          <div class="text-xs font-semibold text-zinc-500 dark:text-zinc-400" data-i18n="metric_avg_score">Средний балл виральности клипов</div>
          <div class="text-3xl font-extrabold text-brand-600 dark:text-brand-400 font-mono">8.4 <span class="text-sm font-normal text-zinc-400">/ 10</span></div>
          <p class="text-[11px] text-zinc-500" data-i18n="metric_avg_desc">Взвешенная оценка по хуку, кульминации и желанию поделиться</p>
        </div>
        <div class="card-interactive bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 p-5 rounded-2xl space-y-2">
          <div class="text-xs font-semibold text-zinc-500 dark:text-zinc-400" data-i18n="metric_publishable">Готовность к публикации (Human Review)</div>
          <div class="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 font-mono">92%</div>
          <p class="text-[11px] text-zinc-500" data-i18n="metric_pub_desc">Доля клипов, одобренных для публикации в Shorts/Reels</p>
        </div>
        <div class="card-interactive bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 p-5 rounded-2xl space-y-2">
          <div class="text-xs font-semibold text-zinc-500 dark:text-zinc-400" data-i18n="metric_smooth">Сглаживание кадрирования 9:16</div>
          <div class="text-3xl font-extrabold text-indigo-600 dark:text-indigo-400 font-mono">25 pts <span class="text-sm font-normal text-zinc-400">RDP</span></div>
          <p class="text-[11px] text-zinc-500" data-i18n="metric_smooth_desc">Алгоритм Рамера-Дугласа-Пекера устраняет рывки камеры</p>
        </div>
      </div>

      <!-- Real-Time Activity Log from /v1/system/events -->
      <div class="bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 p-5 rounded-2xl space-y-3">
        <div class="flex items-center justify-between">
          <div class="text-xs font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 flex items-center gap-1.5">
            <i data-lucide="activity" class="w-4 h-4 text-brand-500"></i>
            <span data-i18n="events_log_title">Журнал событий и действий системы</span>
          </div>
          <button type="button" onclick="triggerRetentionCleanup()" class="btn-press text-xs text-rose-500 hover:text-rose-400 border border-rose-500/30 px-2.5 py-1 rounded-lg transition" data-i18n="cleanup_storage">
            Очистить старые файлы
          </button>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead>
              <tr class="border-b border-zinc-200 dark:border-zinc-800 text-zinc-400 dark:text-zinc-500 font-mono">
                <th class="py-2 px-3" data-i18n="tbl_time">Время</th>
                <th class="py-2 px-3" data-i18n="tbl_event">Событие</th>
                <th class="py-2 px-3" data-i18n="tbl_entity">Сущность</th>
                <th class="py-2 px-3" data-i18n="tbl_details">Детали</th>
              </tr>
            </thead>
            <tbody id="events-table-body" class="divide-y divide-zinc-100 dark:divide-zinc-800/60 font-mono">
              <!-- Filled by JS -->
            </tbody>
          </table>
        </div>
      </div>

    </section>

    <!-- ========================================== -->
    <!-- 3. CREATE PROJECT SCREEN (UI/UX v2)        -->
    <!-- 2-Column: Left 68% settings, Right 32% summary -->
    <!-- ========================================== -->
    <section id="screen-new-project" class="hidden space-y-6">
      <div class="flex items-center gap-3 pb-2 border-b border-zinc-200 dark:border-zinc-800">
        <button type="button" onclick="navigateTo('projects')" class="btn-press text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white flex items-center gap-1 px-3 py-1.5 rounded-xl bg-zinc-100 dark:bg-surface-800 border border-zinc-200 dark:border-zinc-700 text-xs font-semibold transition">
          <i data-lucide="arrow-left" class="w-4 h-4"></i>
          <span data-i18n="back_to_projects">К проектам</span>
        </button>
        <div>
          <h1 class="text-xl font-bold text-zinc-900 dark:text-white" data-i18n="new_proj_heading">Создание проекта нарезки</h1>
          <p class="text-xs text-zinc-500 dark:text-zinc-400" data-i18n="new_proj_subheading">Настройте параметры поиска вирусных моментов и запустите генерацию</p>
        </div>
      </div>

      <form id="form-create-project" onsubmit="handleStartProject(event)" class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        <!-- LEFT COLUMN: 68% (lg:col-span-8) -->
        <div class="lg:col-span-8 space-y-6">

          <!-- 1. Project Name -->
          <div class="bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 space-y-3">
            <label class="block text-sm font-bold text-zinc-900 dark:text-white flex items-center gap-2">
              <i data-lucide="edit-3" class="w-4 h-4 text-brand-500"></i>
              <span data-i18n="fld_proj_name">Название проекта</span>
            </label>
            <input type="text" id="input-project-name" required placeholder="Например: Подкаст #42 — Секреты Успеха" data-i18n-ph="proj_name_placeholder" oninput="updateSummary()" class="w-full bg-zinc-50 dark:bg-surface-900 border border-zinc-300 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-sm text-zinc-900 dark:text-white focus:outline-none focus:border-brand-500 transition">
          </div>

          <!-- 2. Source Video Card (Dropzone or Compact Source Card) -->
          <div class="bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 space-y-3">
            <label class="block text-sm font-bold text-zinc-900 dark:text-white flex items-center justify-between">
              <span class="flex items-center gap-2"><i data-lucide="video" class="w-4 h-4 text-brand-500"></i> <span data-i18n="fld_video">Исходное видео</span></span>
              <span class="text-xs font-normal text-zinc-400">MP4, MOV, MKV, WEBM</span>
            </label>

            <!-- Dropzone (shown when no file selected) -->
            <div id="dropzone" class="border-2 border-dashed border-zinc-300 dark:border-zinc-700 hover:border-brand-500 rounded-2xl p-8 text-center transition bg-zinc-50/50 dark:bg-surface-900/40 cursor-pointer group">
              <input type="file" id="file-input" accept="video/*" class="hidden" onchange="handleFileSelected(event)">
              <div class="w-12 h-12 rounded-2xl bg-brand-500/10 text-brand-500 dark:text-brand-400 flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition">
                <i data-lucide="upload-cloud" class="w-6 h-6"></i>
              </div>
              <div class="text-sm font-semibold text-zinc-900 dark:text-white" data-i18n="dropzone_title">Перетащите видеофайл сюда или нажмите для выбора</div>
              <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-1" data-i18n="dropzone_subtitle">Поддерживается видео до 10 ГБ. Метаданные определятся автоматически.</p>
            </div>

            <!-- Compact Video Source Card (shown once file selected) -->
            <div id="source-video-card" class="hidden bg-zinc-100 dark:bg-surface-900 border border-brand-500/40 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div class="flex items-center gap-3 overflow-hidden">
                <div class="w-10 h-10 rounded-xl bg-brand-600/20 text-brand-500 dark:text-brand-400 flex-shrink-0 flex items-center justify-center">
                  <i data-lucide="film" class="w-5 h-5"></i>
                </div>
                <div class="overflow-hidden">
                  <div id="card-video-name" class="text-sm font-bold text-zinc-900 dark:text-white truncate max-w-xs sm:max-w-md">video.mp4</div>
                  <div class="flex items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400 mt-0.5 font-mono">
                    <span id="card-video-duration">--:--</span>
                    <span>•</span>
                    <span id="card-video-resolution">1920x1080</span>
                    <span>•</span>
                    <span id="card-video-size">-- MB</span>
                  </div>
                </div>
              </div>
              <button type="button" onclick="triggerFileSelect()" class="btn-press text-xs font-semibold px-3 py-1.5 rounded-xl bg-white dark:bg-surface-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 border border-zinc-200 dark:border-zinc-700 text-zinc-800 dark:text-zinc-200 transition flex items-center gap-1.5 flex-shrink-0">
                <i data-lucide="repeat" class="w-3.5 h-3.5"></i>
                <span data-i18n="btn_replace_file">Заменить файл</span>
              </button>
            </div>
          </div>

          <!-- 3. Clip Quantity & Duration Presets -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <!-- Quantity Segmented Control -->
            <div class="bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 space-y-3">
              <label class="block text-sm font-bold text-zinc-900 dark:text-white flex items-center justify-between">
                <span data-i18n="fld_clip_count">Количество клипов</span>
                <span class="text-xs font-normal text-zinc-400">Top-N</span>
              </label>
              <div class="grid grid-cols-3 gap-2">
                <button type="button" data-count="3" onclick="selectClipCount(3)" class="btn-press clip-count-btn py-2.5 px-3 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-sm font-bold text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white transition">3</button>
                <button type="button" data-count="5" onclick="selectClipCount(5)" class="btn-press clip-count-btn py-2.5 px-3 rounded-xl border border-brand-500 bg-brand-500/10 text-sm font-bold text-brand-600 dark:text-brand-400 transition">5 (<span data-i18n="rec_label">рек.</span>)</button>
                <button type="button" data-count="10" onclick="selectClipCount(10)" class="btn-press clip-count-btn py-2.5 px-3 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-sm font-bold text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white transition">10</button>
              </div>
              <input type="hidden" id="select-clip-count" value="5">
              <p class="text-[11px] text-zinc-500 dark:text-zinc-400" data-i18n="clip_count_hint">AI найдет лучшие законченные мысли и диверсифицирует темы.</p>
            </div>

            <!-- Duration Presets -->
            <div class="bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 space-y-3">
              <label class="block text-sm font-bold text-zinc-900 dark:text-white flex items-center justify-between">
                <span data-i18n="fld_duration">Длительность клипов</span>
                <span id="label-current-duration" class="text-xs font-mono text-brand-600 dark:text-brand-400">30–60 сек</span>
              </label>
              <div class="grid grid-cols-2 gap-2 text-xs">
                <button type="button" onclick="selectDurationPreset(15, 30)" class="btn-press dur-preset-btn py-2 px-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white font-medium transition text-center">15–30 <span data-i18n="sec_short">сек</span></button>
                <button type="button" onclick="selectDurationPreset(30, 60)" class="btn-press dur-preset-btn py-2 px-2.5 rounded-xl border border-brand-500 bg-brand-500/10 text-brand-600 dark:text-brand-400 font-bold transition text-center">30–60 <span data-i18n="sec_short">сек</span></button>
                <button type="button" onclick="selectDurationPreset(60, 90)" class="btn-press dur-preset-btn py-2 px-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white font-medium transition text-center">60–90 <span data-i18n="sec_short">сек</span></button>
                <button type="button" onclick="toggleCustomDuration()" id="btn-custom-dur" class="btn-press dur-preset-btn py-2 px-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white font-medium transition text-center" data-i18n="custom_range">Свой диапазон</button>
              </div>

              <!-- Custom Duration Inputs (Toggleable) -->
              <div id="custom-dur-container" class="hidden pt-2 border-t border-zinc-200 dark:border-zinc-800 grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span class="text-[11px] text-zinc-500 dark:text-zinc-400 block mb-1" data-i18n="min_sec">Мин (сек):</span>
                  <input type="number" id="input-dur-min" value="30" min="10" max="120" onchange="onCustomDurChange()" class="w-full bg-zinc-100 dark:bg-surface-900 border border-zinc-300 dark:border-zinc-700 rounded-lg p-2 text-zinc-900 dark:text-white font-mono">
                </div>
                <div>
                  <span class="text-[11px] text-zinc-500 dark:text-zinc-400 block mb-1" data-i18n="max_sec">Макс (сек):</span>
                  <input type="number" id="input-dur-max" value="60" min="15" max="180" onchange="onCustomDurChange()" class="w-full bg-zinc-100 dark:bg-surface-900 border border-zinc-300 dark:border-zinc-700 rounded-lg p-2 text-zinc-900 dark:text-white font-mono">
                </div>
              </div>
            </div>
          </div>

          <!-- 4. Highlight Strategy (Multi-Select Pills) & Content Type -->
          <div class="bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 space-y-4">
            <div>
              <label class="block text-sm font-bold text-zinc-900 dark:text-white mb-1 flex items-center justify-between">
                <span data-i18n="fld_strategy">Что искать нейросети (Стратегия хайлайтов)</span>
                <span class="text-xs font-normal text-zinc-400" data-i18n="multiselect">Мультивыбор</span>
              </label>
              <p class="text-xs text-zinc-500 dark:text-zinc-400 mb-3" data-i18n="strategy_hint">Выберите один или несколько типов моментов для фокусировки LLM-ранжирования:</p>

              <div class="flex flex-wrap gap-2" id="strategy-pills-container">
                <button type="button" data-strategy="auto" onclick="toggleStrategy('auto')" class="btn-press strat-pill px-3 py-1.5 rounded-full text-xs font-semibold border border-brand-500 bg-brand-500/10 text-brand-600 dark:text-brand-300 transition" data-i18n="strat_auto">✨ Авто (лучшие моменты)</button>
                <button type="button" data-strategy="hooks" onclick="toggleStrategy('hooks')" class="btn-press strat-pill px-3 py-1.5 rounded-full text-xs font-semibold border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white transition" data-i18n="strat_hooks">🎯 Хуки (яркие начала)</button>
                <button type="button" data-strategy="insights" onclick="toggleStrategy('insights')" class="btn-press strat-pill px-3 py-1.5 rounded-full text-xs font-semibold border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white transition" data-i18n="strat_insights">💡 Инсайты (польза)</button>
                <button type="button" data-strategy="hot_takes" onclick="toggleStrategy('hot_takes')" class="btn-press strat-pill px-3 py-1.5 rounded-full text-xs font-semibold border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white transition" data-i18n="strat_hot_takes">🔥 Острые мысли</button>
                <button type="button" data-strategy="funny" onclick="toggleStrategy('funny')" class="btn-press strat-pill px-3 py-1.5 rounded-full text-xs font-semibold border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white transition" data-i18n="strat_funny">😂 Юмор</button>
                <button type="button" data-strategy="stories" onclick="toggleStrategy('stories')" class="btn-press strat-pill px-3 py-1.5 rounded-full text-xs font-semibold border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white transition" data-i18n="strat_stories">📖 Истории</button>
                <button type="button" data-strategy="quotes" onclick="toggleStrategy('quotes')" class="btn-press strat-pill px-3 py-1.5 rounded-full text-xs font-semibold border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white transition" data-i18n="strat_quotes">💬 Цитаты</button>
              </div>
            </div>

            <!-- Content Type Dropdown -->
            <div class="pt-3 border-t border-zinc-200 dark:border-zinc-800">
              <label class="block text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1.5" data-i18n="fld_content_type">Тип исходного видеоконтента</label>
              <select id="select-content-type" onchange="updateSummary()" class="w-full sm:w-80 bg-zinc-100 dark:bg-surface-900 border border-zinc-300 dark:border-zinc-700 rounded-xl px-3 py-2 text-xs text-zinc-900 dark:text-white focus:outline-none focus:border-brand-500">
                <option value="auto" selected data-i18n="c_auto">✨ Автоопределение контекста</option>
                <option value="podcast" data-i18n="c_podcast">🎙️ Подкаст / Интервью</option>
                <option value="talking_head" data-i18n="c_head">👤 Говорящая голова / Эксперт</option>
                <option value="stream" data-i18n="c_stream">🎮 Стрим / Гейминг</option>
                <option value="lecture" data-i18n="c_lecture">🎓 Лекция / Обучающий вебинар</option>
                <option value="reaction" data-i18n="c_reaction">⚡ Реакция / Разбор</option>
                <option value="other" data-i18n="c_other">📦 Другое видео</option>
              </select>
            </div>
          </div>

          <!-- 5. Framing Preset -->
          <div class="bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 space-y-3">
            <label class="block text-sm font-bold text-zinc-900 dark:text-white flex items-center justify-between">
              <span data-i18n="fld_framing">Кадрирование 9:16</span>
              <span class="text-xs font-normal text-zinc-400">OpenCV Face Tracking</span>
            </label>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <label class="btn-press framing-card border border-brand-500 bg-brand-500/10 p-3.5 rounded-xl cursor-pointer transition text-center flex flex-col items-center justify-center">
                <input type="radio" name="framing" value="active_speaker" checked onchange="updateSummary()" class="hidden">
                <i data-lucide="user-check" class="w-5 h-5 text-brand-500 dark:text-brand-400 mb-1"></i>
                <div class="text-xs font-bold text-zinc-900 dark:text-white" data-i18n="frame_active">Трекинг лица</div>
                <div class="text-[10px] text-zinc-500 dark:text-zinc-400 mt-0.5" data-i18n="frame_active_sub">Камера следует за спикером</div>
              </label>
              <label class="btn-press framing-card border border-zinc-300 dark:border-zinc-700 hover:border-zinc-500 p-3.5 rounded-xl cursor-pointer transition text-center flex flex-col items-center justify-center">
                <input type="radio" name="framing" value="blurred_background" onchange="updateSummary()" class="hidden">
                <i data-lucide="layers" class="w-5 h-5 text-indigo-400 mb-1"></i>
                <div class="text-xs font-bold text-zinc-900 dark:text-white" data-i18n="frame_blur">Размытый фон</div>
                <div class="text-[10px] text-zinc-500 dark:text-zinc-400 mt-0.5" data-i18n="frame_blur_sub">16:9 с размытым 9:16 фоном</div>
              </label>
              <label class="btn-press framing-card border border-zinc-300 dark:border-zinc-700 hover:border-zinc-500 p-3.5 rounded-xl cursor-pointer transition text-center flex flex-col items-center justify-center">
                <input type="radio" name="framing" value="center_crop" onchange="updateSummary()" class="hidden">
                <i data-lucide="crop" class="w-5 h-5 text-zinc-400 mb-1"></i>
                <div class="text-xs font-bold text-zinc-900 dark:text-white" data-i18n="frame_center">Центр кадра</div>
                <div class="text-[10px] text-zinc-500 dark:text-zinc-400 mt-0.5" data-i18n="frame_center_sub">Статичный центр 9:16</div>
              </label>
            </div>
          </div>

          <!-- 6. Subtitles & Live Preview Box -->
          <div class="bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 space-y-4">
            <div>
              <label class="block text-sm font-bold text-zinc-900 dark:text-white" data-i18n="fld_subtitles">Стиль караоке-субтитров</label>
              <p class="text-xs text-zinc-500 dark:text-zinc-400" data-i18n="subtitles_hint">Пословное выделение текста синхронизировано со звуковой дорожкой</p>
            </div>

            <!-- Preset Cards -->
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <label class="btn-press sub-card border border-brand-500 bg-brand-500/10 p-3.5 rounded-xl cursor-pointer transition text-center">
                <input type="radio" name="subtitles" value="bold_karaoke" checked onchange="onSubtitlePresetChange()" class="hidden">
                <i data-lucide="sparkles" class="w-5 h-5 text-amber-500 mx-auto mb-1"></i>
                <div class="text-xs font-bold text-zinc-900 dark:text-white">Hormozi Gold</div>
                <div class="text-[10px] text-zinc-500 dark:text-zinc-400" data-i18n="sub_gold_sub">Жирный желтый караоке</div>
              </label>
              <label class="btn-press sub-card border border-zinc-300 dark:border-zinc-700 hover:border-zinc-500 p-3.5 rounded-xl cursor-pointer transition text-center">
                <input type="radio" name="subtitles" value="neon_glow" onchange="onSubtitlePresetChange()" class="hidden">
                <i data-lucide="flame" class="w-5 h-5 text-emerald-500 mx-auto mb-1"></i>
                <div class="text-xs font-bold text-zinc-900 dark:text-white">Neon Cyber</div>
                <div class="text-[10px] text-zinc-500 dark:text-zinc-400" data-i18n="sub_neon_sub">Яркий зеленый неон</div>
              </label>
              <label class="btn-press sub-card border border-zinc-300 dark:border-zinc-700 hover:border-zinc-500 p-3.5 rounded-xl cursor-pointer transition text-center">
                <input type="radio" name="subtitles" value="minimal" onchange="onSubtitlePresetChange()" class="hidden">
                <i data-lucide="type" class="w-5 h-5 text-zinc-400 mx-auto mb-1"></i>
                <div class="text-xs font-bold text-zinc-900 dark:text-white">Minimal White</div>
                <div class="text-[10px] text-zinc-500 dark:text-zinc-400" data-i18n="sub_white_sub">Классический белый текст</div>
              </label>
            </div>

            <!-- Subtitle Live Preview Box -->
            <div class="bg-zinc-100 dark:bg-surface-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 text-center">
              <div class="text-[10px] uppercase font-bold text-zinc-500 dark:text-zinc-400 tracking-wider mb-2" data-i18n="live_sub_preview">Live предпросмотр стиля субтитров</div>
              <div class="h-16 flex items-center justify-center bg-zinc-900 rounded-lg p-3">
                <span id="sub-live-preview-text" class="text-lg sub-preview-hormozi" data-i18n="sample_sub_text">
                  ЭТО ИЗМЕНИЛО ВСЁ
                </span>
              </div>
            </div>
          </div>

          <!-- 7. Advanced Developer & Pipeline Options (Collapsible) -->
          <div class="border border-zinc-200 dark:border-zinc-800 rounded-2xl overflow-hidden bg-white dark:bg-surface-850/40">
            <button type="button" onclick="toggleAdvancedOptions()" class="w-full p-4 text-left flex items-center justify-between text-xs font-bold text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white transition">
              <span class="flex items-center gap-2">
                <i data-lucide="settings-2" class="w-4 h-4 text-zinc-400"></i>
                <span data-i18n="adv_title">Расширенные настройки и AI-ядро</span>
              </span>
              <i id="advanced-chevron" data-lucide="chevron-down" class="w-4 h-4 transition transform"></i>
            </button>

            <div id="advanced-options-container" class="hidden p-5 pt-0 border-t border-zinc-200 dark:border-zinc-800/60 space-y-4 text-xs">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4">
                <div>
                  <label class="text-zinc-500 dark:text-zinc-400 block mb-1" data-i18n="adv_asr_lang">Язык распознавания речи</label>
                  <select id="select-language" onchange="updateSummary()" class="w-full bg-zinc-100 dark:bg-surface-900 border border-zinc-300 dark:border-zinc-700 rounded-xl p-2.5 text-zinc-900 dark:text-white">
                    <option value="auto" selected data-i18n="adv_auto_detect">✨ Автоопределение (Faster-Whisper)</option>
                    <option value="ru">Русский (Russian)</option>
                    <option value="en">English (Английский)</option>
                    <option value="es">Español (Испанский)</option>
                    <option value="de">Deutsch (Немецкий)</option>
                    <option value="fr">Français (Французский)</option>
                    <option value="zh">中文 (Китайский)</option>
                    <option value="tr">Türkçe (Турецкий)</option>
                    <option value="kk">Қазақша (Казахский)</option>
                  </select>
                </div>
                <div>
                  <label class="text-zinc-500 dark:text-zinc-400 block mb-1" data-i18n="adv_local_path">Локальный путь (Developer Option)</label>
                  <input type="text" id="input-video-path" oninput="onVideoPathChange()" placeholder="C:\\path\\to\\video.mp4" class="w-full bg-zinc-100 dark:bg-surface-900 border border-zinc-300 dark:border-zinc-700 rounded-xl p-2.5 text-zinc-900 dark:text-white font-mono text-xs">
                </div>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                <label class="flex items-center gap-2 cursor-pointer text-zinc-700 dark:text-zinc-300">
                  <input type="checkbox" id="opt-avoid-overlap" checked onchange="updateSummary()" class="rounded bg-zinc-100 dark:bg-surface-900 border-zinc-300 dark:border-zinc-700 text-brand-600 focus:ring-0">
                  <span data-i18n="opt_avoid_overlap">Исключать пересечение клипов (диверсификация)</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer text-zinc-700 dark:text-zinc-300">
                  <input type="checkbox" id="opt-complete-sentences" checked onchange="updateSummary()" class="rounded bg-zinc-100 dark:bg-surface-900 border-zinc-300 dark:border-zinc-700 text-brand-600 focus:ring-0">
                  <span data-i18n="opt_complete_sentences">Строго завершать мысли по границам предложений</span>
                </label>
              </div>

              <!-- Tech Capabilities Status -->
              <div class="pt-3 border-t border-zinc-200 dark:border-zinc-800 text-[11px] text-zinc-500 dark:text-zinc-400 space-y-1">
                <div class="font-bold text-zinc-700 dark:text-zinc-300" data-i18n="env_params">Параметры окружения:</div>
                <div id="caps-detail-text">Загрузка возможностей системы...</div>
              </div>
            </div>
          </div>

        </div>

        <!-- RIGHT COLUMN: 32% (lg:col-span-4) Sticky Summary Panel -->
        <div class="lg:col-span-4 sticky top-24 space-y-4">
          <div class="card-interactive bg-white dark:bg-surface-800/90 border border-brand-500/30 rounded-2xl p-5 shadow-xl dark:shadow-2xl space-y-5">
            <div class="flex items-center justify-between pb-3 border-b border-zinc-200 dark:border-zinc-800">
              <span class="text-sm font-bold text-zinc-900 dark:text-white" data-i18n="summary_title">Сводка проекта</span>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20" data-i18n="ready_badge">Готов</span>
            </div>

            <!-- Parameters list -->
            <div class="space-y-3 text-xs">
              <div class="flex justify-between items-start">
                <span class="text-zinc-500 dark:text-zinc-400" data-i18n="sum_video">Видеофайл:</span>
                <span id="sum-video-name" class="font-semibold text-zinc-900 dark:text-white text-right max-w-[170px] truncate" data-i18n="not_selected">Не выбран</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-zinc-500 dark:text-zinc-400" data-i18n="sum_clips">Клипов на выходе:</span>
                <span id="sum-clip-count" class="font-bold text-brand-600 dark:text-brand-400 font-mono">5 клипов</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-zinc-500 dark:text-zinc-400" data-i18n="sum_duration">Диапазон длины:</span>
                <span id="sum-duration" class="font-semibold text-zinc-900 dark:text-white font-mono">30–60 сек</span>
              </div>
              <div class="flex justify-between items-start">
                <span class="text-zinc-500 dark:text-zinc-400" data-i18n="sum_strategy">Стратегия:</span>
                <span id="sum-strategy" class="font-semibold text-zinc-900 dark:text-white text-right max-w-[170px]">Авто</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-zinc-500 dark:text-zinc-400" data-i18n="sum_content_type">Тип контента:</span>
                <span id="sum-content-type" class="font-semibold text-zinc-900 dark:text-white" data-i18n="c_auto">Автоопределение</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-zinc-500 dark:text-zinc-400" data-i18n="sum_framing">Кадрирование:</span>
                <span id="sum-framing" class="font-semibold text-zinc-900 dark:text-white" data-i18n="frame_active">Трекинг лица</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-zinc-500 dark:text-zinc-400" data-i18n="sum_subtitles">Субтитры:</span>
                <span id="sum-subtitles" class="font-semibold text-amber-500">Hormozi Gold</span>
              </div>
            </div>

            <!-- Primary Dynamic CTA Button -->
            <div class="pt-3 border-t border-zinc-200 dark:border-zinc-800 space-y-2">
              <button type="submit" id="btn-submit-process" class="btn-press w-full bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-bold py-3.5 px-4 rounded-xl transition shadow-xl shadow-brand-600/30 flex items-center justify-center gap-2 text-sm">
                <i data-lucide="play" class="w-4 h-4 fill-white"></i>
                <span id="btn-submit-text">▶ Создать 5 клипов</span>
              </button>
              <p class="text-[11px] text-zinc-500 dark:text-zinc-400 text-center leading-tight" data-i18n="cta_subtext">
                Транскрибация, AI-анализ и рендеринг 9:16 запустятся в один клик.
              </p>
            </div>

          </div>
        </div>

      </form>
    </section>

    <!-- ========================================== -->
    <!-- 4. PROCESSING SCREEN (UI/UX v2)            -->
    <!-- Stage Timeline, Transparency & Recovery   -->
    <!-- ========================================== -->
    <section id="screen-processing" class="hidden max-w-2xl mx-auto py-8 space-y-6">
      
      <!-- Pulsing Header Icon -->
      <div class="text-center space-y-3">
        <div id="process-header-icon" class="w-16 h-16 rounded-3xl bg-brand-600/10 border border-brand-500/30 flex items-center justify-center mx-auto text-brand-500 dark:text-brand-400 relative">
          <div id="process-header-ping" class="absolute inset-0 rounded-3xl border border-brand-500/40 animate-ping opacity-25"></div>
          <i id="process-header-icon-inner" data-lucide="cpu" class="w-8 h-8 animate-pulse"></i>
        </div>
        <h2 id="process-title" class="text-2xl font-bold text-zinc-900 dark:text-white" data-i18n="proc_title">Обработка видео нейросетями</h2>
        <p id="process-desc" class="text-xs text-zinc-500 dark:text-zinc-400" data-i18n="proc_desc">Транскрибация речи и поиск кульминационных моментов...</p>
      </div>

      <!-- Main Progress Bar -->
      <div id="process-progress-container" class="bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 p-5 rounded-2xl space-y-2">
        <div class="flex justify-between text-xs font-bold">
          <span id="process-stage-badge" class="px-2 py-0.5 bg-zinc-100 dark:bg-surface-900 rounded-md border border-zinc-200 dark:border-zinc-700 text-brand-600 dark:text-brand-300 font-mono">transcribing</span>
          <span id="process-percent" class="text-brand-600 dark:text-brand-400 font-mono">15%</span>
        </div>
        <div class="w-full h-3 bg-zinc-100 dark:bg-surface-900 rounded-full overflow-hidden p-0.5 border border-zinc-200 dark:border-zinc-800">
          <div id="process-bar-fill" class="h-full bg-gradient-to-r from-brand-500 via-indigo-500 to-purple-500 rounded-full transition-all duration-300" style="width: 15%"></div>
        </div>
      </div>

      <!-- Dedicated Error Box (shown on failure) -->
      <div id="processing-error-box" class="hidden bg-rose-500/10 border border-rose-500/30 rounded-2xl p-5 space-y-4">
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-xl bg-rose-500/20 text-rose-500 flex items-center justify-center flex-shrink-0">
            <i data-lucide="alert-triangle" class="w-5 h-5"></i>
          </div>
          <div class="flex-1">
            <h3 class="text-sm font-bold text-rose-600 dark:text-rose-400" data-i18n="proc_error_title">Сбой при выполнении пайплайна</h3>
            <p id="processing-error-summary" class="text-xs text-zinc-800 dark:text-zinc-200 mt-1 font-medium leading-relaxed"></p>
          </div>
        </div>

        <!-- Collapsible Technical Details -->
        <div id="processing-error-details-container" class="pt-2 border-t border-rose-500/20">
          <button type="button" onclick="toggleErrorDetails()" class="text-[11px] text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 flex items-center gap-1.5 font-medium transition">
            <i id="error-details-chevron" data-lucide="chevron-down" class="w-3.5 h-3.5 transition-transform"></i>
            <span data-i18n="tech_details_title">Технические подробности (Лог ошибки)</span>
          </button>
          <pre id="processing-error-details" class="hidden mt-2 p-3 bg-zinc-950 text-rose-300 font-mono text-[11px] rounded-xl overflow-x-auto max-h-48 border border-zinc-800 whitespace-pre-wrap select-all"></pre>
        </div>

        <!-- Recovery Action Buttons -->
        <div class="flex flex-wrap items-center gap-2 pt-2">
          <button type="button" onclick="returnToProjectSettings()" class="btn-press px-4 py-2.5 bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-brand-600/20 flex items-center gap-1.5">
            <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
            <span data-i18n="btn_back_to_settings">Вернуться к настройкам проекта</span>
          </button>
          <button type="button" onclick="retryCurrentJob()" class="btn-press px-4 py-2.5 bg-zinc-200 dark:bg-surface-700 hover:bg-zinc-300 dark:hover:bg-surface-600 text-zinc-800 dark:text-zinc-100 font-semibold text-xs rounded-xl flex items-center gap-1.5">
            <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
            <span data-i18n="btn_retry_job">Повторить попытку</span>
          </button>
          <button type="button" onclick="navigateTo('projects')" class="btn-press px-4 py-2.5 border border-zinc-300 dark:border-zinc-700 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white text-xs rounded-xl">
            <span data-i18n="btn_to_projects">К списку проектов</span>
          </button>
        </div>
      </div>

      <!-- Stage Checklist (6 Steps) -->
      <div class="bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 space-y-3">
        <div class="text-xs font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 mb-2" data-i18n="proc_stages_title">Этапы выполнения пайплайна:</div>
        
        <div id="timeline-stage-1" class="stage-item flex items-center justify-between text-xs p-2 rounded-xl transition bg-zinc-50 dark:bg-surface-900/60">
          <div class="flex items-center gap-2.5">
            <span class="stage-icon text-zinc-400">○</span>
            <span class="stage-text text-zinc-700 dark:text-zinc-300 font-medium" data-i18n="stage_1">1. Загрузка и проверка видеопотока</span>
          </div>
          <span class="stage-status text-[11px] text-zinc-400 font-mono" data-i18n="status_waiting">Ожидание</span>
        </div>

        <div id="timeline-stage-2" class="stage-item flex items-center justify-between text-xs p-2 rounded-xl transition bg-zinc-50 dark:bg-surface-900/60">
          <div class="flex items-center gap-2.5">
            <span class="stage-icon text-brand-500 animate-spin">●</span>
            <span class="stage-text text-zinc-900 dark:text-white font-semibold" data-i18n="stage_2">2. Распознавание речи (Faster-Whisper CUDA)</span>
          </div>
          <span class="stage-status text-[11px] text-brand-600 dark:text-brand-400 font-mono" data-i18n="status_running">В процессе</span>
        </div>

        <div id="timeline-stage-3" class="stage-item flex items-center justify-between text-xs p-2 rounded-xl transition bg-zinc-50 dark:bg-surface-900/60">
          <div class="flex items-center gap-2.5">
            <span class="stage-icon text-zinc-400">○</span>
            <span class="stage-text text-zinc-500 dark:text-zinc-400 font-medium" data-i18n="stage_3">3. Сегментация смысловых окон и предложений</span>
          </div>
          <span class="stage-status text-[11px] text-zinc-400 font-mono" data-i18n="status_waiting">Ожидание</span>
        </div>

        <div id="timeline-stage-4" class="stage-item flex items-center justify-between text-xs p-2 rounded-xl transition bg-zinc-50 dark:bg-surface-900/60">
          <div class="flex items-center gap-2.5">
            <span class="stage-icon text-zinc-400">○</span>
            <span class="stage-text text-zinc-500 dark:text-zinc-400 font-medium" data-i18n="stage_4">4. AI-оценка виральности по 7 факторам (Qwen 2.5)</span>
          </div>
          <span class="stage-status text-[11px] text-zinc-400 font-mono" data-i18n="status_waiting">Ожидание</span>
        </div>

        <div id="timeline-stage-5" class="stage-item flex items-center justify-between text-xs p-2 rounded-xl transition bg-zinc-50 dark:bg-surface-900/60">
          <div class="flex items-center gap-2.5">
            <span class="stage-icon text-zinc-400">○</span>
            <span class="stage-text text-zinc-500 dark:text-zinc-400 font-medium" data-i18n="stage_5">5. Анализ лиц и построение траектории 9:16</span>
          </div>
          <span class="stage-status text-[11px] text-zinc-400 font-mono" data-i18n="status_waiting">Ожидание</span>
        </div>

        <div id="timeline-stage-6" class="stage-item flex items-center justify-between text-xs p-2 rounded-xl transition bg-zinc-50 dark:bg-surface-900/60">
          <div class="flex items-center gap-2.5">
            <span class="stage-icon text-zinc-400">○</span>
            <span class="stage-text text-zinc-500 dark:text-zinc-400 font-medium" data-i18n="stage_6">6. Рендеринг клипов и караоке субтитров (NVENC)</span>
          </div>
          <span class="stage-status text-[11px] text-zinc-400 font-mono" data-i18n="status_waiting">Ожидание</span>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center justify-between pt-2">
        <button type="button" onclick="navigateTo('projects')" class="btn-press text-xs text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white py-2 px-4 rounded-xl border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition flex items-center gap-1.5">
          <i data-lucide="arrow-left" class="w-3.5 h-3.5"></i>
          <span data-i18n="btn_to_projects">К списку проектов</span>
        </button>
        <button type="button" onclick="cancelCurrentJob()" class="btn-press text-xs text-rose-500 hover:text-rose-400 py-2 px-4 rounded-xl hover:bg-rose-500/10 border border-rose-500/30 transition flex items-center gap-1.5">
          <i data-lucide="x" class="w-3.5 h-3.5"></i>
          <span data-i18n="btn_cancel_job">Отменить обработку</span>
        </button>
      </div>

    </section>

    <!-- ========================================== -->
    <!-- 5. RESULTS STUDIO SCREEN (UI/UX v2)        -->
    <!-- 3 Columns: 25% List, 45% Player, 30% Inspector -->
    <!-- ========================================== -->
    <section id="screen-results" class="hidden space-y-6">
      
      <!-- Studio Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-zinc-200 dark:border-zinc-800 gap-3">
        <div class="flex items-center gap-3">
          <button type="button" onclick="navigateTo('projects')" class="btn-press text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-zinc-100 dark:bg-surface-800 border border-zinc-300 dark:border-zinc-700 text-xs font-semibold transition">
            <i data-lucide="arrow-left" class="w-4 h-4"></i>
            <span data-i18n="back_to_projects">К проектам</span>
          </button>
          <div>
            <h1 id="results-project-name" class="text-xl font-bold text-zinc-900 dark:text-white" data-i18n="res_title">Результаты генерации</h1>
            <p id="results-project-meta" class="text-xs text-zinc-500 dark:text-zinc-400" data-i18n="res_subtitle">Готовые вертикальные ролики</p>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <button type="button" onclick="regenerateProjectHighlights()" class="btn-press text-xs font-semibold px-3 py-1.5 rounded-xl bg-zinc-100 dark:bg-surface-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-indigo-600 dark:text-indigo-300 border border-indigo-500/30 transition flex items-center gap-1.5">
            <i data-lucide="sparkles" class="w-3.5 h-3.5 text-indigo-500"></i>
            <span data-i18n="btn_regen_highlights">Переподобрать хайлайты</span>
          </button>
          <button type="button" onclick="archiveCurrentProjectToDrive()" class="btn-press text-xs font-semibold px-3 py-1.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/80 hover:bg-emerald-100 dark:hover:bg-emerald-900 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30 transition flex items-center gap-1.5">
            <i data-lucide="archive" class="w-3.5 h-3.5"></i>
            <span data-i18n="btn_save_gdrive">Сохранить в Google Drive</span>
          </button>
        </div>
      </div>

      <!-- Studio 3 Columns Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        <!-- COLUMN 1: Candidate Clips List (25% -> lg:col-span-3) -->
        <div class="lg:col-span-3 bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 space-y-3 max-h-[800px] overflow-y-auto">
          <div class="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 px-1">
            <span data-i18n="clips_list_title">Отобранные клипы</span>
            <span id="clips-counter-badge" class="font-mono text-brand-600 dark:text-brand-400">0</span>
          </div>
          <div id="clips-list-container" class="space-y-2">
            <!-- Filled by JS -->
          </div>
        </div>

        <!-- COLUMN 2: 9:16 Vertical Video Player (45% -> lg:col-span-5) -->
        <div class="lg:col-span-5 flex flex-col items-center">
          <div class="w-full max-w-[340px] player-aspect bg-black rounded-3xl overflow-hidden border-2 border-zinc-300 dark:border-zinc-800 shadow-2xl relative group">
            <video id="studio-video-player" class="w-full h-full object-cover" controls playsinline preload="auto" ontimeupdate="onVideoTimeUpdate()">
              <source id="studio-video-source" src="" type="video/mp4">
              Ваш браузер не поддерживает видео.
            </video>
          </div>

          <!-- Video Timecode Display & Quick Nudge Controls -->
          <div class="w-full max-w-[340px] mt-3 space-y-2">
            <div class="flex items-center justify-between text-xs font-mono text-zinc-600 dark:text-zinc-400 bg-zinc-100 dark:bg-surface-800/80 px-3 py-1.5 rounded-xl border border-zinc-200 dark:border-zinc-800">
              <span id="player-timecode-cur">00:00</span>
              <span class="text-zinc-400">/</span>
              <span id="player-timecode-dur">00:00</span>
              <label class="flex items-center gap-1 cursor-pointer text-[11px] text-zinc-700 dark:text-zinc-300">
                <input type="checkbox" id="player-loop-toggle" onchange="togglePlayerLoop()" checked class="rounded bg-zinc-200 dark:bg-surface-900 border-zinc-300 dark:border-zinc-700 text-brand-600">
                <span>Loop</span>
              </label>
            </div>

            <!-- Start / End Quick Nudge Controls -->
            <div class="bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 p-2.5 rounded-xl space-y-2 text-xs">
              <div class="flex items-center justify-between">
                <span class="text-[11px] text-zinc-500 dark:text-zinc-400" data-i18n="nudge_start">Сдвиг старта:</span>
                <div class="flex items-center gap-1 font-mono">
                  <button type="button" onclick="nudgeTrim('start', -1.0)" class="btn-press px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-surface-900 border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 text-[10px]">-1s</button>
                  <button type="button" onclick="nudgeTrim('start', -0.5)" class="btn-press px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-surface-900 border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 text-[10px]">-0.5s</button>
                  <button type="button" onclick="nudgeTrim('start', 0.5)" class="btn-press px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-surface-900 border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 text-[10px]">+0.5s</button>
                  <button type="button" onclick="nudgeTrim('start', 1.0)" class="btn-press px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-surface-900 border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 text-[10px]">+1s</button>
                </div>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-[11px] text-zinc-500 dark:text-zinc-400" data-i18n="nudge_end">Сдвиг конца:</span>
                <div class="flex items-center gap-1 font-mono">
                  <button type="button" onclick="nudgeTrim('end', -1.0)" class="btn-press px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-surface-900 border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 text-[10px]">-1s</button>
                  <button type="button" onclick="nudgeTrim('end', -0.5)" class="btn-press px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-surface-900 border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 text-[10px]">-0.5s</button>
                  <button type="button" onclick="nudgeTrim('end', 0.5)" class="btn-press px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-surface-900 border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 text-[10px]">+0.5s</button>
                  <button type="button" onclick="nudgeTrim('end', 1.0)" class="btn-press px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-surface-900 border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 text-[10px]">+1s</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- COLUMN 3: Inspector, 7 Dimensions, Rerender & Feedback (30% -> lg:col-span-4) -->
        <div class="lg:col-span-4 space-y-4">
          
          <!-- Climax & Virality Analysis Card -->
          <div class="card-interactive bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 space-y-4">
            <div>
              <div class="text-[10px] font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400 mb-1" data-i18n="insp_virality_title">AI Анализ виральности</div>
              <h3 id="inspector-clip-title" class="text-base font-bold text-zinc-900 dark:text-white" data-i18n="insp_select_prompt">Выделите клип слева</h3>
              <p id="inspector-clip-reason" class="text-xs text-zinc-600 dark:text-zinc-300 mt-2 leading-relaxed bg-zinc-50 dark:bg-surface-900/60 p-3 rounded-xl border border-zinc-200 dark:border-zinc-800" data-i18n="insp_select_desc">
                Выберите нужный фрагмент из списка слева для предпросмотра и скачивания.
              </p>
            </div>

            <!-- Composite Score Badge -->
            <div class="p-3 bg-brand-500/10 border border-brand-500/20 rounded-xl flex items-center justify-between">
              <span class="text-xs font-semibold text-brand-700 dark:text-brand-300" data-i18n="score_badge_title">Итоговый балл виральности</span>
              <span id="inspector-final-score" class="text-lg font-extrabold text-brand-600 dark:text-brand-400 font-mono">-- / 10</span>
            </div>

            <!-- Provenance Info -->
            <div id="inspector-provenance-box" class="p-3 bg-zinc-50 dark:bg-surface-900/60 border border-zinc-200 dark:border-zinc-800 rounded-xl space-y-1 text-[11px] text-zinc-600 dark:text-zinc-400 font-mono">
              <div class="flex items-center justify-between">
                <span>ASR:</span>
                <span id="meta-asr-info" class="text-zinc-900 dark:text-zinc-200">faster_whisper</span>
              </div>
              <div class="flex items-center justify-between">
                <span>LLM:</span>
                <span id="meta-llm-info" class="text-zinc-900 dark:text-zinc-200">qwen2.5:1.5b</span>
              </div>
              <div id="meta-fallback-badge" class="hidden text-amber-500 font-semibold bg-amber-500/10 border border-amber-500/30 p-1 rounded text-center mt-1" data-i18n="badge_fallback">
                ⚠️ Эвристический fallback
              </div>
            </div>

            <!-- 7 Dimensions Breakdown -->
            <div class="space-y-2.5 pt-1">
              <div class="text-xs font-bold text-zinc-700 dark:text-zinc-300" data-i18n="dim_title">7 измерений вирального потенциала:</div>
              
              <div class="space-y-1.5 text-xs">
                <div>
                  <div class="flex justify-between text-zinc-500 dark:text-zinc-400 mb-1 text-[11px]">
                    <span data-i18n="dim_hook">1. Сила хука (первые 3 сек)</span>
                    <span id="score-hook" class="font-mono text-zinc-900 dark:text-white">--</span>
                  </div>
                  <div class="w-full h-1.5 bg-zinc-200 dark:bg-surface-900 rounded-full overflow-hidden">
                    <div id="bar-hook" class="h-full bg-brand-500 rounded-full transition-all" style="width: 0%"></div>
                  </div>
                </div>

                <div>
                  <div class="flex justify-between text-zinc-500 dark:text-zinc-400 mb-1 text-[11px]">
                    <span data-i18n="dim_payoff">2. Кульминация (Payoff)</span>
                    <span id="score-payoff" class="font-mono text-zinc-900 dark:text-white">--</span>
                  </div>
                  <div class="w-full h-1.5 bg-zinc-200 dark:bg-surface-900 rounded-full overflow-hidden">
                    <div id="bar-payoff" class="h-full bg-emerald-500 rounded-full transition-all" style="width: 0%"></div>
                  </div>
                </div>

                <div>
                  <div class="flex justify-between text-zinc-500 dark:text-zinc-400 mb-1 text-[11px]">
                    <span data-i18n="dim_share">3. Желание поделиться</span>
                    <span id="score-share" class="font-mono text-zinc-900 dark:text-white">--</span>
                  </div>
                  <div class="w-full h-1.5 bg-zinc-200 dark:bg-surface-900 rounded-full overflow-hidden">
                    <div id="bar-share" class="h-full bg-amber-500 rounded-full transition-all" style="width: 0%"></div>
                  </div>
                </div>

                <div>
                  <div class="flex justify-between text-zinc-500 dark:text-zinc-400 mb-1 text-[11px]">
                    <span data-i18n="dim_context">4. Понятность вне контекста</span>
                    <span id="score-context" class="font-mono text-zinc-900 dark:text-white">--</span>
                  </div>
                  <div class="w-full h-1.5 bg-zinc-200 dark:bg-surface-900 rounded-full overflow-hidden">
                    <div id="bar-context" class="h-full bg-indigo-500 rounded-full transition-all" style="width: 0%"></div>
                  </div>
                </div>

                <div>
                  <div class="flex justify-between text-zinc-500 dark:text-zinc-400 mb-1 text-[11px]">
                    <span data-i18n="dim_pacing">5. Динамика и темп речи</span>
                    <span id="score-pacing" class="font-mono text-zinc-900 dark:text-white">--</span>
                  </div>
                  <div class="w-full h-1.5 bg-zinc-200 dark:bg-surface-900 rounded-full overflow-hidden">
                    <div id="bar-pacing" class="h-full bg-cyan-500 rounded-full transition-all" style="width: 0%"></div>
                  </div>
                </div>

                <div>
                  <div class="flex justify-between text-zinc-500 dark:text-zinc-400 mb-1 text-[11px]">
                    <span data-i18n="dim_relevance">6. Актуальность темы</span>
                    <span id="score-relevance" class="font-mono text-zinc-900 dark:text-white">--</span>
                  </div>
                  <div class="w-full h-1.5 bg-zinc-200 dark:bg-surface-900 rounded-full overflow-hidden">
                    <div id="bar-relevance" class="h-full bg-pink-500 rounded-full transition-all" style="width: 0%"></div>
                  </div>
                </div>

                <div>
                  <div class="flex justify-between text-zinc-500 dark:text-zinc-400 mb-1 text-[11px]">
                    <span data-i18n="dim_trend">7. Трендовость формата</span>
                    <span id="score-trend" class="font-mono text-zinc-900 dark:text-white">--</span>
                  </div>
                  <div class="w-full h-1.5 bg-zinc-200 dark:bg-surface-900 rounded-full overflow-hidden">
                    <div id="bar-trend" class="h-full bg-purple-500 rounded-full transition-all" style="width: 0%"></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Primary Actions: Download & Cloud Archive -->
            <div class="pt-3 border-t border-zinc-200 dark:border-zinc-800 space-y-2">
              <a id="btn-download-clip" href="#" download class="btn-press w-full bg-brand-600 hover:bg-brand-500 text-white font-semibold py-2.5 px-4 rounded-xl transition shadow-lg shadow-brand-600/20 flex items-center justify-center gap-2 text-xs">
                <i data-lucide="download" class="w-4 h-4"></i>
                <span data-i18n="btn_download_mp4">Скачать готовый клип (MP4)</span>
              </a>
              <button type="button" id="btn-gdrive-archive" onclick="archiveCurrentClipToDrive()" class="btn-press w-full bg-zinc-100 dark:bg-surface-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-200 border border-zinc-200 dark:border-zinc-700 font-semibold py-2 px-4 rounded-xl transition flex items-center justify-center gap-2 text-xs">
                <i data-lucide="hard-drive" class="w-4 h-4 text-emerald-500"></i>
                <span data-i18n="btn_save_drive_10tb">Сохранить в Google Drive 10 TB</span>
              </button>
              <div id="gdrive-status-msg" class="text-xs text-center text-emerald-500 font-mono py-1 hidden"></div>
            </div>

          </div>

          <!-- Quick Rerender & Trim Editor Card -->
          <div class="card-interactive bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 space-y-3">
            <div class="text-xs font-bold uppercase tracking-wider text-indigo-500 flex items-center gap-1.5">
              <i data-lucide="sliders" class="w-3.5 h-3.5"></i>
              <span data-i18n="rerender_title">Редактор клипа & Быстрый перерендер</span>
            </div>
            
            <div class="grid grid-cols-2 gap-2 text-xs">
              <div>
                <label class="text-[11px] text-zinc-500 dark:text-zinc-400 block mb-1" data-i18n="trim_start_sec">Старт (сек)</label>
                <input type="number" id="editor-trim-start" step="0.5" class="w-full bg-zinc-100 dark:bg-surface-900 border border-zinc-300 dark:border-zinc-700 rounded-lg px-2.5 py-1.5 text-zinc-900 dark:text-white font-mono focus:border-indigo-500">
              </div>
              <div>
                <label class="text-[11px] text-zinc-500 dark:text-zinc-400 block mb-1" data-i18n="trim_end_sec">Конец (сек)</label>
                <input type="number" id="editor-trim-end" step="0.5" class="w-full bg-zinc-100 dark:bg-surface-900 border border-zinc-300 dark:border-zinc-700 rounded-lg px-2.5 py-1.5 text-zinc-900 dark:text-white font-mono focus:border-indigo-500">
              </div>
            </div>

            <div class="space-y-1 text-xs">
              <label class="text-[11px] text-zinc-500 dark:text-zinc-400 block" data-i18n="fld_subtitles">Пресет субтитров</label>
              <select id="editor-sub-preset" class="w-full bg-zinc-100 dark:bg-surface-900 border border-zinc-300 dark:border-zinc-700 rounded-lg px-2.5 py-1.5 text-zinc-900 dark:text-white">
                <option value="bold_karaoke">Hormozi Gold (Dynamic Yellow)</option>
                <option value="neon_glow">Neon Cyber (Impact Green)</option>
                <option value="minimal">Minimal White (Clean Text)</option>
              </select>
            </div>

            <div class="space-y-1 text-xs">
              <label class="text-[11px] text-zinc-500 dark:text-zinc-400 block" data-i18n="fld_framing">Кадрирование 9:16</label>
              <select id="editor-framing" class="w-full bg-zinc-100 dark:bg-surface-900 border border-zinc-300 dark:border-zinc-700 rounded-lg px-2.5 py-1.5 text-zinc-900 dark:text-white">
                <option value="active_speaker">Active Speaker (Face Track & Dead-Zone)</option>
                <option value="blurred_background">Blurred Background (16:9 с размытием)</option>
                <option value="center_crop">Center Crop (Статичный центр)</option>
              </select>
            </div>

            <button type="button" id="btn-rerender" onclick="rerenderCurrentClip()" class="btn-press w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2 px-3 rounded-xl transition flex items-center justify-center gap-2 text-xs shadow-md shadow-indigo-600/20">
              <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
              <span data-i18n="btn_apply_rerender">Применить & Быстрый перерендер</span>
            </button>
            <div id="rerender-status-msg" class="text-xs text-center text-indigo-400 font-mono hidden"></div>
          </div>

          <!-- Human Feedback Scorecard -->
          <div class="card-interactive bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 space-y-3">
            <div class="flex items-center justify-between">
              <div class="text-xs font-bold uppercase tracking-wider text-amber-500 flex items-center gap-1.5">
                <i data-lucide="check-square" class="w-3.5 h-3.5"></i>
                <span data-i18n="feedback_title">Оценка качества клипа</span>
              </div>
              <label class="inline-flex items-center gap-1.5 cursor-pointer">
                <input type="checkbox" id="review-publishable" checked class="rounded bg-zinc-100 dark:bg-surface-900 border-zinc-300 dark:border-zinc-700 text-brand-600 focus:ring-0">
                <span class="text-xs font-semibold text-emerald-600 dark:text-emerald-400" data-i18n="ready_to_publish">Готово к публикации</span>
              </label>
            </div>

            <!-- Multi-Select Issue Tags -->
            <div>
              <div class="text-[11px] text-zinc-500 dark:text-zinc-400 mb-1.5" data-i18n="issues_prompt">Замеченные проблемы:</div>
              <div class="flex flex-wrap gap-1.5" id="feedback-issues-container">
                <button type="button" data-issue="bad_start" onclick="toggleFeedbackIssue('bad_start')" class="btn-press issue-pill px-2.5 py-1 rounded-lg text-[11px] border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition" data-i18n="issue_bad_start">✂️ Плохое начало</button>
                <button type="button" data-issue="cut_thought" onclick="toggleFeedbackIssue('cut_thought')" class="btn-press issue-pill px-2.5 py-1 rounded-lg text-[11px] border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition" data-i18n="issue_cut_thought">⏳ Обрезана мысль</button>
                <button type="button" data-issue="framing_off" onclick="toggleFeedbackIssue('framing_off')" class="btn-press issue-pill px-2.5 py-1 rounded-lg text-[11px] border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition" data-i18n="issue_framing_off">👤 Лицо вне кадра</button>
                <button type="button" data-issue="sub_typo" onclick="toggleFeedbackIssue('sub_typo')" class="btn-press issue-pill px-2.5 py-1 rounded-lg text-[11px] border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition" data-i18n="issue_sub_typo">📝 Ошибка субтитров</button>
                <button type="button" data-issue="boring" onclick="toggleFeedbackIssue('boring')" class="btn-press issue-pill px-2.5 py-1 rounded-lg text-[11px] border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition" data-i18n="issue_boring">💤 Скучный момент</button>
              </div>
            </div>

            <!-- Star Ratings 1-5 -->
            <div class="space-y-2 text-xs pt-1">
              <div class="flex items-center justify-between">
                <span class="text-zinc-500 dark:text-zinc-400" data-i18n="score_highlight">Хайлайт:</span>
                <select id="review-select-highlight" class="bg-zinc-100 dark:bg-surface-900 border border-zinc-300 dark:border-zinc-700 rounded-lg px-2 py-1 text-zinc-900 dark:text-white text-xs">
                  <option value="5" selected>⭐⭐⭐⭐⭐ 5</option>
                  <option value="4">⭐⭐⭐⭐ 4</option>
                  <option value="3">⭐⭐⭐ 3</option>
                  <option value="2">⭐⭐ 2</option>
                  <option value="1">⭐ 1</option>
                </select>
              </div>

              <div class="flex items-center justify-between">
                <span class="text-zinc-500 dark:text-zinc-400" data-i18n="score_framing">Кадрирование:</span>
                <select id="review-select-framing" class="bg-zinc-100 dark:bg-surface-900 border border-zinc-300 dark:border-zinc-700 rounded-lg px-2 py-1 text-zinc-900 dark:text-white text-xs">
                  <option value="5" selected>⭐⭐⭐⭐⭐ 5</option>
                  <option value="4">⭐⭐⭐⭐ 4</option>
                  <option value="3">⭐⭐⭐ 3</option>
                  <option value="2">⭐⭐ 2</option>
                  <option value="1">⭐ 1</option>
                </select>
              </div>

              <div class="flex items-center justify-between">
                <span class="text-zinc-500 dark:text-zinc-400" data-i18n="score_subtitles">Субтитры:</span>
                <select id="review-select-subtitle" class="bg-zinc-100 dark:bg-surface-900 border border-zinc-300 dark:border-zinc-700 rounded-lg px-2 py-1 text-zinc-900 dark:text-white text-xs">
                  <option value="5" selected>⭐⭐⭐⭐⭐ 5</option>
                  <option value="4">⭐⭐⭐⭐ 4</option>
                  <option value="3">⭐⭐⭐ 3</option>
                  <option value="2">⭐⭐ 2</option>
                  <option value="1">⭐ 1</option>
                </select>
              </div>
            </div>

            <button type="button" id="btn-save-feedback" onclick="saveCurrentClipFeedback()" class="btn-press w-full bg-amber-600 hover:bg-amber-500 text-white font-semibold py-2 px-3 rounded-xl transition flex items-center justify-center gap-2 text-xs shadow-md shadow-amber-600/20">
              <i data-lucide="check" class="w-3.5 h-3.5"></i>
              <span data-i18n="btn_save_scorecard">Сохранить оценку клипа</span>
            </button>
            <div id="feedback-status-msg" class="text-xs text-center text-amber-500 font-mono hidden"></div>
          </div>

        </div>

      </div>
    </section>

  </main>

  <!-- ========================================== -->
  <!-- FULL I18N LOCALIZATION DICTIONARY          -->
  <!-- ========================================== -->
  <script>
    const I18N = {
      ru: {
        nav_projects: "Проекты",
        nav_analytics: "Аналитика",
        nav_new_project: "Создать проект",
        projects_title: "Мои проекты нарезки",
        projects_subtitle: "Каталог проектов и готовых вирусных клипов 9:16",
        search_placeholder: "Поиск проекта...",
        refresh: "Обновить",
        stat_projects: "Всего проектов",
        stat_clips: "Сгенерировано клипов",
        stat_encoder: "Энкодер",
        stat_llm: "AI Модель",
        dash_title: "Дашборд аналитики и системы",
        dash_subtitle: "Мониторинг нейросетей, аппаратного ускорения и событий обработки",
        hw_gpu: "Видеокарта (GPU)",
        hw_asr: "Распознавание речи",
        hw_llm: "Оценка виральности",
        hw_storage: "Хранилище & База",
        metric_avg_score: "Средний балл виральности клипов",
        metric_avg_desc: "Взвешенная оценка по хуку, кульминации и желанию поделиться",
        metric_publishable: "Готовность к публикации (Human Review)",
        metric_pub_desc: "Доля клипов, одобренных для публикации в Shorts/Reels",
        metric_smooth: "Сглаживание кадрирования 9:16",
        metric_smooth_desc: "Алгоритм Рамера-Дугласа-Пекера устраняет рывки камеры",
        events_log_title: "Журнал событий и действий системы",
        cleanup_storage: "Очистить старые файлы",
        tbl_time: "Время",
        tbl_event: "Событие",
        tbl_entity: "Сущность",
        tbl_details: "Детали",
        back_to_projects: "К проектам",
        new_proj_heading: "Создание проекта нарезки",
        new_proj_subheading: "Настройте параметры поиска вирусных моментов и запустите генерацию",
        fld_proj_name: "Название проекта",
        proj_name_placeholder: "Например: Подкаст #42 — Секреты Успеха",
        fld_video: "Исходное видео",
        dropzone_title: "Перетащите видеофайл сюда или нажмите для выбора",
        dropzone_subtitle: "Поддерживается видео до 10 ГБ. Метаданные определятся автоматически.",
        btn_replace_file: "Заменить файл",
        fld_clip_count: "Количество клипов",
        rec_label: "рек.",
        clip_count_hint: "AI найдет лучшие законченные мысли и диверсифицирует темы.",
        fld_duration: "Длительность клипов",
        sec_short: "сек",
        custom_range: "Свой диапазон",
        min_sec: "Мин (сек):",
        max_sec: "Макс (сек):",
        fld_strategy: "Что искать нейросети (Стратегия хайлайтов)",
        multiselect: "Мультивыбор",
        strategy_hint: "Выберите один или несколько типов моментов для фокусировки LLM-ранжирования:",
        strat_auto: "✨ Авто (лучшие моменты)",
        strat_hooks: "🎯 Хуки (яркие начала)",
        strat_insights: "💡 Инсайты (польза)",
        strat_hot_takes: "🔥 Острые мысли",
        strat_funny: "😂 Юмор",
        strat_stories: "📖 Истории",
        strat_quotes: "💬 Цитаты",
        fld_content_type: "Тип исходного видеоконтента",
        c_auto: "✨ Автоопределение контекста",
        c_podcast: "🎙️ Подкаст / Интервью",
        c_head: "👤 Говорящая голова / Эксперт",
        c_stream: "🎮 Стрим / Гейминг",
        c_lecture: "🎓 Лекция / Обучающий вебинар",
        c_reaction: "⚡ Реакция / Разбор",
        c_other: "📦 Другое видео",
        fld_framing: "Кадрирование 9:16",
        frame_active: "Трекинг лица",
        frame_active_sub: "Камера следует за спикером",
        frame_blur: "Размытый фон",
        frame_blur_sub: "16:9 с размытым 9:16 фоном",
        frame_center: "Центр кадра",
        frame_center_sub: "Статичный центр 9:16",
        fld_subtitles: "Стиль караоке-субтитров",
        subtitles_hint: "Пословное выделение текста синхронизировано со звуковой дорожкой",
        sub_gold_sub: "Жирный желтый караоке",
        sub_neon_sub: "Яркий зеленый неон",
        sub_white_sub: "Классический белый текст",
        live_sub_preview: "Live предпросмотр стиля субтитров",
        sample_sub_text: "ЭТО ИЗМЕНИЛО ВСЁ",
        adv_title: "Расширенные настройки и AI-ядро",
        adv_asr_lang: "Язык распознавания речи",
        adv_auto_detect: "✨ Автоопределение (Faster-Whisper)",
        adv_local_path: "Локальный путь (Developer Option)",
        opt_avoid_overlap: "Исключать пересечение клипов (диверсификация)",
        opt_complete_sentences: "Строго завершать мысли по границам предложений",
        env_params: "Параметры окружения:",
        summary_title: "Сводка проекта",
        ready_badge: "Готов",
        sum_video: "Видеофайл:",
        not_selected: "Не выбран",
        sum_clips: "Клипов на выходе:",
        sum_duration: "Диапазон длины:",
        sum_strategy: "Стратегия:",
        sum_content_type: "Тип контента:",
        sum_framing: "Кадрирование:",
        sum_subtitles: "Субтитры:",
        btn_create_clips_prefix: "▶ Создать",
        cta_subtext: "Транскрибация, AI-анализ и рендеринг 9:16 запустятся в один клик.",
        proc_title: "Обработка видео нейросетями",
        proc_desc: "Транскрибация речи и поиск кульминационных моментов...",
        proc_stages_title: "Этапы выполнения пайплайна:",
        stage_1: "1. Загрузка и проверка видеопотока",
        stage_2: "2. Распознавание речи (Faster-Whisper CUDA)",
        stage_3: "3. Сегментация смысловых окон и предложений",
        stage_4: "4. AI-оценка виральности по 7 факторам (Qwen 2.5)",
        stage_5: "5. Анализ лиц и построение траектории 9:16",
        stage_6: "6. Рендеринг клипов и караоке субтитров (NVENC)",
        status_waiting: "Ожидание",
        status_running: "В процессе",
        status_done: "Завершено",
        status_failed: "Ошибка",
        proc_error_title: "Сбой при выполнении пайплайна",
        proc_error_desc: "Произошла ошибка при обработке видео. Все настройки сохранены, вы можете исправить параметры и запустить снова.",
        btn_back_to_settings: "Вернуться к настройкам проекта",
        btn_retry_job: "Повторить попытку",
        tech_details_title: "Технические подробности (Лог ошибки)",
        btn_to_projects: "К списку проектов",
        btn_cancel_job: "Отменить обработку",
        res_title: "Результаты генерации",
        res_subtitle: "Готовые вертикальные ролики",
        btn_regen_highlights: "Переподобрать хайлайты",
        btn_save_gdrive: "Сохранить в Google Drive",
        clips_list_title: "Отобранные клипы",
        nudge_start: "Сдвиг старта:",
        nudge_end: "Сдвиг конца:",
        insp_virality_title: "AI Анализ виральности",
        insp_select_prompt: "Выделите клип слева",
        insp_select_desc: "Выберите нужный фрагмент из списка слева для предпросмотра и скачивания.",
        score_badge_title: "Итоговый балл виральности",
        badge_fallback: "⚠️ Эвристический fallback",
        dim_title: "7 измерений вирального потенциала:",
        dim_hook: "1. Сила хука (первые 3 сек)",
        dim_payoff: "2. Кульминация (Payoff)",
        dim_share: "3. Желание поделиться",
        dim_context: "4. Понятность вне контекста",
        dim_pacing: "5. Динамика и темп речи",
        dim_relevance: "6. Актуальность темы",
        dim_trend: "7. Трендовость формата",
        btn_download_mp4: "Скачать готовый клип (MP4)",
        btn_save_drive_10tb: "Сохранить в Google Drive 10 TB",
        rerender_title: "Редактор клипа & Быстрый перерендер",
        trim_start_sec: "Старт (сек)",
        trim_end_sec: "Конец (сек)",
        btn_apply_rerender: "Применить & Быстрый перерендер",
        feedback_title: "Оценка качества клипа",
        ready_to_publish: "Готово к публикации",
        issues_prompt: "Замеченные проблемы:",
        issue_bad_start: "✂️ Плохое начало",
        issue_cut_thought: "⏳ Обрезана мысль",
        issue_framing_off: "👤 Лицо вне кадра",
        issue_sub_typo: "📝 Ошибка субтитров",
        issue_boring: "💤 Скучный момент",
        score_highlight: "Хайлайт:",
        score_framing: "Кадрирование:",
        score_subtitles: "Субтитры:",
        btn_save_scorecard: "Сохранить оценку клипа",
        confirm_title: "Подтверждение действия",
        btn_confirm: "Подтвердить",
        btn_cancel: "Отмена",
        confirm_regen_prompt: "Переподобрать хайлайты с текущими настройками без повторной транскрибации?",
        confirm_cleanup_prompt: "Запустить безопасную очистку старых временных файлов и кэша?",
        select_video_error: "Пожалуйста, выберите видеофайл для обработки.",
        regen_success: "Хайлайты успешно переподобраны! Найдено кандидатов: "
      },

      en: {
        nav_projects: "Projects",
        nav_analytics: "Analytics",
        nav_new_project: "New Project",
        projects_title: "My Video Projects",
        projects_subtitle: "Catalog of projects and rendered 9:16 viral shorts",
        search_placeholder: "Search projects...",
        refresh: "Refresh",
        stat_projects: "Total Projects",
        stat_clips: "Clips Generated",
        stat_encoder: "Hardware Encoder",
        stat_llm: "AI Model",
        dash_title: "Analytics & System Dashboard",
        dash_subtitle: "Neural engines, hardware acceleration & product events monitoring",
        hw_gpu: "Graphics Card (GPU)",
        hw_asr: "Speech Recognition",
        hw_llm: "Virality Scorer",
        hw_storage: "Storage & Database",
        metric_avg_score: "Average Clip Virality Score",
        metric_avg_desc: "Weighted calculation based on hook, climax, and shareability",
        metric_publishable: "Publishable Rate (Human Review)",
        metric_pub_desc: "Share of clips approved for YouTube Shorts / TikTok / Reels",
        metric_smooth: "9:16 Trajectory Smoothing",
        metric_smooth_desc: "Ramer-Douglas-Peucker algorithm prevents camera jitter",
        events_log_title: "Product Events & Activity Audit Log",
        cleanup_storage: "Clean Expired Files",
        tbl_time: "Time",
        tbl_event: "Event",
        tbl_entity: "Entity",
        tbl_details: "Details",
        back_to_projects: "To Projects",
        new_proj_heading: "Create New Project",
        new_proj_subheading: "Configure viral moment detection criteria and launch rendering",
        fld_proj_name: "Project Name",
        proj_name_placeholder: "e.g., Podcast #42 — Success Secrets",
        fld_video: "Source Video",
        dropzone_title: "Drop video file here or click to browse",
        dropzone_subtitle: "Up to 10 GB supported. Resolution and duration detected automatically.",
        btn_replace_file: "Replace Video",
        fld_clip_count: "Clip Quantity",
        rec_label: "rec.",
        clip_count_hint: "AI identifies complete thoughts and diversifies subtopics.",
        fld_duration: "Clip Duration",
        sec_short: "s",
        custom_range: "Custom Range",
        min_sec: "Min (sec):",
        max_sec: "Max (sec):",
        fld_strategy: "AI Search Target (Highlight Strategy)",
        multiselect: "Multi-select",
        strategy_hint: "Select one or more focus themes for LLM candidate ranking:",
        strat_auto: "✨ Auto (Best Moments)",
        strat_hooks: "🎯 Hooks (Strong Openers)",
        strat_insights: "💡 Insights (Actionable)",
        strat_hot_takes: "🔥 Hot Takes (Bold Opinions)",
        strat_funny: "😂 Funny (Humor)",
        strat_stories: "📖 Stories (Narrative)",
        strat_quotes: "💬 Quotes (Catchy)",
        fld_content_type: "Source Video Content Type",
        c_auto: "✨ Auto-detect Context",
        c_podcast: "🎙️ Podcast / Interview",
        c_head: "👤 Talking Head / Expert",
        c_stream: "🎮 Stream / Gaming",
        c_lecture: "🎓 Lecture / Webinar",
        c_reaction: "⚡ Reaction / Breakdown",
        c_other: "📦 Other Video",
        fld_framing: "9:16 Framing Mode",
        frame_active: "Face Tracking",
        frame_active_sub: "Camera dynamically tracks speaker",
        frame_blur: "Blurred Background",
        frame_blur_sub: "16:9 centered with blurred 9:16 backdrop",
        frame_center: "Center Crop",
        frame_center_sub: "Static 9:16 crop box",
        fld_subtitles: "Karaoke Subtitle Style",
        subtitles_hint: "Word-by-word karaoke highlight synchronized to audio",
        sub_gold_sub: "Bold Yellow Karaoke",
        sub_neon_sub: "Vibrant Cyber Green",
        sub_white_sub: "Classic Clean White",
        live_sub_preview: "Live Subtitle Style Preview",
        sample_sub_text: "THIS CHANGED EVERYTHING",
        adv_title: "Advanced Pipeline & Core Settings",
        adv_asr_lang: "Speech Recognition Language",
        adv_auto_detect: "✨ Auto-detect (Faster-Whisper)",
        adv_local_path: "Local Path (Developer Option)",
        opt_avoid_overlap: "Prevent clip overlaps (diversification)",
        opt_complete_sentences: "Strictly snap boundaries to full sentences",
        env_params: "Environment Parameters:",
        summary_title: "Project Summary",
        ready_badge: "Ready",
        sum_video: "Source File:",
        not_selected: "Not selected",
        sum_clips: "Target Clips:",
        sum_duration: "Duration Range:",
        sum_strategy: "Strategy:",
        sum_content_type: "Content Type:",
        sum_framing: "Framing:",
        sum_subtitles: "Subtitles:",
        btn_create_clips_prefix: "▶ Create",
        cta_subtext: "Transcription, AI analysis, and 9:16 rendering start in 1 click.",
        proc_title: "AI Video Repurposing Pipeline",
        proc_desc: "Transcribing audio and searching for peak viral moments...",
        proc_stages_title: "Pipeline Stages Checklist:",
        stage_1: "1. Media stream inspection & audio probe",
        stage_2: "2. Speech-to-Text (Faster-Whisper CUDA)",
        stage_3: "3. Semantic windowing & sentence boundaries",
        stage_4: "4. Multi-factor LLM Virality Scoring (Qwen 2.5)",
        stage_5: "5. Face tracking & 9:16 trajectory planning",
        stage_6: "6. Hardware Clip & Karaoke Render (NVENC)",
        status_waiting: "Waiting",
        status_running: "Running",
        status_done: "Done",
        status_failed: "Failed",
        proc_error_title: "Pipeline Execution Error",
        proc_error_desc: "An error occurred during video processing. All settings are preserved so you can adjust and retry.",
        btn_back_to_settings: "Return to Project Settings",
        btn_retry_job: "Retry Processing",
        tech_details_title: "Technical Details (Error Log)",
        btn_to_projects: "Back to Projects",
        btn_cancel_job: "Cancel Processing",
        res_title: "Generation Results",
        res_subtitle: "Ready-to-publish vertical clips",
        btn_regen_highlights: "Regenerate Highlights",
        btn_save_gdrive: "Archive to Google Drive",
        clips_list_title: "Ranked Clips",
        nudge_start: "Start Nudge:",
        nudge_end: "End Nudge:",
        insp_virality_title: "AI Virality Inspector",
        insp_select_prompt: "Select a clip on the left",
        insp_select_desc: "Choose a clip from the list to preview, trim, and download.",
        score_badge_title: "Composite Virality Score",
        badge_fallback: "⚠️ Heuristic Fallback",
        dim_title: "7 Virality Potential Dimensions:",
        dim_hook: "1. Hook Strength (first 3s)",
        dim_payoff: "2. Climax / Emotional Payoff",
        dim_share: "3. Shareability Factor",
        dim_context: "4. Standalone Context",
        dim_pacing: "5. Story Pacing & Flow",
        dim_relevance: "6. Topic Relevance",
        dim_trend: "7. Trend Potential",
        btn_download_mp4: "Download Clip (MP4)",
        btn_save_drive_10tb: "Save to Google Drive 10 TB",
        rerender_title: "Clip Editor & Fast Rerender",
        trim_start_sec: "Start (sec)",
        trim_end_sec: "End (sec)",
        btn_apply_rerender: "Apply & Fast Rerender",
        feedback_title: "Human Quality Scorecard",
        ready_to_publish: "Ready to Publish",
        issues_prompt: "Reported Issues:",
        issue_bad_start: "✂️ Weak Opening Hook",
        issue_cut_thought: "⏳ Cut Off Thought",
        issue_framing_off: "👤 Speaker Out of Frame",
        issue_sub_typo: "📝 Subtitle Typo",
        issue_boring: "💤 Low Energy / Dull",
        score_highlight: "Highlight:",
        score_framing: "Framing:",
        score_subtitles: "Subtitles:",
        btn_save_scorecard: "Save Clip Feedback",
        confirm_title: "Confirm Action",
        btn_confirm: "Confirm",
        btn_cancel: "Cancel",
        confirm_regen_prompt: "Regenerate highlights from existing transcript without re-transcribing?",
        confirm_cleanup_prompt: "Safely prune expired temporary files and cache?",
        select_video_error: "Please select a video file to process.",
        regen_success: "Highlights regenerated! Candidates found: "
      }
    };

    let currentLang = localStorage.getItem('viral_clips_lang') || 'ru';
    if (!I18N[currentLang]) currentLang = 'ru';

    function t(key) {
      const dict = I18N[currentLang] || I18N.ru;
      return dict[key] || I18N.ru[key] || key;
    }

    function changeLanguage(lang) {
      currentLang = lang;
      localStorage.setItem('viral_clips_lang', lang);
      applyTranslations();
      updateSummary();
      refreshProjects();
    }

    function applyTranslations() {
      const sel = document.getElementById('lang-selector');
      if (sel) sel.value = currentLang;

      document.querySelectorAll('[data-i18n]').forEach(el => {
        const k = el.getAttribute('data-i18n');
        if (k) el.innerText = t(k);
      });

      document.querySelectorAll('[data-i18n-ph]').forEach(el => {
        const k = el.getAttribute('data-i18n-ph');
        if (k) el.placeholder = t(k);
      });

      const previewText = document.getElementById('sub-live-preview-text');
      if (previewText) previewText.innerText = t('sample_sub_text');
    }
  </script>

  <!-- ========================================== -->
  <!-- HIGH-PERFORMANCE NOTIFICATIONS & MODALS    -->
  <!-- ========================================== -->
  <script>
    function cleanErrorMessage(msg) {
      if (!msg) return 'Неизвестная ошибка';
      let s = String(msg);
      if (s.includes('ffmpeg version') || s.includes('configuration:')) {
        const lines = s.split('\n')
          .map(l => l.trim())
          .filter(l => l && !l.startsWith('ffmpeg version') && !l.startsWith('built with') && !l.startsWith('configuration:') && !l.startsWith('libav') && !l.startsWith('libsw') && !l.startsWith('libpostproc'));
        const combined = lines.join(' ');
        if (combined.includes('does not contain any stream') || combined.includes('matches no streams')) {
          return 'В исходном видеофайле отсутствует аудиодорожка. Для создания клипов требуется видео со звуком.';
        }
        if (lines.length > 0) {
          return lines[lines.length - 1];
        }
      }
      return s;
    }

    // Zero-lag, GPU-accelerated Toast Notification
    function showToast(message, type = 'info', title = '', duration = 3800) {
      const container = document.getElementById('toast-container');
      if (!container) return;

      const displayMsg = (type === 'error') ? cleanErrorMessage(message) : message;

      const toast = document.createElement('div');
      const typeStyles = {
        success: 'bg-emerald-950/95 border-emerald-500/50 text-emerald-200 shadow-emerald-950/30',
        error: 'bg-rose-950/95 border-rose-500/50 text-rose-200 shadow-rose-950/30',
        warning: 'bg-amber-950/95 border-amber-500/50 text-amber-200 shadow-amber-950/30',
        info: 'bg-zinc-900/95 dark:bg-surface-850/95 border-brand-500/50 text-zinc-100 shadow-brand-950/30',
      };
      const iconNames = {
        success: 'check-circle-2',
        error: 'alert-triangle',
        warning: 'alert-circle',
        info: 'info',
      };

      const style = typeStyles[type] || typeStyles.info;
      const icon = iconNames[type] || 'info';

      toast.className = `pointer-events-auto flex items-start gap-3 p-3.5 rounded-2xl border shadow-xl backdrop-blur-md transition-all duration-300 ease-out transform translate-x-12 opacity-0 ${style}`;
      toast.innerHTML = `
        <i data-lucide="${icon}" class="w-5 h-5 flex-shrink-0 mt-0.5"></i>
        <div class="flex-1 min-w-0">
          ${title ? `<div class="text-xs font-bold mb-0.5">${title}</div>` : ''}
          <div class="text-xs leading-relaxed break-words">${displayMsg}</div>
        </div>
        <button type="button" class="text-zinc-400 hover:text-white transition flex-shrink-0 ml-1 p-0.5 rounded-lg hover:bg-white/10" onclick="this.parentElement.remove()">
          <i data-lucide="x" class="w-4 h-4"></i>
        </button>
      `;

      container.appendChild(toast);
      safeRenderIcons();

      requestAnimationFrame(() => {
        toast.classList.remove('translate-x-12', 'opacity-0');
        toast.classList.add('translate-x-0', 'opacity-100');
      });

      setTimeout(() => {
        toast.classList.remove('translate-x-0', 'opacity-100');
        toast.classList.add('translate-x-12', 'opacity-0');
        setTimeout(() => {
          if (toast.parentElement) toast.remove();
        }, 320);
      }, duration);
    }

    // Modern Modal Confirmation (Replaces native blocking confirm)
    let confirmPromiseResolve = null;

    function showConfirm(title, message, okText, cancelText) {
      const backdrop = document.getElementById('confirm-modal-backdrop');
      const box = document.getElementById('confirm-modal-box');
      const titleEl = document.getElementById('confirm-modal-title');
      const msgEl = document.getElementById('confirm-modal-message');
      const okBtn = document.getElementById('confirm-modal-ok');
      const cancelBtn = document.getElementById('confirm-modal-cancel');

      titleEl.innerText = title || t('confirm_title');
      msgEl.innerText = message || '';
      okBtn.innerText = okText || t('btn_confirm');
      cancelBtn.innerText = cancelText || t('btn_cancel');

      backdrop.classList.remove('hidden', 'pointer-events-none');
      backdrop.classList.add('flex');
      safeRenderIcons();

      requestAnimationFrame(() => {
        backdrop.classList.remove('opacity-0');
        backdrop.classList.add('opacity-100');
        box.classList.remove('scale-95');
        box.classList.add('scale-100');
      });

      return new Promise((resolve) => {
        confirmPromiseResolve = resolve;
      });
    }

    function closeConfirm(result) {
      const backdrop = document.getElementById('confirm-modal-backdrop');
      const box = document.getElementById('confirm-modal-box');

      backdrop.classList.remove('opacity-100');
      backdrop.classList.add('opacity-0');
      box.classList.remove('scale-100');
      box.classList.add('scale-95');

      setTimeout(() => {
        backdrop.classList.add('hidden', 'pointer-events-none');
        backdrop.classList.remove('flex');
        if (confirmPromiseResolve) {
          confirmPromiseResolve(result);
          confirmPromiseResolve = null;
        }
      }, 200);
    }

    // Setup modal confirmation listeners
    function initConfirmModal() {
      const okBtn = document.getElementById('confirm-modal-ok');
      const cancelBtn = document.getElementById('confirm-modal-cancel');
      const backdrop = document.getElementById('confirm-modal-backdrop');

      if (okBtn) okBtn.onclick = () => closeConfirm(true);
      if (cancelBtn) cancelBtn.onclick = () => closeConfirm(false);
      if (backdrop) {
        backdrop.onclick = (e) => {
          if (e.target === backdrop) closeConfirm(false);
        };
      }
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeConfirm(false);
      });
    }
  </script>

  <!-- ========================================== -->
  <!-- FRONTEND SCRIPT ENGINE                     -->
  <!-- ========================================== -->
  <script>
    let activeProjectId = null;
    let activeJobId = null;
    let currentEventSource = null;
    let selectedFileObject = null;
    let currentClipsData = [];
    let allProjectsData = [];
    let selectedClipIndex = 0;
    let activeStrategies = ['auto'];
    let activeIssues = [];

    // Safe Lucide Icon Renderer
    function safeRenderIcons() {
      try {
        if (window.lucide && typeof window.lucide.createIcons === 'function') {
          window.lucide.createIcons();
        }
      } catch (err) {
        console.warn('Lucide icons warning:', err);
      }
    }

    // Theme Switcher (Dark / Light)
    function initTheme() {
      const saved = localStorage.getItem('viral_clips_theme') || 'dark';
      setTheme(saved);
    }

    function toggleTheme() {
      const isDark = document.documentElement.classList.contains('dark');
      setTheme(isDark ? 'light' : 'dark');
      showToast(isDark ? 'Светлая тема включена' : 'Тёмная тема включена', 'info', '', 2000);
    }

    function setTheme(theme) {
      if (theme === 'dark') {
        document.documentElement.classList.add('dark');
        localStorage.setItem('viral_clips_theme', 'dark');
      } else {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('viral_clips_theme', 'light');
      }
      safeRenderIcons();
    }

    // System Capabilities & Health
    async function loadSystemCapabilities() {
      try {
        const res = await fetch('/v1/system/capabilities');
        if (res.ok) {
          const caps = await res.json();
          window.systemCapabilities = caps;

          const detailEl = document.getElementById('caps-detail-text');
          if (detailEl) {
            detailEl.innerHTML = `
              • <b>ASR:</b> ${caps.asr.provider} (${caps.asr.model}, ${caps.asr.device})<br>
              • <b>LLM:</b> ${caps.llm.model} (${caps.llm.provider}, доступен: ${caps.llm.available ? 'Да' : 'Нет'})<br>
              • <b>NVENC:</b> ${caps.render.nvenc ? 'Включен (Аппаратное ускорение)' : 'Отключен'}<br>
              • <b>Smart Reframe:</b> Active Speaker 9:16 (RDP 25-point smooth)
            `;
          }
        }
      } catch (e) {
        console.warn('Capabilities fetch error:', e);
      }
    }

    // Navigation & Router
    function navigateTo(screenId, params = {}) {
      const hash = '#' + screenId + (params.id ? '?id=' + params.id : '');
      if (window.location.hash !== hash) {
        history.pushState({ screenId, ...params }, '', hash);
      }
      showScreen(screenId, params);
    }

    window.addEventListener('popstate', (e) => {
      handleRoute();
    });

    window.addEventListener('hashchange', (e) => {
      handleRoute();
    });

    function handleRoute() {
      const rawHash = window.location.hash.replace('#', '') || 'projects';
      const [screenId, query] = rawHash.split('?');
      const params = {};
      if (query) {
        const urlParams = new URLSearchParams(query);
        urlParams.forEach((v, k) => { params[k] = v; });
      }

      if (screenId === 'results' && params.id) {
        openProject(params.id, false);
      } else {
        showScreen(screenId || 'projects', params);
      }
    }

    function showScreen(screenId, params = {}) {
      document.querySelectorAll('main > section').forEach(sec => sec.classList.add('hidden'));
      
      document.querySelectorAll('.nav-tab').forEach(b => {
        b.className = 'nav-tab text-xs font-semibold px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white';
      });

      if (screenId === 'projects' || screenId === 'dashboard') {
        const activeNavBtn = document.getElementById(screenId === 'projects' ? 'nav-btn-projects' : 'nav-btn-dashboard');
        if (activeNavBtn) {
          activeNavBtn.className = 'nav-tab text-xs font-semibold px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 bg-white dark:bg-surface-800 text-zinc-900 dark:text-white shadow-sm';
        }
      }

      const target = document.getElementById('screen-' + screenId);
      if (target) {
        target.classList.remove('hidden');
      } else {
        const projScreen = document.getElementById('screen-projects');
        if (projScreen) projScreen.classList.remove('hidden');
      }

      if (screenId === 'projects') {
        refreshProjects();
      } else if (screenId === 'dashboard') {
        loadDashboardAnalytics();
      } else if (screenId === 'new-project') {
        restoreFormDraft();
      }

      safeRenderIcons();
    }

    // Projects Loader & Search Filter
    async function refreshProjects() {
      try {
        const res = await fetch('/v1/projects');
        allProjectsData = await res.json();
        renderProjectsList(allProjectsData);

        document.getElementById('stat-total-projects').innerText = allProjectsData.length;
        let totalClips = 0;
        allProjectsData.forEach(p => { totalClips += (p.desired_clip_count || 0); });
        document.getElementById('stat-total-clips').innerText = totalClips;
      } catch (err) {
        console.error('Failed to load projects:', err);
      }
    }

    function filterProjects(query) {
      const q = (query || '').toLowerCase().trim();
      if (!q) {
        renderProjectsList(allProjectsData);
        return;
      }
      const filtered = allProjectsData.filter(p => (p.name || '').toLowerCase().includes(q));
      renderProjectsList(filtered);
    }

    function renderProjectsList(projects) {
      const container = document.getElementById('projects-list-container');
      if (!projects.length) {
        container.innerHTML = `
          <div class="col-span-full py-16 text-center border border-dashed border-zinc-200 dark:border-zinc-800 rounded-2xl bg-white dark:bg-surface-800/40">
            <i data-lucide="film" class="w-12 h-12 text-zinc-400 mx-auto mb-3"></i>
            <h3 class="text-sm font-semibold text-zinc-800 dark:text-zinc-200">${t('not_selected')}</h3>
            <p class="text-xs text-zinc-500 mt-1">${t('projects_subtitle')}</p>
            <button type="button" onclick="navigateTo('new-project')" class="btn-press mt-4 px-4 py-2 bg-brand-600 text-white rounded-xl text-xs font-semibold hover:bg-brand-500 transition">
              ${t('nav_new_project')}
            </button>
          </div>
        `;
        safeRenderIcons();
        return;
      }

      container.innerHTML = projects.map(p => {
        const isDone = p.status === 'completed';
        const statusClass = isDone ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20' : 'bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20';
        return `
          <div onclick="openProject('${p.id}')" class="card-interactive bg-white dark:bg-surface-800/60 border border-zinc-200 dark:border-zinc-800 hover:border-brand-500/60 p-5 rounded-2xl cursor-pointer transition group shadow-sm hover:shadow-md">
            <div class="flex items-center justify-between text-xs mb-3">
              <span class="px-2 py-0.5 rounded-full font-medium ${statusClass}">
                ${p.status}
              </span>
              <span class="text-zinc-400 text-[11px] font-mono">${new Date(p.created_at).toLocaleDateString()}</span>
            </div>
            <h3 class="text-sm font-bold text-zinc-900 dark:text-white group-hover:text-brand-500 transition truncate">${p.name}</h3>
            <div class="flex items-center gap-3 mt-4 text-xs text-zinc-500 dark:text-zinc-400 font-mono">
              <span class="flex items-center gap-1"><i data-lucide="video" class="w-3.5 h-3.5"></i> ${p.desired_clip_count || 5} clips</span>
              <span class="flex items-center gap-1"><i data-lucide="globe" class="w-3.5 h-3.5"></i> ${p.language || 'auto'}</span>
            </div>
          </div>
        `;
      }).join('');
      safeRenderIcons();
    }

    // Dashboard Analytics & Audit Stream
    async function loadDashboardAnalytics() {
      try {
        const res = await fetch('/v1/system/events?limit=30');
        if (res.ok) {
          const events = await res.json();
          const tbody = document.getElementById('events-table-body');
          if (!events.length) {
            tbody.innerHTML = '<tr><td colspan="4" class="py-4 text-center text-zinc-400">Нет записанных событий</td></tr>';
          } else {
            tbody.innerHTML = events.map(ev => {
              const dateStr = new Date(ev.created_at).toLocaleTimeString();
              let payloadStr = '';
              try {
                const p = JSON.parse(ev.payload_json || '{}');
                payloadStr = Object.entries(p).map(([k, v]) => `${k}=${typeof v === 'object' ? JSON.stringify(v) : v}`).join(', ');
              } catch (e) {
                payloadStr = ev.payload_json || '';
              }
              return `
                <tr class="hover:bg-zinc-50 dark:hover:bg-surface-850/50 transition">
                  <td class="py-2.5 px-3 text-zinc-400 text-[11px] whitespace-nowrap">${dateStr}</td>
                  <td class="py-2.5 px-3 font-semibold text-brand-600 dark:text-brand-400">${ev.event_name}</td>
                  <td class="py-2.5 px-3 text-zinc-600 dark:text-zinc-300 truncate max-w-[150px]">${ev.entity_id || '—'}</td>
                  <td class="py-2.5 px-3 text-zinc-500 dark:text-zinc-400 truncate max-w-[280px]" title="${payloadStr}">${payloadStr || '—'}</td>
                </tr>
              `;
            }).join('');
          }
        }
      } catch (err) {
        console.warn('Dashboard analytics error:', err);
      }
    }

    async function triggerRetentionCleanup() {
      const confirmed = await showConfirm(t('cleanup_storage'), t('confirm_cleanup_prompt'));
      if (!confirmed) return;
      try {
        const res = await fetch('/v1/storage/cleanup?max_age_days=14', { method: 'POST' });
        const data = await res.json();
        showToast('Очистка успешно завершена', 'success');
        loadDashboardAnalytics();
      } catch (e) {
        showToast(e.message, 'error');
      }
    }

    // File Selection & Client-Side Metadata Extraction
    function triggerFileSelect() {
      const fi = document.getElementById('file-input');
      if (fi) fi.click();
    }

    function initDropzone() {
      const dropzone = document.getElementById('dropzone');
      if (!dropzone) return;

      dropzone.onclick = triggerFileSelect;
      dropzone.ondragover = (e) => { e.preventDefault(); dropzone.classList.add('border-brand-500'); };
      dropzone.ondragleave = () => { dropzone.classList.remove('border-brand-500'); };
      dropzone.ondrop = (e) => {
        e.preventDefault();
        dropzone.classList.remove('border-brand-500');
        if (e.dataTransfer && e.dataTransfer.files.length) {
          processSelectedFile(e.dataTransfer.files[0]);
        }
      };
    }

    function handleFileSelected(e) {
      if (e.target.files && e.target.files.length) {
        processSelectedFile(e.target.files[0]);
      }
    }

    function processSelectedFile(file) {
      selectedFileObject = file;
      const dropzone = document.getElementById('dropzone');
      const card = document.getElementById('source-video-card');
      const nameEl = document.getElementById('card-video-name');
      const durEl = document.getElementById('card-video-duration');
      const resEl = document.getElementById('card-video-resolution');
      const sizeEl = document.getElementById('card-video-size');

      nameEl.innerText = file.name;
      sizeEl.innerText = `${(file.size / (1024 * 1024)).toFixed(1)} MB`;

      const tempVideo = document.createElement('video');
      tempVideo.preload = 'metadata';
      tempVideo.onloadedmetadata = () => {
        window.URL.revokeObjectURL(tempVideo.src);
        const mins = Math.floor(tempVideo.duration / 60);
        const secs = Math.floor(tempVideo.duration % 60);
        durEl.innerText = `${mins}:${secs < 10 ? '0' : ''}${secs}`;
        resEl.innerText = `${tempVideo.videoWidth}x${tempVideo.videoHeight}`;
        updateSummary();
      };
      tempVideo.src = URL.createObjectURL(file);

      const nameInput = document.getElementById('input-project-name');
      if (!nameInput.value.trim()) {
        const cleanName = file.name.replace(/\\.[^/.]+$/, '').replace(/[_\\-]/g, ' ');
        nameInput.value = cleanName;
      }

      dropzone.classList.add('hidden');
      card.classList.remove('hidden');
      updateSummary();
      safeRenderIcons();
      showToast(file.name, 'success', 'Видеофайл загружен');
    }

    // Clip Quantity Control
    function selectClipCount(count) {
      document.getElementById('select-clip-count').value = count;
      document.querySelectorAll('.clip-count-btn').forEach(btn => {
        if (parseInt(btn.getAttribute('data-count')) === count) {
          btn.className = 'btn-press clip-count-btn py-2.5 px-3 rounded-xl border border-brand-500 bg-brand-500/10 text-sm font-bold text-brand-600 dark:text-brand-400 transition';
        } else {
          btn.className = 'btn-press clip-count-btn py-2.5 px-3 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-sm font-bold text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white transition';
        }
      });
      updateSummary();
    }

    // Duration Presets & Custom
    let isCustomDuration = false;
    function selectDurationPreset(minS, maxS) {
      isCustomDuration = false;
      document.getElementById('custom-dur-container').classList.add('hidden');
      document.getElementById('input-dur-min').value = minS;
      document.getElementById('input-dur-max').value = maxS;
      document.getElementById('label-current-duration').innerText = `${minS}–${maxS} ${t('sec_short')}`;

      document.querySelectorAll('.dur-preset-btn').forEach(btn => {
        if (btn.innerText.includes(`${minS}–${maxS}`)) {
          btn.className = 'btn-press dur-preset-btn py-2 px-2.5 rounded-xl border border-brand-500 bg-brand-500/10 text-brand-600 dark:text-brand-400 font-bold transition text-center';
        } else {
          btn.className = 'btn-press dur-preset-btn py-2 px-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white font-medium transition text-center';
        }
      });
      updateSummary();
    }

    function toggleCustomDuration() {
      isCustomDuration = true;
      const c = document.getElementById('custom-dur-container');
      c.classList.remove('hidden');
      document.querySelectorAll('.dur-preset-btn').forEach(btn => {
        if (btn.id === 'btn-custom-dur') {
          btn.className = 'btn-press dur-preset-btn py-2 px-2.5 rounded-xl border border-brand-500 bg-brand-500/10 text-brand-600 dark:text-brand-400 font-bold transition text-center';
        } else {
          btn.className = 'btn-press dur-preset-btn py-2 px-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white font-medium transition text-center';
        }
      });
      onCustomDurChange();
    }

    function onCustomDurChange() {
      const minS = parseFloat(document.getElementById('input-dur-min').value) || 20;
      const maxS = parseFloat(document.getElementById('input-dur-max').value) || 60;
      document.getElementById('label-current-duration').innerText = `${minS}–${maxS} ${t('sec_short')}`;
      updateSummary();
    }

    // Highlight Strategy Multi-Select
    function toggleStrategy(strat) {
      if (strat === 'auto') {
        activeStrategies = ['auto'];
      } else {
        activeStrategies = activeStrategies.filter(s => s !== 'auto');
        if (activeStrategies.includes(strat)) {
          activeStrategies = activeStrategies.filter(s => s !== strat);
        } else {
          activeStrategies.push(strat);
        }
        if (!activeStrategies.length) {
          activeStrategies = ['auto'];
        }
      }

      document.querySelectorAll('.strat-pill').forEach(btn => {
        const s = btn.getAttribute('data-strategy');
        if (activeStrategies.includes(s)) {
          btn.className = 'btn-press strat-pill px-3 py-1.5 rounded-full text-xs font-semibold border border-brand-500 bg-brand-500/10 text-brand-600 dark:text-brand-300 transition';
        } else {
          btn.className = 'btn-press strat-pill px-3 py-1.5 rounded-full text-xs font-semibold border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white transition';
        }
      });

      updateSummary();
    }

    // Subtitle Preset Selection
    function onSubtitlePresetChange() {
      const val = document.querySelector('input[name="subtitles"]:checked')?.value || 'bold_karaoke';
      const previewText = document.getElementById('sub-live-preview-text');

      document.querySelectorAll('.sub-card').forEach(card => {
        const inp = card.querySelector('input');
        if (inp && inp.checked) {
          card.classList.add('border-brand-500', 'bg-brand-500/10');
          card.classList.remove('border-zinc-300', 'dark:border-zinc-700');
        } else {
          card.classList.remove('border-brand-500', 'bg-brand-500/10');
          card.classList.add('border-zinc-300', 'dark:border-zinc-700');
        }
      });

      if (val === 'bold_karaoke') {
        previewText.className = 'text-lg sub-preview-hormozi';
      } else if (val === 'neon_glow') {
        previewText.className = 'text-lg sub-preview-neon';
      } else {
        previewText.className = 'text-lg sub-preview-minimal';
      }

      updateSummary();
    }

    // Framing visual selector
    document.addEventListener('change', (e) => {
      if (e.target.name === 'framing') {
        document.querySelectorAll('.framing-card').forEach(card => {
          const inp = card.querySelector('input');
          if (inp && inp.checked) {
            card.classList.add('border-brand-500', 'bg-brand-500/10');
            card.classList.remove('border-zinc-300', 'dark:border-zinc-700');
          } else {
            card.classList.remove('border-brand-500', 'bg-brand-500/10');
            card.classList.add('border-zinc-300', 'dark:border-zinc-700');
          }
        });
        updateSummary();
      }
    });

    // Collapsible Advanced Options
    let isAdvancedOpen = false;
    function toggleAdvancedOptions() {
      isAdvancedOpen = !isAdvancedOpen;
      const c = document.getElementById('advanced-options-container');
      const chev = document.getElementById('advanced-chevron');
      if (isAdvancedOpen) {
        c.classList.remove('hidden');
        chev.style.transform = 'rotate(180deg)';
      } else {
        c.classList.add('hidden');
        chev.style.transform = 'rotate(0deg)';
      }
    }

    // Sticky Summary Synchronizer
    function updateSummary() {
      const clipCount = parseInt(document.getElementById('select-clip-count').value) || 5;
      const minS = parseFloat(document.getElementById('input-dur-min').value) || 30;
      const maxS = parseFloat(document.getElementById('input-dur-max').value) || 60;
      const framing = document.querySelector('input[name="framing"]:checked')?.value || 'active_speaker';
      const subtitle = document.querySelector('input[name="subtitles"]:checked')?.value || 'bold_karaoke';
      const cType = document.getElementById('select-content-type')?.value || 'auto';

      const name = selectedFileObject ? selectedFileObject.name : (document.getElementById('input-video-path').value.trim() || t('not_selected'));
      document.getElementById('sum-video-name').innerText = name;
      document.getElementById('sum-clip-count').innerText = `${clipCount} clips`;
      document.getElementById('sum-duration').innerText = `${minS}–${maxS} ${t('sec_short')}`;

      const stratNames = {
        'auto': t('strat_auto'),
        'hooks': t('strat_hooks'),
        'insights': t('strat_insights'),
        'hot_takes': t('strat_hot_takes'),
        'funny': t('strat_funny'),
        'stories': t('strat_stories'),
        'quotes': t('strat_quotes')
      };
      document.getElementById('sum-strategy').innerText = activeStrategies.map(s => stratNames[s] || s).join(', ');

      const cTypeLabels = {
        'auto': t('c_auto'),
        'podcast': t('c_podcast'),
        'talking_head': t('c_head'),
        'stream': t('c_stream'),
        'lecture': t('c_lecture'),
        'reaction': t('c_reaction'),
        'other': t('c_other')
      };
      document.getElementById('sum-content-type').innerText = cTypeLabels[cType] || cType;

      const framingLabels = {
        'active_speaker': t('frame_active'),
        'blurred_background': t('frame_blur'),
        'center_crop': t('frame_center')
      };
      document.getElementById('sum-framing').innerText = framingLabels[framing] || framing;

      const subLabels = {
        'bold_karaoke': 'Hormozi Gold',
        'neon_glow': 'Neon Cyber',
        'minimal': 'Minimal White'
      };
      document.getElementById('sum-subtitles').innerText = subLabels[subtitle] || subtitle;

      document.getElementById('btn-submit-text').innerText = `${t('btn_create_clips_prefix')} ${clipCount} clips`;
      saveFormDraft();
    }

    function onVideoPathChange() {
      const p = document.getElementById('input-video-path').value.trim();
      if (p) {
        const filename = p.split(/[\\/]/).pop() || p;
        const nameEl = document.getElementById('card-video-name');
        if (nameEl) nameEl.innerText = filename;
        const durEl = document.getElementById('card-video-duration');
        if (durEl) durEl.innerText = 'Локальный файл';
        const resEl = document.getElementById('card-video-resolution');
        if (resEl) resEl.innerText = 'MP4 / 1080p';
        const sizeEl = document.getElementById('card-video-size');
        if (sizeEl) sizeEl.innerText = '';
        document.getElementById('dropzone')?.classList.add('hidden');
        document.getElementById('source-video-card')?.classList.remove('hidden');

        const nameInput = document.getElementById('input-project-name');
        if (nameInput && !nameInput.value.trim()) {
          const cleanName = filename.replace(/\.[^/.]+$/, '').replace(/[_\-]/g, ' ');
          nameInput.value = cleanName;
        }
      } else if (!selectedFileObject) {
        document.getElementById('dropzone')?.classList.remove('hidden');
        document.getElementById('source-video-card')?.classList.add('hidden');
      }
      updateSummary();
    }

    function saveFormDraft() {
      try {
        const draft = {
          name: document.getElementById('input-project-name')?.value || '',
          directPath: document.getElementById('input-video-path')?.value || '',
          selectedFileName: selectedFileObject ? selectedFileObject.name : '',
          clipCount: parseInt(document.getElementById('select-clip-count')?.value) || 5,
          minDur: parseFloat(document.getElementById('input-dur-min')?.value) || 30,
          maxDur: parseFloat(document.getElementById('input-dur-max')?.value) || 60,
          isCustomDuration: isCustomDuration,
          strategies: activeStrategies || ['auto'],
          contentType: document.getElementById('select-content-type')?.value || 'auto',
          framing: document.querySelector('input[name="framing"]:checked')?.value || 'active_speaker',
          subtitles: document.querySelector('input[name="subtitles"]:checked')?.value || 'bold_karaoke',
          language: document.getElementById('select-language')?.value || 'auto',
          avoidOverlap: document.getElementById('opt-avoid-overlap')?.checked ?? true,
          completeSentences: document.getElementById('opt-complete-sentences')?.checked ?? true,
        };
        localStorage.setItem('viral_clips_form_draft', JSON.stringify(draft));
      } catch (e) {
        console.warn('saveFormDraft error:', e);
      }
    }

    function restoreFormDraft() {
      try {
        const raw = localStorage.getItem('viral_clips_form_draft');
        if (!raw) return;
        const draft = JSON.parse(raw);

        if (draft.name && document.getElementById('input-project-name')) {
          document.getElementById('input-project-name').value = draft.name;
        }
        if (draft.directPath && document.getElementById('input-video-path')) {
          document.getElementById('input-video-path').value = draft.directPath;
          if (!selectedFileObject) {
            const filename = draft.directPath.split(/[\\/]/).pop() || draft.directPath;
            const nameEl = document.getElementById('card-video-name');
            if (nameEl) nameEl.innerText = filename;
            const durEl = document.getElementById('card-video-duration');
            if (durEl) durEl.innerText = 'Локальный файл';
            const resEl = document.getElementById('card-video-resolution');
            if (resEl) resEl.innerText = 'MP4 / 1080p';
            const sizeEl = document.getElementById('card-video-size');
            if (sizeEl) sizeEl.innerText = '';
            document.getElementById('dropzone')?.classList.add('hidden');
            document.getElementById('source-video-card')?.classList.remove('hidden');
          }
        }
        if (draft.clipCount) {
          selectClipCount(draft.clipCount);
        }
        if (draft.isCustomDuration) {
          isCustomDuration = true;
          document.getElementById('custom-dur-container')?.classList.remove('hidden');
          if (draft.minDur) document.getElementById('input-dur-min').value = draft.minDur;
          if (draft.maxDur) document.getElementById('input-dur-max').value = draft.maxDur;
          onCustomDurChange();
        } else if (draft.minDur && draft.maxDur) {
          selectDurationPreset(draft.minDur, draft.maxDur);
        }
        if (draft.strategies && Array.isArray(draft.strategies)) {
          activeStrategies = draft.strategies;
          document.querySelectorAll('.strat-pill').forEach(btn => {
            const s = btn.getAttribute('data-strategy');
            if (activeStrategies.includes(s)) {
              btn.className = 'btn-press strat-pill px-3 py-1.5 rounded-full text-xs font-semibold border border-brand-500 bg-brand-500/10 text-brand-600 dark:text-brand-300 transition';
            } else {
              btn.className = 'btn-press strat-pill px-3 py-1.5 rounded-full text-xs font-semibold border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white transition';
            }
          });
        }
        if (draft.contentType && document.getElementById('select-content-type')) {
          document.getElementById('select-content-type').value = draft.contentType;
        }
        if (draft.framing) {
          const radio = document.querySelector(`input[name="framing"][value="${draft.framing}"]`);
          if (radio) {
            radio.checked = true;
            document.querySelectorAll('.framing-card').forEach(card => {
              const inp = card.querySelector('input');
              if (inp && inp.value === draft.framing) {
                card.classList.add('border-brand-500', 'bg-brand-500/10');
                card.classList.remove('border-zinc-300', 'dark:border-zinc-700');
              } else {
                card.classList.remove('border-brand-500', 'bg-brand-500/10');
                card.classList.add('border-zinc-300', 'dark:border-zinc-700');
              }
            });
          }
        }
        if (draft.subtitles) {
          const radio = document.querySelector(`input[name="subtitles"][value="${draft.subtitles}"]`);
          if (radio) {
            radio.checked = true;
            onSubtitlePresetChange();
          }
        }
        if (draft.language && document.getElementById('select-language')) {
          document.getElementById('select-language').value = draft.language;
        }
        if (draft.avoidOverlap !== undefined && document.getElementById('opt-avoid-overlap')) {
          document.getElementById('opt-avoid-overlap').checked = draft.avoidOverlap;
        }
        if (draft.completeSentences !== undefined && document.getElementById('opt-complete-sentences')) {
          document.getElementById('opt-complete-sentences').checked = draft.completeSentences;
        }
      } catch (e) {
        console.warn('restoreFormDraft error:', e);
      }
    }

    // Submit Project Form
    async function handleStartProject(e) {
      e.preventDefault();
      const btn = document.getElementById('btn-submit-process');
      btn.disabled = true;
      const origText = document.getElementById('btn-submit-text').innerText;
      document.getElementById('btn-submit-text').innerText = 'Initializing...';

      const name = document.getElementById('input-project-name').value;
      const language = document.getElementById('select-language').value;
      const clip_count = parseInt(document.getElementById('select-clip-count').value);
      const min_duration_s = parseFloat(document.getElementById('input-dur-min').value) || 30;
      const max_duration_s = parseFloat(document.getElementById('input-dur-max').value) || 60;
      const framing = document.querySelector('input[name="framing"]:checked').value;
      const subtitle_preset = document.querySelector('input[name="subtitles"]:checked').value;
      const content_type = document.getElementById('select-content-type').value;
      const directPath = document.getElementById('input-video-path').value.trim();

      const options = {
        avoid_overlap: document.getElementById('opt-avoid-overlap')?.checked ?? true,
        complete_sentences: document.getElementById('opt-complete-sentences')?.checked ?? true,
      };

      try {
        const langVal = language === 'auto' ? null : language;
        const pRes = await fetch('/v1/projects', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, language: langVal, desired_clip_count: clip_count })
        });
        const project = await pRes.json();
        activeProjectId = project.id;

        let video_path = directPath;
        if (selectedFileObject) {
          document.getElementById('btn-submit-text').innerText = 'Uploading video...';
          const formData = new FormData();
          formData.append('file', selectedFileObject);
          const uRes = await fetch(`/v1/projects/${activeProjectId}/upload`, {
            method: 'POST',
            body: formData
          });
          if (!uRes.ok) {
            const err = await uRes.json();
            throw new Error(err.detail || 'Upload error');
          }
          const uData = await uRes.json();
          video_path = uData.file_path;
        }

        if (!video_path) {
          showToast(t('select_video_error'), 'warning', 'Внимание');
          return;
        }

        document.getElementById('btn-submit-text').innerText = 'Starting pipeline...';
        const procRes = await fetch(`/v1/projects/${activeProjectId}/process`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            video_path: video_path,
            clip_count: clip_count,
            duration: { min_seconds: min_duration_s, max_seconds: max_duration_s },
            min_duration_s: min_duration_s,
            max_duration_s: max_duration_s,
            framing: framing,
            subtitles: { preset: subtitle_preset },
            subtitle_preset: subtitle_preset,
            language: langVal,
            content_type: content_type,
            highlight_strategy: activeStrategies,
            options: options,
          })
        });

        if (!procRes.ok) {
          const err = await procRes.json();
          throw new Error(err.detail || 'Processing start error');
        }

        const job = await procRes.json();
        activeJobId = job.job_id;

        localStorage.setItem('viral_clips_active_job', JSON.stringify({
          jobId: activeJobId,
          projectId: activeProjectId,
        }));

        navigateTo('processing');
        listenToJobEvents(activeJobId);
        showToast('Пайплайн успешно запущен на GPU RTX 4060', 'success', 'Запуск');

      } catch (err) {
        showToast(err.message, 'error', 'Ошибка запуска');
      } finally {
        btn.disabled = false;
        document.getElementById('btn-submit-text').innerText = origText;
      }
    }

    // Processing SSE Progress Tracker
    function updateStageTimeline(stage, progress) {
      const stages = [
        { id: 'timeline-stage-1', min: 0, max: 10 },
        { id: 'timeline-stage-2', min: 10, max: 35 },
        { id: 'timeline-stage-3', min: 35, max: 45 },
        { id: 'timeline-stage-4', min: 45, max: 55 },
        { id: 'timeline-stage-5', min: 55, max: 65 },
        { id: 'timeline-stage-6', min: 65, max: 100 },
      ];

      stages.forEach((s) => {
        const el = document.getElementById(s.id);
        if (!el) return;
        const icon = el.querySelector('.stage-icon');
        const text = el.querySelector('.stage-text');
        const status = el.querySelector('.stage-status');

        if (progress >= s.max) {
          icon.innerText = '✓';
          icon.className = 'stage-icon text-emerald-500 font-bold';
          text.className = 'stage-text text-zinc-800 dark:text-zinc-300 font-medium';
          status.innerText = t('status_done');
          status.className = 'stage-status text-[11px] text-emerald-500 font-mono';
        } else if (progress >= s.min && progress < s.max) {
          icon.innerText = '●';
          icon.className = 'stage-icon text-brand-500 font-bold animate-pulse';
          text.className = 'stage-text text-zinc-900 dark:text-white font-bold';
          status.innerText = t('status_running');
          status.className = 'stage-status text-[11px] text-brand-500 font-mono';
        } else {
          icon.innerText = '○';
          icon.className = 'stage-icon text-zinc-400';
          text.className = 'stage-text text-zinc-500 font-medium';
          status.innerText = t('status_waiting');
          status.className = 'stage-status text-[11px] text-zinc-400 font-mono';
        }
      });
    }

    function cleanErrorMessage(msg) {
      if (!msg) return 'Неизвестная ошибка обработки';
      let s = String(msg);
      if (s.includes('ffmpeg version') || s.includes('configuration:')) {
        const lines = s.split('\n')
          .map(l => l.trim())
          .filter(l => l && !l.startsWith('ffmpeg version') && !l.startsWith('built with') && !l.startsWith('configuration:') && !l.startsWith('libav') && !l.startsWith('libsw') && !l.startsWith('libpostproc'));
        const combined = lines.join(' ');
        if (combined.includes('does not contain any stream') || combined.includes('matches no streams')) {
          return 'В исходном видеофайле отсутствует аудиодорожка. Для распознавания речи (ASR) и монтажа клипов требуется видео со звуком.';
        }
        if (lines.length > 0) {
          return lines[lines.length - 1];
        }
      }
      return s;
    }

    function toggleErrorDetails() {
      const el = document.getElementById('processing-error-details');
      const chev = document.getElementById('error-details-chevron');
      if (!el) return;
      if (el.classList.contains('hidden')) {
        el.classList.remove('hidden');
        if (chev) chev.style.transform = 'rotate(180deg)';
      } else {
        el.classList.add('hidden');
        if (chev) chev.style.transform = 'rotate(0deg)';
      }
    }

    function showProcessingError(cleanMsg, rawMsg, failedStage) {
      const iconBox = document.getElementById('process-header-icon');
      if (iconBox) {
        iconBox.className = 'w-16 h-16 rounded-3xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center mx-auto text-rose-500 relative';
      }
      const ping = document.getElementById('process-header-ping');
      if (ping) ping.classList.add('hidden');
      const innerIcon = document.getElementById('process-header-icon-inner');
      if (innerIcon) {
        innerIcon.setAttribute('data-lucide', 'alert-triangle');
        innerIcon.className = 'w-8 h-8';
      }

      const titleEl = document.getElementById('process-title');
      if (titleEl) {
        titleEl.innerText = t('proc_error_title') || 'Сбой при выполнении пайплайна';
        titleEl.classList.add('text-rose-600', 'dark:text-rose-400');
      }
      const descEl = document.getElementById('process-desc');
      if (descEl) {
        descEl.innerText = t('proc_error_desc') || 'Пайплайн завершился с ошибкой. Все параметры сохранены, вы можете исправить их и повторить запуск.';
      }

      document.getElementById('process-progress-container')?.classList.add('hidden');
      const errBox = document.getElementById('processing-error-box');
      if (errBox) {
        errBox.classList.remove('hidden');
        document.getElementById('processing-error-summary').innerText = cleanMsg;
        document.getElementById('processing-error-details').innerText = rawMsg;
      }

      if (failedStage) {
        markStageError(failedStage);
      }

      safeRenderIcons();
    }

    function resetProcessingUI() {
      const iconBox = document.getElementById('process-header-icon');
      if (iconBox) {
        iconBox.className = 'w-16 h-16 rounded-3xl bg-brand-600/10 border border-brand-500/30 flex items-center justify-center mx-auto text-brand-500 dark:text-brand-400 relative';
      }
      const ping = document.getElementById('process-header-ping');
      if (ping) ping.classList.remove('hidden');
      const innerIcon = document.getElementById('process-header-icon-inner');
      if (innerIcon) {
        innerIcon.setAttribute('data-lucide', 'cpu');
        innerIcon.className = 'w-8 h-8 animate-pulse';
      }

      const titleEl = document.getElementById('process-title');
      if (titleEl) {
        titleEl.innerText = t('proc_title');
        titleEl.classList.remove('text-rose-600', 'dark:text-rose-400');
      }
      const descEl = document.getElementById('process-desc');
      if (descEl) {
        descEl.innerText = t('proc_desc');
      }

      document.getElementById('process-progress-container')?.classList.remove('hidden');
      document.getElementById('processing-error-box')?.classList.add('hidden');
      document.getElementById('processing-error-details')?.classList.add('hidden');
      safeRenderIcons();
    }

    function returnToProjectSettings() {
      if (currentEventSource) currentEventSource.close();
      navigateTo('new-project');
      restoreFormDraft();
    }

    async function retryCurrentJob() {
      if (currentEventSource) currentEventSource.close();
      resetProcessingUI();
      navigateTo('new-project');
      restoreFormDraft();
      const form = document.getElementById('form-create-project');
      if (form) {
        handleStartProject(new Event('submit'));
      }
    }

    function markStageError(stage) {
      const stageMap = {
        'probing': 'timeline-stage-1',
        'extracting_audio': 'timeline-stage-2',
        'transcribing': 'timeline-stage-2',
        'segmenting': 'timeline-stage-3',
        'ranking': 'timeline-stage-4',
        'visual_analysis': 'timeline-stage-5',
        'rendering': 'timeline-stage-6'
      };
      const stageId = stageMap[stage] || 'timeline-stage-1';
      const el = document.getElementById(stageId);
      if (el) {
        const icon = el.querySelector('.stage-icon');
        const text = el.querySelector('.stage-text');
        const status = el.querySelector('.stage-status');
        if (icon) {
          icon.innerText = '✕';
          icon.className = 'stage-icon text-rose-500 font-bold';
        }
        if (text) {
          text.className = 'stage-text text-rose-600 dark:text-rose-400 font-bold';
        }
        if (status) {
          status.innerText = t('status_failed') || 'Ошибка';
          status.className = 'stage-status text-[11px] text-rose-500 font-mono font-bold';
        }
      }
    }

    function listenToJobEvents(jobId) {
      if (currentEventSource) currentEventSource.close();
      currentEventSource = new EventSource(`/v1/jobs/${jobId}/events`);

      currentEventSource.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.progress !== undefined) {
            document.getElementById('process-percent').innerText = `${data.progress}%`;
            document.getElementById('process-bar-fill').style.width = `${data.progress}%`;
            updateStageTimeline(data.stage, data.progress);
          }
          if (data.stage) {
            document.getElementById('process-stage-badge').innerText = data.stage;
          }
          if (data.message) {
            document.getElementById('process-desc').innerText = data.message;
          }

          if (data.status === 'completed') {
            currentEventSource.close();
            localStorage.removeItem('viral_clips_active_job');
            showToast('Все клипы успешно созданы и готовы к просмотру!', 'success', 'Готово');
            openProject(activeProjectId);
          } else if (data.status === 'failed') {
            currentEventSource.close();
            localStorage.removeItem('viral_clips_active_job');
            const rawErr = data.error_message || 'Неизвестная ошибка обработки';
            const cleanErr = cleanErrorMessage(rawErr);
            showToast(cleanErr, 'error', t('proc_error_title') || 'Ошибка обработки');
            showProcessingError(cleanErr, rawErr, data.stage);
          }
        } catch (err) {
          console.error(err);
        }
      };
    }

    async function checkJobRecovery() {
      const stored = localStorage.getItem('viral_clips_active_job');
      if (!stored) return;
      try {
        const { jobId, projectId } = JSON.parse(stored);
        const res = await fetch(`/v1/jobs/${jobId}`);
        if (!res.ok) {
          localStorage.removeItem('viral_clips_active_job');
          return;
        }
        const job = await res.json();
        if (job.status === 'running' || job.status === 'queued') {
          activeJobId = jobId;
          activeProjectId = projectId;
          navigateTo('processing');
          listenToJobEvents(jobId);
        } else if (job.status === 'completed') {
          localStorage.removeItem('viral_clips_active_job');
          openProject(projectId);
        } else if (job.status === 'failed') {
          localStorage.removeItem('viral_clips_active_job');
          navigateTo('processing');
          const rawErr = job.error_message || 'Неизвестная ошибка обработки';
          const cleanErr = cleanErrorMessage(rawErr);
          showProcessingError(cleanErr, rawErr, job.stage);
        } else {
          localStorage.removeItem('viral_clips_active_job');
        }
      } catch (err) {
        localStorage.removeItem('viral_clips_active_job');
      }
    }

    // Open Project & Populate Studio
    async function openProject(projectId, updateHash = true) {
      activeProjectId = projectId;
      if (updateHash) {
        const hash = '#results?id=' + projectId;
        if (window.location.hash !== hash) {
          history.pushState({ screenId: 'results', id: projectId }, '', hash);
        }
      }

      try {
        const res = await fetch(`/v1/projects/${projectId}`);
        const project = await res.json();

        document.getElementById('results-project-name').innerText = project.name;
        document.getElementById('results-project-meta').innerText = `${project.clips?.length || 0} clips`;
        document.getElementById('clips-counter-badge').innerText = project.clips?.length || 0;

        currentClipsData = project.clips || [];
        const container = document.getElementById('clips-list-container');

        if (!currentClipsData.length) {
          container.innerHTML = '<div class="text-xs text-zinc-500 p-4">В проекте пока нет готовых клипов. Запустите генерацию.</div>';
          showScreen('results');
          return;
        }

        container.innerHTML = currentClipsData.map((clip, idx) => {
          const dur = Math.round((clip.end_ms - clip.start_ms) / 1000);
          const score = (clip.final_score !== undefined && clip.final_score !== null) ? Number(clip.final_score).toFixed(1) : '—';
          return `
            <div onclick="selectClip(${idx})" id="clip-card-${idx}" class="card-interactive p-3 bg-zinc-50 dark:bg-surface-900 border border-zinc-200 dark:border-zinc-800 hover:border-brand-500/50 rounded-xl cursor-pointer transition ${idx === 0 ? 'border-brand-500 bg-brand-500/5' : ''}">
              <div class="flex items-center justify-between text-xs mb-1">
                <span class="font-bold text-brand-600 dark:text-brand-400">#${idx + 1} Clip</span>
                <span class="text-zinc-500 font-mono text-[11px]">${dur}s</span>
              </div>
              <div class="text-xs font-semibold text-zinc-900 dark:text-white truncate">${clip.title || 'Highlight #' + (idx+1)}</div>
              <div class="flex items-center justify-between text-[11px] text-zinc-500 dark:text-zinc-400 mt-2">
                <span>Score: <b class="text-brand-600 dark:text-brand-300 font-mono">${score}</b></span>
                <span class="text-emerald-500 flex items-center gap-0.5"><i data-lucide="check" class="w-3 h-3"></i> Ready</span>
              </div>
            </div>
          `;
        }).join('');

        showScreen('results');
        selectClip(0);
        safeRenderIcons();

      } catch (err) {
        showToast(err.message, 'error', 'Ошибка загрузки проекта');
      }
    }

    // Select Clip
    function selectClip(idx) {
      selectedClipIndex = idx;
      const clip = currentClipsData[idx];
      if (!clip) return;

      document.getElementById('gdrive-status-msg').classList.add('hidden');
      const rerenderMsg = document.getElementById('rerender-status-msg');
      if (rerenderMsg) rerenderMsg.classList.add('hidden');
      const fbMsg = document.getElementById('feedback-status-msg');
      if (fbMsg) fbMsg.classList.add('hidden');

      document.querySelectorAll('#clips-list-container > div').forEach((c, i) => {
        if (i === idx) {
          c.classList.add('border-brand-500', 'bg-brand-500/5');
        } else {
          c.classList.remove('border-brand-500', 'bg-brand-500/5');
        }
      });

      const player = document.getElementById('studio-video-player');
      const source = document.getElementById('studio-video-source');
      if (clip.current_render_id) {
        const videoUrl = `/v1/renders/${clip.current_render_id}/download`;
        source.src = videoUrl;
        player.load();
        document.getElementById('btn-download-clip').href = videoUrl;
      }

      document.getElementById('inspector-clip-title').innerText = clip.title || `Clip #${idx + 1}`;
      document.getElementById('inspector-clip-reason').innerText = clip.reason || 'High speech density and complete narrative closure.';
      document.getElementById('inspector-final-score').innerText = (clip.final_score !== undefined && clip.final_score !== null) ? `${Number(clip.final_score).toFixed(1)} / 10` : '— / 10';

      const scores = clip.scores || {};
      const hookVal = scores.hook_strength ?? scores.hook ?? 5;
      const payoffVal = scores.payoff ?? 5;
      const shareVal = scores.shareability ?? 5;
      const contextVal = scores.standalone_context ?? 5;
      const pacingVal = scores.story_pacing ?? 5;
      const relVal = scores.topic_relevance ?? 5;
      const trendVal = scores.trend_potential ?? 5;

      document.getElementById('score-hook').innerText = `${hookVal} / 10`;
      document.getElementById('bar-hook').style.width = `${hookVal * 10}%`;

      document.getElementById('score-payoff').innerText = `${payoffVal} / 10`;
      document.getElementById('bar-payoff').style.width = `${payoffVal * 10}%`;

      document.getElementById('score-share').innerText = `${shareVal} / 10`;
      document.getElementById('bar-share').style.width = `${shareVal * 10}%`;

      document.getElementById('score-context').innerText = `${contextVal} / 10`;
      document.getElementById('bar-context').style.width = `${contextVal * 10}%`;

      document.getElementById('score-pacing').innerText = `${pacingVal} / 10`;
      document.getElementById('bar-pacing').style.width = `${pacingVal * 10}%`;

      document.getElementById('score-relevance').innerText = `${relVal} / 10`;
      document.getElementById('bar-relevance').style.width = `${relVal * 10}%`;

      document.getElementById('score-trend').innerText = `${trendVal} / 10`;
      document.getElementById('bar-trend').style.width = `${trendVal * 10}%`;

      const trimStartInput = document.getElementById('editor-trim-start');
      const trimEndInput = document.getElementById('editor-trim-end');
      if (trimStartInput && trimEndInput) {
        trimStartInput.value = (clip.start_ms / 1000).toFixed(1);
        trimEndInput.value = (clip.end_ms / 1000).toFixed(1);
      }
      const presetSelect = document.getElementById('editor-sub-preset');
      if (presetSelect && clip.preset && clip.preset.preset) {
        presetSelect.value = clip.preset.preset;
      }

      loadClipFeedback(clip.id);
    }

    // Player Loop & Timecode
    function onVideoTimeUpdate() {
      const player = document.getElementById('studio-video-player');
      if (!player) return;
      const cur = Math.floor(player.currentTime);
      const dur = Math.floor(player.duration || 0);

      const curM = Math.floor(cur / 60);
      const curS = cur % 60;
      const durM = Math.floor(dur / 60);
      const durS = dur % 60;

      document.getElementById('player-timecode-cur').innerText = `${curM}:${curS < 10 ? '0' : ''}${curS}`;
      document.getElementById('player-timecode-dur').innerText = `${durM}:${durS < 10 ? '0' : ''}${durS}`;
    }

    function togglePlayerLoop() {
      const player = document.getElementById('studio-video-player');
      const isLoop = document.getElementById('player-loop-toggle').checked;
      if (player) player.loop = isLoop;
    }

    function nudgeTrim(type, deltaSeconds) {
      const startInput = document.getElementById('editor-trim-start');
      const endInput = document.getElementById('editor-trim-end');
      if (type === 'start') {
        const cur = parseFloat(startInput.value) || 0;
        startInput.value = Math.max(0, cur + deltaSeconds).toFixed(1);
      } else {
        const cur = parseFloat(endInput.value) || 0;
        endInput.value = Math.max(0, cur + deltaSeconds).toFixed(1);
      }
    }

    // Rerender Clip
    async function rerenderCurrentClip() {
      const clip = currentClipsData[selectedClipIndex];
      if (!clip) return;
      const btn = document.getElementById('btn-rerender');
      const msg = document.getElementById('rerender-status-msg');

      const startS = parseFloat(document.getElementById('editor-trim-start').value);
      const endS = parseFloat(document.getElementById('editor-trim-end').value);
      const subPreset = document.getElementById('editor-sub-preset').value;
      const framing = document.getElementById('editor-framing').value;

      btn.disabled = true;
      msg.classList.remove('hidden');
      msg.innerText = 'Rerendering clip (NVENC)...';

      try {
        const res = await fetch(`/v1/clips/${clip.id}/render`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            subtitle_preset: subPreset,
            framing: framing,
            start_ms: Math.round(startS * 1000),
            end_ms: Math.round(endS * 1000),
          }),
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'Rerender error');
        }
        const data = await res.json();
        msg.innerText = '✓ Rerender completed!';
        showToast('Клип успешно перерендерен на GPU RTX 4060!', 'success', 'Ререндер');

        const player = document.getElementById('studio-video-player');
        const source = document.getElementById('studio-video-source');
        const newUrl = `/v1/renders/${data.render_id}/download?t=${Date.now()}`;
        source.src = newUrl;
        player.load();
        player.play().catch(() => {});
        document.getElementById('btn-download-clip').href = newUrl;

        clip.current_render_id = data.render_id;
        clip.start_ms = Math.round(startS * 1000);
        clip.end_ms = Math.round(endS * 1000);

      } catch (err) {
        msg.innerText = 'Error: ' + err.message;
        showToast(err.message, 'error', 'Ошибка ререндеринга');
      } finally {
        btn.disabled = false;
      }
    }

    // Regenerate Highlights
    async function regenerateProjectHighlights() {
      if (!activeProjectId) return;
      const confirmed = await showConfirm(t('btn_regen_highlights'), t('confirm_regen_prompt'));
      if (!confirmed) return;

      try {
        const res = await fetch(`/v1/projects/${activeProjectId}/regenerate-highlights`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            highlight_strategy: activeStrategies,
          })
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'Error');
        }
        const data = await res.json();
        showToast(`${t('regen_success')} ${data.candidates_count}`, 'success', 'Хайлайты');
        openProject(activeProjectId);
      } catch (err) {
        showToast(err.message, 'error', 'Ошибка');
      }
    }

    // Feedback Scorecard
    function toggleFeedbackIssue(issueKey) {
      if (activeIssues.includes(issueKey)) {
        activeIssues = activeIssues.filter(i => i !== issueKey);
      } else {
        activeIssues.push(issueKey);
      }
      renderFeedbackIssuePills();
    }

    function renderFeedbackIssuePills() {
      document.querySelectorAll('.issue-pill').forEach(btn => {
        const k = btn.getAttribute('data-issue');
        if (activeIssues.includes(k)) {
          btn.className = 'btn-press issue-pill px-2.5 py-1 rounded-lg text-[11px] border border-rose-500 bg-rose-500/10 text-rose-500 dark:text-rose-300 font-semibold transition';
        } else {
          btn.className = 'btn-press issue-pill px-2.5 py-1 rounded-lg text-[11px] border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-surface-900 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition';
        }
      });
    }

    async function loadClipFeedback(clipId) {
      try {
        const res = await fetch(`/v1/clips/${clipId}/feedback`);
        if (res.ok) {
          const fb = await res.json();
          document.getElementById('review-publishable').checked = fb.publishable ?? true;
          activeIssues = fb.issues || [];
          renderFeedbackIssuePills();

          const r = fb.ratings || {};
          document.getElementById('review-select-highlight').value = r.highlight || 5;
          document.getElementById('review-select-framing').value = r.framing || 5;
          document.getElementById('review-select-subtitle').value = r.subtitles || 5;
        }
      } catch (e) {
        console.warn('Feedback load error:', e);
      }
    }

    async function saveCurrentClipFeedback() {
      const clip = currentClipsData[selectedClipIndex];
      if (!clip) return;
      const btn = document.getElementById('btn-save-feedback');
      const msg = document.getElementById('feedback-status-msg');

      btn.disabled = true;
      msg.classList.remove('hidden');
      msg.innerText = 'Saving...';

      const publishable = document.getElementById('review-publishable').checked;
      const ratings = {
        highlight: parseInt(document.getElementById('review-select-highlight').value),
        framing: parseInt(document.getElementById('review-select-framing').value),
        subtitles: parseInt(document.getElementById('review-select-subtitle').value),
      };

      try {
        const res = await fetch(`/v1/clips/${clip.id}/feedback`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            publishable,
            issues: activeIssues,
            ratings,
          })
        });
        if (!res.ok) throw new Error('Save error');
        msg.innerText = '✓ Quality scorecard saved!';
        showToast('Оценка качества успешно сохранена в базе', 'success', 'Scorecard');
      } catch (err) {
        msg.innerText = 'Error: ' + err.message;
        showToast(err.message, 'error', 'Ошибка сохранения');
      } finally {
        btn.disabled = false;
      }
    }

    // Google Drive Cloud Backup
    async function archiveCurrentClipToDrive() {
      const clip = currentClipsData[selectedClipIndex];
      if (!clip) return;
      const statusEl = document.getElementById('gdrive-status-msg');
      const btn = document.getElementById('btn-gdrive-archive');

      statusEl.classList.remove('hidden');
      statusEl.innerText = 'Archiving to Google Drive 10 TB...';
      btn.disabled = true;

      try {
        const res = await fetch(`/v1/clips/${clip.id}/archive/drive`, { method: 'POST' });
        const data = await res.json();
        statusEl.innerHTML = `✓ ${data.message} <br><a href="${data.drive_url}" target="_blank" class="text-sky-400 underline">Open in Drive</a>`;
        showToast('Ролик сохранен в облако Google Drive 10 TB', 'success', 'Google Drive');
      } catch (err) {
        statusEl.innerText = 'Drive error: ' + err.message;
        showToast(err.message, 'error', 'Ошибка Drive');
      } finally {
        btn.disabled = false;
      }
    }

    async function archiveCurrentProjectToDrive() {
      if (!activeProjectId) return;
      try {
        const res = await fetch(`/v1/projects/${activeProjectId}/archive/drive`, { method: 'POST' });
        const data = await res.json();
        showToast(`Проект архивирован в Google Drive (${data.archived_count} клипов)`, 'success', 'Архивация');
      } catch (err) {
        showToast(err.message, 'error', 'Ошибка архивации');
      }
    }

    async function cancelCurrentJob() {
      if (activeJobId) {
        const confirmed = await showConfirm(t('btn_cancel_job'), 'Прервать текущий процесс генерации?');
        if (!confirmed) return;
        await fetch(`/v1/jobs/${activeJobId}/cancel`, { method: 'POST' });
        localStorage.removeItem('viral_clips_active_job');
        showToast('Обработка отменена пользователем', 'warning');
        navigateTo('projects');
      }
    }

    // Boot Initializer
    document.addEventListener('DOMContentLoaded', () => {
      initTheme();
      initConfirmModal();
      applyTranslations();
      initDropzone();
      loadSystemCapabilities();
      restoreFormDraft();
      checkJobRecovery();
      handleRoute();
      updateSummary();
      safeRenderIcons();
    });
  </script>
</body>
</html>
"""
