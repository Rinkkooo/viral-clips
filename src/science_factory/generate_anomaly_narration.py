import asyncio
import os
import sys
import json
import edge_tts

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

OUTPUT_DIR = r"C:\Users\user\Desktop\viral_clips\src\science_factory\assets\anomaly_narration"
os.makedirs(OUTPUT_DIR, exist_ok=True)

CHAPTERS = [
    {
        "id": "intro",
        "chapter_num": 0,
        "title": "ХРУПКОСТЬ СОЗНАНИЯ",
        "subtitle": "Нейробиологическая иллюзия реальности",
        "icd_code": "SYSTEM: CNS ARCHITECTURE",
        "rarity": "Универсально",
        "mechanism": "Крах баланса тормозных и возбуждающих синапсов",
        "text": (
            "Ваш мозг — это биокомпьютер, который ежесекундно создает ощущение реальности. "
            "Но достаточно крошечной ошибки в синапсе, повреждения мозолистого тела или сбоя одного нейромедиатора, "
            "и привычный мир превращается в леденящий кошмар. "
            "Вот пять самых пугающих аномалий мозга и тела, от которых ученые до сих пор в шоке."
        ),
        "broll_video": r"C:\Users\user\Desktop\viral_clips\src\science_factory\video_broll\anomalies\intro_brain.mp4",
        "vfx_type": "fmri",
        "vfx_target": "amygdala"
    },
    {
        "id": "ch1_paralysis",
        "chapter_num": 1,
        "title": "СОННЫЙ ПАРАЛИЧ",
        "subtitle": "Атония быстрой фазы сна",
        "icd_code": "ICD-11: 7A40 // G47.54",
        "rarity": "8% населения планеты",
        "mechanism": "Рассинхронизация таламуса и мотонейронов спинного мозга",
        "text": (
            "Вы просыпаетесь посреди ночи. Сознание кристально чистое, но тело парализовано. "
            "Вы не можете пошевелить даже пальцем или закричать. "
            "А в темном углу спальни сгущается жуткий силуэт, медленно приближаясь к вашей кровати. "
            "Это сонный паралич. В фазе быстрого сна мозг блокирует мышцы с помощью ГАМК и глицина, чтобы мы не двигались во сне. "
            "Но если кора просыпается раньше спинного мозга, сновидения проецируются прямо в физическую комнату. "
            "Пульс взлетает до ста сорока ударов, а грудь сдавливает удушье."
        ),
        "broll_video": r"C:\Users\user\Desktop\viral_clips\src\science_factory\video_broll\anomalies\ch1_paralysis.mp4",
        "vfx_type": "ecg",
        "vfx_start_bpm": 75,
        "vfx_end_bpm": 142
    },
    {
        "id": "ch2_alien_hand",
        "chapter_num": 2,
        "title": "СИНДРОМ ЧУЖОЙ РУКИ",
        "subtitle": "Автономный нейромоторный конфликт",
        "icd_code": "ICD-11: 8E7Y // DISCONNECT",
        "rarity": "Крайне редко (< 1:100,000)",
        "mechanism": "Разрыв мозолистого тела и премоторной коры",
        "text": (
            "Представьте, что ваша собственная рука внезапно обретает чужую волю. "
            "Она расстегивает одежду, вырывает руль на скорости или даже пытается задушить вас во сне. "
            "Человек в ужасе вынужден физически бороться с собственной конечностью. "
            "Причина — повреждение мозолистого тела, магистрального пучка из двухсот миллионов волокон между полушариями. "
            "Без связи правое полушарие начинает запускать сложные целенаправленные движения, "
            "полностью отрезанные от осознанного контроля левого полушария."
        ),
        "broll_video": r"C:\Users\user\Desktop\viral_clips\src\science_factory\video_broll\anomalies\ch2_alien_hand.mp4",
        "vfx_type": "fmri",
        "vfx_target": "callosum"
    },
    {
        "id": "ch3_exploding_head",
        "chapter_num": 3,
        "title": "СИНДРОМ ВЗРЫВАЮЩЕЙСЯ ГОЛОВЫ",
        "subtitle": "Пароксизмальный сенсорный шторм",
        "icd_code": "ICD-11: 7A87 // PARASOMNIA",
        "rarity": "До 10% людей хотя бы раз в жизни",
        "mechanism": "Синхронный залповый разряд ретикулярной формации",
        "text": (
            "Вы почти уснули. Дыхание замедляется. "
            "И внезапно прямо внутри вашего черепа с оглушительным грохотом детонирует бомба или раздается выстрел, "
            "сопровождаемый слепящей вспышкой света. "
            "Вы вскакиваете в ледяном поту, уверенные, что взорвался мозг. "
            "Но физической травмы нет. Это сенсорный сбой в ретикулярной формации ствола мозга. "
            "Вместо плавного отключения слуховых и зрительных центров происходит мгновенный гигантский синхронный разряд миллионов нейронов."
        ),
        "broll_video": r"C:\Users\user\Desktop\viral_clips\src\science_factory\video_broll\anomalies\ch3_neurons_firing.mp4",
        "vfx_type": "eeg",
        "vfx_spike": True
    },
    {
        "id": "ch4_fatal_insomnia",
        "chapter_num": 4,
        "title": "ФАТАЛЬНАЯ БЕССОННИЦА",
        "subtitle": "Необратимое разрушение таламуса",
        "icd_code": "ICD-11: 8E01 // PRION DISEASE",
        "rarity": "Смертельное генетическое (1 на 1 000 000)",
        "mechanism": "Прионная мутация D178N в гене PRNP",
        "text": (
            "Что, если вы ляжете в постель и больше никогда в жизни не сможете уснуть? "
            "Фатальная семейная бессонница — неизлечимый генетический кошмар. "
            "Неправильно свернутые прионные белки начинают уничтожать таламус — главный коммутатор сна в мозгу. "
            "Таламус буквально превращается в пористую губку. "
            "Снотворные препараты и даже искусственная кома бессильны. "
            "Начинаются бесконечные галлюцинации, потеря веса, безумие и неминуемая гибель от тотального истощения нервной системы."
        ),
        "broll_video": r"C:\Users\user\Desktop\viral_clips\src\science_factory\video_broll\anomalies\ch4_eye_pupil.mp4",
        "vfx_type": "fmri",
        "vfx_target": "thalamus"
    },
    {
        "id": "ch5_cotard",
        "chapter_num": 5,
        "title": "СИНДРОМ КОТАРА: ЖИВОЙ МЕРТВЕЦ",
        "subtitle": "Тотальный бред отрицания существования",
        "icd_code": "ICD-11: 6A20 // COTARD DELUSION",
        "rarity": "Ультра-редкий нейропсихиатрический сбой",
        "mechanism": "Обрыв связей веретеновидной извилины и лимбической системы",
        "text": (
            "Самая жуткая иллюзия в психиатрии. "
            "Пациенты с синдромом Котара искренне убеждены, что они уже мертвы. "
            "Они требуют отвезти их в морг, утверждая, что их органы сгнили, в венах нет крови, а сердце остановилось. "
            "Они отказываются от еды со словами: мертвецам не нужна пища. "
            "Это катастрофический разрыв между восприятием сенсорных сигналов и миндалевидным телом. "
            "Мозг больше не получает эмоционального подтверждения своего существования и делает леденящий вывод: раз я ничего не чувствую, значит, меня больше нет."
        ),
        "broll_video": r"C:\Users\user\Desktop\viral_clips\src\science_factory\video_broll\anomalies\ch5_hospital_corridor.mp4",
        "vfx_type": "ecg",
        "vfx_start_bpm": 60,
        "vfx_end_bpm": 0,
        "vfx_flatline_rel": 0.65
    },
    {
        "id": "outro",
        "chapter_num": 6,
        "title": "ГРАНЬ РЕАЛЬНОСТИ",
        "subtitle": "Анатомическая хрупкость разума",
        "icd_code": "CONCLUSION: HOMEOSTASIS",
        "rarity": "Норма",
        "mechanism": "Хрупкое нейрохимическое равновесие",
        "text": (
            "Каждую секунду ваш мозг фильтрует триллионы сигналов, оберегая ваше сознание от бездны. "
            "Но грань между порядком и распадом реальности невероятно тонка. "
            "Какая из этих пяти аномалий потрясла вас больше всего? "
            "Напишите в комментариях и берегите свой мозг."
        ),
        "broll_video": r"C:\Users\user\Desktop\viral_clips\src\science_factory\video_broll\anomalies\intro_brain.mp4",
        "vfx_type": "eeg",
        "vfx_spike": False
    }
]

