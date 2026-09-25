# Product

## Primary JTBD
"У меня есть 30–180 минут исходного видео. Я хочу за несколько минут получить 3–10 вертикальных кандидатов, быстро проверить их и экспортировать."

## MVP persona
Один creator, один workspace, desktop browser.

## MVP features
- upload/local source;
- language auto/manual;
- transcript;
- candidate generation;
- top-N ranking;
- 9:16 framing;
- karaoke captions;
- preview;
- rerender with preset;
- export MP4;
- project history.

## Quality metrics
Главная:
`publishable_top5_rate`

Определение:
сколько из top-5 clips пользователь принимает без изменения start/end.

Дополнительные:
- face_visible_ratio;
- subtitle_alignment_error;
- render_time/source_minute;
- crash-free jobs;
- manual trim rate.

## Clip score
LLM возвращает dimensions:
- hook_strength;
- standalone_context;
- payoff;
- emotion;
- novelty;
- pace;
- shareability.

Итоговый score считается кодом по versioned weights.

## Competitive wedge candidates
Выбрать только один для первого launch:
- Russian-first;
- podcast active speaker;
- privacy/local-first;
- gaming + facecam/gameplay;
- API/batch agency workflow.
