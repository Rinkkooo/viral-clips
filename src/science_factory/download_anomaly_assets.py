import os
import sys
import yt_dlp

OUTPUT_DIR = r"C:\Users\user\Desktop\viral_clips\src\science_factory\video_broll\anomalies"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Selected high-quality royalty-free video clips for each chapter
CLIPS = [
    {
        "id": "intro_brain",
        "query": "ytsearch1:3D Human Brain Animation Free HD Footage Royalty Free No Copyright 1080p JXmd0DBZIX8",
        "filename": "intro_brain.mp4"
    },
    {
        "id": "ch1_paralysis",
        "query": "ytsearch1:Nightmare Night Mare Stock Footage qrLXbKwv0_8",
        "filename": "ch1_paralysis.mp4"
    },
    {
        "id": "ch2_alien_hand",
        "query": "ytsearch1:Female Fingers Moving Stock Video Io4XT_FQkak",
        "filename": "ch2_alien_hand.mp4"
    },
    {
        "id": "ch3_exploding_head",
        "query": "ytsearch1:brain neural network and neurons synapse firing 3d render LsehL-tvuA4",
        "filename": "ch3_neurons_firing.mp4"
    },
    {
        "id": "ch4_fatal_insomnia",
        "query": "ytsearch1:stock footage extreme close up human eye iris contracting FMF6MLuu1MQ",
        "filename": "ch4_eye_pupil.mp4"
    },
    {
        "id": "ch5_cotard",
        "query": "ytsearch1:Long empty light corridor in hospital 1Dm7Q6LIIlg",
        "filename": "ch5_hospital_corridor.mp4"
    }
]

def download_clips():
    print(f"Starting download of {len(CLIPS)} anomaly clips to {OUTPUT_DIR}...")
    for item in CLIPS:
        target_path = os.path.join(OUTPUT_DIR, item["filename"])
        if os.path.exists(target_path) and os.path.getsize(target_path) > 100000:
            print(f"[-] Already exists: {item['filename']} ({os.path.getsize(target_path)} bytes)")
            continue
        
        print(f"[+] Downloading: {item['id']} ({item['filename']})...")
        ydl_opts = {
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
            'outtmpl': target_path,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([item['query']])
            if os.path.exists(target_path):
                print(f"[OK] Downloaded {item['filename']} -> {os.path.getsize(target_path)} bytes")
            else:
                print(f"[WARN] File not created at {target_path}")
        except Exception as e:
            print(f"[ERROR] Failed downloading {item['id']}: {e}")

if __name__ == "__main__":
    download_clips()