async def generate_chapter_audio(ch):
    voice = "ru-RU-DmitryNeural"
    out_mp3 = os.path.join(OUTPUT_DIR, f"{ch['id']}.mp3")
    
    print(f"[+] Synthesizing {ch['id']}...", flush=True)
    words = []
    total_duration = 0.0
    
    for attempt in range(3):
        try:
            communicate = edge_tts.Communicate(
                text=ch["text"],
                voice=voice,
                rate="+2%",
                boundary="WordBoundary"
            )
            raw_audio = bytearray()
            words = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    raw_audio.extend(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    start_s = chunk["offset"] / 10_000_000.0
                    dur_s = chunk["duration"] / 10_000_000.0
                    end_s = start_s + dur_s
                    w = chunk["text"].strip()
                    if w:
                        words.append({
                            "word": w,
                            "start": round(start_s, 3),
                            "end": round(end_s, 3),
                            "duration": round(dur_s, 3)
                        })
            if len(raw_audio) > 0:
                with open(out_mp3, "wb") as f_out:
                    f_out.write(raw_audio)
                total_duration = words[-1]["end"] + 0.6 if words else 30.0
                break
        except Exception as e:
            print(f"  [!] Attempt {attempt+1} error: {e}", flush=True)
            await asyncio.sleep(1.0)
            
    ch["duration"] = round(total_duration, 2)
    ch["audio_path"] = out_mp3
    ch["words"] = words
    print(f"[OK] {ch['id']} duration: {total_duration:.2f}s ({len(words)} words)", flush=True)
    return ch

async def main():
    results = []
    total_dur = 0.0
    for ch in CHAPTERS:
        res = await generate_chapter_audio(ch)
        results.append(res)
        total_dur += res["duration"]
        
    master_manifest = os.path.join(OUTPUT_DIR, "anomaly_chapters_manifest.json")
    with open(master_manifest, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"\n[DONE] All {len(CHAPTERS)} chapters synthesized!", flush=True)
    print(f"Total documentary runtime: {total_dur:.1f}s ({total_dur/60.0:.2f} minutes)", flush=True)
    print(f"Manifest saved to: {master_manifest}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
