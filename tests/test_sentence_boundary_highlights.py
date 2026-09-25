import pytest
from pathlib import Path
from viral_clips.core.highlight_engine import (
    reconstruct_sentences,
    generate_candidate_windows,
    detect_highlights,
)

def test_reconstruct_sentences_from_transcript():
    sample_transcript = {
        "words": [
            {"word": "Привет,", "start_ms": 0, "end_ms": 500},
            {"word": "мир!", "start_ms": 510, "end_ms": 1000},
            {"word": "Это", "start_ms": 1100, "end_ms": 1400},
            {"word": "второе", "start_ms": 1410, "end_ms": 1800},
            {"word": "предложение.", "start_ms": 1810, "end_ms": 2500},
        ],
        "segments": []
    }
    sents = reconstruct_sentences(sample_transcript)
    assert len(sents) == 2
    assert sents[0]["text"] == "Привет, мир!"
    assert sents[0]["start_ms"] == 0
    assert sents[0]["end_ms"] == 1000
    assert sents[1]["text"] == "Это второе предложение."
    assert sents[1]["start_ms"] == 1100
    assert sents[1]["end_ms"] == 2500


def test_candidate_windows_strict_sentence_boundaries():
    sample_transcript = {
        "words": [
            {"word": "Секрет", "start_ms": 0, "end_ms": 500},
            {"word": "вирусных", "start_ms": 510, "end_ms": 1000},
            {"word": "видео.", "start_ms": 1010, "end_ms": 1500},
            {"word": "И", "start_ms": 1600, "end_ms": 1800},
            {"word": "потом", "start_ms": 1810, "end_ms": 2200},
            {"word": "случилась", "start_ms": 2210, "end_ms": 2700},
            {"word": "ошибка,", "start_ms": 2710, "end_ms": 3200},
            {"word": "которая", "start_ms": 3210, "end_ms": 3700},
            {"word": "все", "start_ms": 3710, "end_ms": 4000},
            {"word": "изменила.", "start_ms": 4010, "end_ms": 4500},
            {"word": "В", "start_ms": 4600, "end_ms": 4800},
            {"word": "итоге", "start_ms": 4810, "end_ms": 5200},
            {"word": "получился", "start_ms": 5210, "end_ms": 5800},
            {"word": "крутой", "start_ms": 5810, "end_ms": 6400},
            {"word": "результат!", "start_ms": 6410, "end_ms": 7000},
        ],
        "segments": []
    }

    windows = generate_candidate_windows(
        sample_transcript,
        min_duration_s=2.0,
        max_duration_s=10.0,
        complete_sentences=True,
    )

    assert len(windows) > 0
    for w in windows:
        # Every window must start with an uppercase letter
        assert w["text"][0].isupper()
        # Every window must end with terminal punctuation
        assert w["text"][-1] in (".", "!", "?")
        # No window starts with bad conjunctions
        first_word = w["text"].split()[0].lower().strip(",.-")
        assert first_word not in {"и", "а", "но", "так", "что"}
