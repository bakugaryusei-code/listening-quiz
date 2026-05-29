"""
バッチ生成された JSON を集約・検証・重複排除して
output/data/pool_words.json / pool_idioms.json / pool_phrases.json を作る。

使い方:
  python src/aggregate_pools.py
"""
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BATCH_DIR = PROJECT_ROOT / "output" / "data" / "batches"
OUT_DIR = PROJECT_ROOT / "output" / "data"

VALID_POS = {"NOUN", "VERB", "ADJ", "ADV", "PREP", "CONJ", "PRON"}
VALID_CEFR = {"A1", "A2", "B1", "B2"}


def load_array(path: Path):
    """ファイルからJSON配列を取り出す。前後に説明文が混ざっていても救出。"""
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # {"items":[...]} のような包みを救出
            for v in data.values():
                if isinstance(v, list):
                    return v
            return [data]
    except json.JSONDecodeError:
        pass
    # 最初の [ から最後の ] までを抜き出して再挑戦
    s, e = text.find("["), text.rfind("]")
    if s != -1 and e != -1 and e > s:
        try:
            return json.loads(text[s:e + 1])
        except json.JSONDecodeError:
            pass
    return None


def norm_phrase(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", str(s).lower()).strip()


def slug(s: str, prefix: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_")[:40]
    return f"{prefix}_{base}"


def valid_word(x):
    if not isinstance(x, dict):
        return None
    lemma = x.get("lemma") or x.get("surface")
    pos = x.get("pos")
    if not lemma or not x.get("meaning_ja") or pos not in VALID_POS:
        return None
    if x.get("cefr") not in VALID_CEFR:
        x["cefr"] = "A2"
    surface = x.get("surface") or lemma
    return {
        "id": x.get("id") or slug(f"{lemma}_{pos}", "w"),
        "category": "word",
        "lemma": lemma, "surface": surface, "pos": pos, "cefr": x["cefr"],
        "ipa": x.get("ipa"), "syllables": x.get("syllables"),
        "stress_pos": x.get("stress_pos", 0),
        "meaning_ja": x.get("meaning_ja"),
        "tags": x.get("tags") or [],
        "example_en": x.get("example_en"), "example_ja": x.get("example_ja"),
        "tts_text": x.get("tts_text") or surface,
    }


def valid_idiom(x):
    if not isinstance(x, dict):
        return None
    phrase = x.get("phrase")
    if not phrase or not x.get("meaning_ja"):
        return None
    if x.get("cefr") not in VALID_CEFR:
        x["cefr"] = "B1"
    return {
        "id": x.get("id") or slug(phrase, "i"),
        "category": "idiom",
        "phrase": phrase, "ipa": x.get("ipa"), "cefr": x["cefr"],
        "meaning_ja": x.get("meaning_ja"), "literal_ja": x.get("literal_ja"),
        "tags": x.get("tags") or [],
        "example_en": x.get("example_en"), "example_ja": x.get("example_ja"),
        "tts_text": x.get("tts_text") or phrase,
    }


def valid_phrase(x):
    if not isinstance(x, dict):
        return None
    phrase = x.get("phrase")
    if not phrase or not x.get("meaning_ja"):
        return None
    if x.get("cefr") not in VALID_CEFR:
        x["cefr"] = "A2"
    return {
        "id": x.get("id") or slug(phrase, "p"),
        "category": "phrase",
        "phrase": phrase, "ipa": x.get("ipa"), "cefr": x["cefr"],
        "meaning_ja": x.get("meaning_ja"),
        "tags": x.get("tags") or [],
        "situation": x.get("situation"),
        "variations": x.get("variations") or [],
        "example_en": x.get("example_en"), "example_ja": x.get("example_ja"),
        "tts_text": x.get("tts_text") or phrase,
    }


CATEGORIES = {
    "w": ("word", valid_word, lambda x: f"{x['lemma'].lower()}|{x['pos']}", "pool_words.json"),
    "i": ("idiom", valid_idiom, lambda x: norm_phrase(x["phrase"]), "pool_idioms.json"),
    "p": ("phrase", valid_phrase, lambda x: norm_phrase(x["phrase"]), "pool_phrases.json"),
}


def main():
    buckets = {"w": [], "i": [], "p": []}
    files = sorted(BATCH_DIR.glob("*.json"))
    bad_files = []
    for path in files:
        prefix = path.name[0]
        if prefix not in buckets:
            continue
        arr = load_array(path)
        if arr is None:
            bad_files.append(path.name)
            continue
        buckets[prefix].append((path.name, arr))

    print(f"読み込みバッチ: {len(files)}ファイル / 解析失敗: {bad_files or 'なし'}")

    summary = []
    for prefix, (catname, validator, keyfn, outname) in CATEGORIES.items():
        seen_key, seen_id = set(), set()
        out, raw, dropped, dup = [], 0, 0, 0
        for fname, arr in buckets[prefix]:
            for item in arr:
                raw += 1
                v = validator(item)
                if v is None:
                    dropped += 1
                    continue
                k = keyfn(v)
                if k in seen_key:
                    dup += 1
                    continue
                seen_key.add(k)
                # id一意化
                base_id = v["id"]
                if base_id in seen_id:
                    n = 2
                    while f"{base_id}_{n}" in seen_id:
                        n += 1
                    v["id"] = f"{base_id}_{n}"
                seen_id.add(v["id"])
                out.append(v)
        (OUT_DIR / outname).write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        summary.append((catname, len(out), raw, dropped, dup))
        print(f"[{catname:7}] 採用 {len(out):5} / 生 {raw:5} / 除外 {dropped:4} / 重複 {dup:5}  -> {outname}")

    total = sum(s[1] for s in summary)
    print(f"\n合計採用: {total} 件")


if __name__ == "__main__":
    main()
