# 英会話 Quiz

日本語話者向けの **リスニング・発音理解特化** 英会話学習ツール。単一HTMLで完結し、ダブルクリックで動く。
Kroniiリスニングクイズの派生として構築（設計書: `Ouro-Kronii/output/spec/generic_english_app_spec_v1.md`）。

## 特徴

- **3カテゴリ × 3モード = 9セッションタイプ**
  - 単語 / 慣用句 / フレーズ
  - 🔊 音声→意味 / 🎧 音声→スペル(表記) / 👁 表示→意味
- **発音強化**: IPA表示・音節&強勢表示・🐢ゆっくり・🔁3回連続・🪜ゆっくり→普通速
- **SRS (SM-2)**: 不正解は同日再出題、正解で間隔延長、習得判定
- **フィルタ**: CEFRレベル / タグ（場面・トピック）で絞り込み
- **設定**: TTS音声・速度・IPA/音節表示・進捗エクスポート/インポート/初期化
- **ダッシュボード**: カテゴリ別 / CEFR別 / タグ別の習得率、セッション履歴
- 配色は青系 (#4a90e2)、ダーク基調。スマホ対応。

## 使い方

```
python src/build_html.py
```
→ `output/app/index.html` をブラウザで開く。

ローカルプレビュー（任意）:
```
python -m http.server 8137 --directory output/app
```

## 構成

```
english-quiz/
├── data/
│   └── cefrj-vocabulary-profile-1.5.csv   # CEFR照合用 (Kroniiから流用)
├── src/
│   └── build_html.py                       # 単一HTMLジェネレータ
├── output/
│   ├── data/                               # 生成データ (pool_words/idioms/phrases.json)
│   └── app/
│       └── index.html                      # 完成アプリ
└── README.md
```

`build_html.py` は `output/data/` のプールを優先的に読み、無ければ `output/app/data/` を見る。

## データスキーマ

- **単語**: `id, category, lemma, surface, pos, cefr, ipa, syllables, stress_pos, meaning_ja, tags, example_en, example_ja, tts_text`
- **慣用句**: 単語に加え `phrase, literal_ja`（lemma/pos/surfaceの代わりにphrase）
- **フレーズ**: `phrase, situation, variations`（example系はnull可）

## 進捗状況

- [x] Phase 0: セットアップ
- [x] Phase 1: パイロット（全機能動作確認済み）
- [x] Phase 2: 単語 **3,205**（目標3,000達成。リーン補充＋除外リストで重複抑制）
- [x] Phase 3: 慣用句 **1,034**（目標800超過）
- [x] Phase 4: フレーズ **1,955**（目標1,500超過）
- [x] CEFR-Jざっくり照合（単語の96%収載・±1レベル内96%）
- [ ] Phase 5: サイズ最適化の検討（現状2.41MBの単一HTML）
- [ ] Phase 6: 実機・初心者目線の最終確認
- [ ] ホスティング設定

**総計 6,194件** / 全モード・SRS・誤答生成 検証済み。

### データ生成の運用メモ
1. `output/data/batches/` に各バッチJSONを置く（LLM生成）
2. `python src/aggregate_pools.py` で集約・検証・重複排除 → `pool_*.json`
3. `python src/build_html.py` で `index.html` 再生成

## 既知の制約

- TTSはブラウザのWeb Speech API依存。iOS Safariはユーザータップ起因なら概ね動作。
- IPAはLLM生成のため誤差あり。TTS音声を主、IPAは補助。
- localStorageキー: 進捗 `english.quiz.progress.v1` / 設定 `english.quiz.settings.v1`
