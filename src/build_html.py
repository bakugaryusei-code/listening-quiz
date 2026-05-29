"""
汎用英会話学習ツール: 単一HTMLジェネレータ。
pool_words.json / pool_idioms.json / pool_phrases.json を埋め込んで
output/app/index.html を生成する。

使い方:
  python src/build_html.py
  → output/app/index.html をダブルクリックでブラウザで開く

Kronii版 build_html.py からの派生。SM-2 / TTS / 4択UI / ダッシュボード /
CSSを流用し、新スキーマ・発音強化機能・フィルタ・設定画面を追加。
"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "output" / "data"
APP_DATA_DIR = PROJECT_ROOT / "output" / "app" / "data"
OUT_HTML = PROJECT_ROOT / "output" / "app" / "index.html"

# テーマ設定（オープン項目16: アプリ名=Listening Quiz / 配色=緑系 #52b788）
APP_NAME = "Listening Quiz"

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__APP_NAME__</title>
<style>
  :root {
    --bg: #161b22;
    --panel: #1e2530;
    --panel2: #283142;
    --border: #364153;
    --text: #e6edf3;
    --muted: #8b98ad;
    --accent: #52b788;
    --accent-soft: #234a3a;
    --accent-text: #08130d;
    --good: #74d3a0;
    --good-bg: #15362a;
    --good-text: #c2f3d7;
    --bad: #e5615e;
    --bad-bg: #3a1e1e;
    --bad-text: #f0c8c8;
    --warn: #e6b84c;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Yu Gothic', 'Hiragino Sans', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 12px;
  }
  #app { width: 100%; max-width: 620px; margin-top: 12px; }
  h1 { color: var(--accent); font-size: 1.7em; text-align: center; margin-bottom: 6px; }
  .subtitle { text-align: center; color: var(--muted); margin-bottom: 22px; font-size: 0.9em; }
  .card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 14px;
  }
  .mode-btn {
    width: 100%;
    padding: 16px;
    margin-bottom: 10px;
    background: var(--panel2);
    color: var(--text);
    border: 2px solid transparent;
    border-radius: 10px;
    font-size: 1.05em;
    cursor: pointer;
    transition: all 0.15s;
    text-align: left;
    font-family: inherit;
  }
  .mode-btn:hover { border-color: var(--accent); background: var(--accent-soft); }
  .mode-btn .mode-title { font-weight: bold; display: block; margin-bottom: 4px; }
  .mode-btn .mode-desc { font-size: 0.85em; color: var(--muted); }

  .stats {
    display: flex; justify-content: space-around;
    padding: 14px; background: var(--panel); border-radius: 10px; margin-top: 16px;
  }
  .stat-item { text-align: center; }
  .stat-value { font-size: 1.4em; font-weight: bold; color: var(--accent); }
  .stat-label { font-size: 0.8em; color: var(--muted); }

  .question-header {
    display: flex; justify-content: space-between;
    color: var(--muted); font-size: 0.85em; margin-bottom: 10px;
  }
  .question-main { text-align: center; margin: 12px 0 8px; }
  .word-display { font-size: 1.9em; color: var(--text); margin: 10px 0 4px; font-weight: 300; letter-spacing: 0.02em; }
  .phrase-display { font-size: 1.45em; color: var(--text); margin: 10px 0 4px; font-weight: 400; }
  .sentence-display { font-size: 1.15em; color: var(--text); margin: 10px 0 4px; line-height: 1.5; padding: 0 4px; }

  .pron-line { font-size: 0.95em; color: var(--accent); margin: 4px 0; font-family: 'Segoe UI', system-ui, sans-serif; }
  .syll-line { font-size: 0.9em; color: var(--warn); margin: 2px 0 4px; letter-spacing: 0.03em; }

  .category-tabs { display: flex; gap: 6px; margin-bottom: 14px; }
  .category-tab {
    flex: 1; padding: 11px 8px; background: var(--panel);
    color: var(--muted); border: 2px solid var(--border);
    border-radius: 8px; font-size: 0.92em; font-weight: bold;
    cursor: pointer; font-family: inherit; transition: all 0.15s;
  }
  .category-tab:hover { border-color: var(--accent); }
  .category-tab.active { background: var(--accent-soft); color: var(--accent); border-color: var(--accent); }

  .word-meta { font-size: 0.8em; color: var(--muted); margin-bottom: 8px; }

  .play-btn {
    background: var(--accent); color: var(--accent-text); border: none;
    padding: 11px 22px; border-radius: 50px; font-size: 1.0em; cursor: pointer;
    margin: 6px 4px; display: inline-flex; align-items: center; gap: 8px;
    font-weight: bold; box-shadow: 0 4px 16px rgba(74,144,226,0.3); font-family: inherit;
  }
  .play-btn:hover { background: #65c997; }
  .play-btn:active { transform: scale(0.97); }
  .play-btn.small { padding: 8px 14px; font-size: 0.88em; box-shadow: none; }
  .play-btn.ghost { background: var(--panel2); color: var(--text); box-shadow: none; border: 1px solid var(--border); }
  .play-btn.ghost.on { border-color: var(--accent); color: var(--accent); }

  .pron-controls { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; margin: 12px 0 6px; }
  .toggle-row { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; margin: 4px 0; }

  .choices { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 16px; }
  .choice {
    padding: 12px 14px; background: var(--panel2); border: 2px solid var(--border);
    border-radius: 10px; cursor: pointer; transition: all 0.15s; font-size: 0.95em;
    text-align: left; color: var(--text); font-family: inherit; width: 100%;
    min-height: 56px; display: flex; align-items: center;
  }
  .choices-stacked { grid-template-columns: 1fr !important; }
  .choices-stacked .choice { min-height: 44px; font-size: 0.9em; padding: 11px 13px; }
  @media (max-width: 480px) { .choices { grid-template-columns: 1fr; } }
  .choice:hover:not(.disabled) { border-color: var(--accent); background: var(--accent-soft); }
  .choice.disabled { cursor: default; opacity: 0.75; }
  .choice.correct { border-color: var(--good); background: var(--good-bg); color: var(--good-text); }
  .choice.wrong { border-color: var(--bad); background: var(--bad-bg); color: var(--bad-text); }
  .choice-key {
    display: inline-block; width: 22px; height: 22px; background: var(--accent-soft);
    color: var(--accent); border-radius: 50%; text-align: center; line-height: 22px;
    font-size: 0.85em; margin-right: 12px; font-weight: bold; flex-shrink: 0;
  }
  .choice.correct .choice-key { background: var(--good); color: #0d2a1a; }
  .choice.wrong .choice-key { background: var(--bad); color: #2a0d0d; }

  .feedback { margin-top: 12px; padding: 10px 14px; border-radius: 10px; background: var(--panel2); font-size: 0.95em; }
  .feedback.correct { background: var(--good-bg); color: var(--good-text); }
  .feedback.wrong { background: var(--bad-bg); color: var(--bad-text); }
  .feedback strong { color: #fff; }
  .feedback .example { margin-top: 8px; font-size: 0.85em; color: var(--muted); font-style: italic; }
  .feedback .example-ja { font-style: normal; color: var(--muted); }

  .next-btn {
    width: 100%; padding: 12px; background: var(--accent); color: var(--accent-text);
    border: none; border-radius: 10px; font-size: 1em; font-weight: bold;
    cursor: pointer; margin-top: 10px; font-family: inherit;
  }
  .next-btn:hover { background: #65c997; }
  .next-btn:active { transform: scale(0.99); }

  .progress-bar { height: 4px; background: var(--border); border-radius: 2px; overflow: hidden; margin-bottom: 14px; }
  .progress-fill { height: 100%; background: var(--accent); transition: width 0.3s; }

  .result-score { font-size: 3em; text-align: center; color: var(--accent); margin: 20px 0; }
  .result-message { text-align: center; color: var(--muted); margin-bottom: 24px; }

  .small-text { font-size: 0.8em; color: var(--muted); }
  .center { text-align: center; }

  .srs-badge { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
  .badge { display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 0.72em; font-weight: bold; }
  .badge-due { background: var(--bad); color: #fff; }
  .badge-fresh { background: var(--accent-soft); color: var(--accent); }
  .badge-learning { background: var(--warn); color: #3a2e08; }
  .badge-mastered { background: var(--good); color: #0d2a1a; }

  table { border-collapse: collapse; }
  table th, table td { padding: 8px 4px; border-bottom: 1px solid var(--border); }

  /* フィルタパネル */
  .filter-summary {
    display: flex; justify-content: space-between; align-items: center;
    cursor: pointer; color: var(--accent); font-size: 0.9em; font-weight: bold;
  }
  .chip {
    display: inline-block; padding: 5px 11px; margin: 3px; border-radius: 16px;
    background: var(--panel2); color: var(--muted); border: 1px solid var(--border);
    font-size: 0.82em; cursor: pointer; font-family: inherit; transition: all 0.12s;
  }
  .chip:hover { border-color: var(--accent); }
  .chip.on { background: var(--accent-soft); color: var(--accent); border-color: var(--accent); }
  .filter-group-label { font-size: 0.78em; color: var(--muted); margin: 8px 0 4px; }

  /* 設定 */
  .setting-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--border); }
  .setting-row:last-child { border-bottom: none; }
  .setting-label { font-size: 0.95em; }
  .setting-desc { font-size: 0.78em; color: var(--muted); margin-top: 2px; }
  .switch { position: relative; width: 46px; height: 26px; flex-shrink: 0; }
  .switch input { display: none; }
  .slider { position: absolute; inset: 0; background: var(--border); border-radius: 26px; cursor: pointer; transition: 0.2s; }
  .slider:before { content: ''; position: absolute; width: 20px; height: 20px; left: 3px; top: 3px; background: #fff; border-radius: 50%; transition: 0.2s; }
  .switch input:checked + .slider { background: var(--accent); }
  .switch input:checked + .slider:before { transform: translateX(20px); }
  select.speed-select {
    background: var(--panel2); color: var(--text); border: 1px solid var(--border);
    padding: 7px 10px; border-radius: 6px; font-family: inherit; font-size: 0.9em;
  }

  @media (max-width: 768px) {
    #app { max-width: 100%; margin-top: 6px; }
    body { padding: 8px; }
    h1 { font-size: 1.4em; }
    .subtitle { font-size: 0.85em; margin-bottom: 16px; }
    .card { padding: 14px 16px; margin-bottom: 10px; }
    .word-display { font-size: 1.7em; }
    .phrase-display { font-size: 1.3em; }
    .sentence-display { font-size: 1.05em; }
    .mode-btn { padding: 14px; }
  }
  @media (max-width: 480px) {
    body { padding: 6px; }
    h1 { font-size: 1.22em; margin-bottom: 2px; }
    .subtitle { font-size: 0.78em; margin-bottom: 12px; }
    .card { padding: 12px 14px; border-radius: 12px; }
    .word-display { font-size: 1.5em; }
    .phrase-display { font-size: 1.18em; }
    .sentence-display { font-size: 1.0em; }
    .choices { grid-template-columns: 1fr; gap: 6px; }
    .choice { min-height: 48px; padding: 11px 12px; font-size: 0.92em; }
    .choices-stacked .choice { min-height: 40px; font-size: 0.86em; padding: 9px 11px; }
    .mode-btn { padding: 12px; }
    .next-btn { padding: 11px; font-size: 0.95em; }
    .stats .stat-value { font-size: 1.2em; }
    .badge { font-size: 0.68em; padding: 2px 6px; }
    .play-btn { padding: 10px 16px; font-size: 0.92em; }
    .play-btn.small { padding: 7px 12px; font-size: 0.82em; }
  }
</style>
</head>
<body>
<div id="app"></div>

<script type="application/json" id="words-pool">
__WORDS_POOL_JSON__
</script>
<script type="application/json" id="idioms-pool">
__IDIOMS_POOL_JSON__
</script>
<script type="application/json" id="phrases-pool">
__PHRASES_POOL_JSON__
</script>

<script>
'use strict';

// ============================================================
// データロード
// ============================================================
const WORDS_POOL   = JSON.parse(document.getElementById('words-pool').textContent);
const IDIOMS_POOL  = JSON.parse(document.getElementById('idioms-pool').textContent);
const PHRASES_POOL = JSON.parse(document.getElementById('phrases-pool').textContent);
WORDS_POOL.forEach(x => x.category = 'word');
IDIOMS_POOL.forEach(x => x.category = 'idiom');
PHRASES_POOL.forEach(x => x.category = 'phrase');

const POS_LABELS = { NOUN: '名詞', VERB: '動詞', ADJ: '形容詞', ADV: '副詞', PREP: '前置詞', CONJ: '接続詞', PRON: '代名詞' };

function basePool(cat) {
  if (cat === 'word')   return WORDS_POOL.filter(x => x.meaning_ja);
  if (cat === 'idiom')  return IDIOMS_POOL.filter(x => x.meaning_ja);
  if (cat === 'phrase') return PHRASES_POOL.filter(x => x.meaning_ja);
  return [];
}

// フィルタ適用後のプール
function getPool(cat) {
  let pool = basePool(cat);
  const f = state.filters;
  if (f.cefr.size > 0) pool = pool.filter(x => f.cefr.has(x.cefr));
  if (f.tags.size > 0) pool = pool.filter(x => (x.tags || []).some(t => f.tags.has(t)));
  return pool;
}

function getSurface(item) {
  if (item.category === 'word') return item.surface || item.lemma;
  return item.phrase;
}
function getTtsText(item) { return item.tts_text || getSurface(item); }
function getItemKey(item) {
  if (item.category === 'word') return item.lemma + '|' + item.pos;
  return item.phrase;
}
function wordCountOf(item) {
  return getSurface(item).trim().split(/\s+/).length;
}

// ============================================================
// 設定 (localStorage)
// ============================================================
const SETTINGS_KEY = 'english.quiz.settings.v1';
function defaultSettings() {
  return { showIpa: true, showSyllables: true, defaultRate: 0.9, voiceName: null, sound: true };
}
function loadSettings() {
  const raw = localStorage.getItem(SETTINGS_KEY);
  if (raw) { try { return Object.assign(defaultSettings(), JSON.parse(raw)); } catch (e) {} }
  return defaultSettings();
}
function saveSettings(s) { localStorage.setItem(SETTINGS_KEY, JSON.stringify(s)); }
let settings = loadSettings();

// ============================================================
// 進捗管理 (localStorage) + SRS
// ============================================================
const STORAGE_KEY = 'english.quiz.progress.v1';

function defaultProgress() {
  return { version: 1, sessions: 0, totalAnswered: 0, totalCorrect: 0, srs: {}, history: [] };
}
function loadProgress() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (raw) { try { return Object.assign(defaultProgress(), JSON.parse(raw)); } catch (e) {} }
  return defaultProgress();
}
function saveProgress(p) { localStorage.setItem(STORAGE_KEY, JSON.stringify(p)); }

function today() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}
function dateAfter(days) {
  const d = new Date(); d.setDate(d.getDate() + days);
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}

function getSrs(progress, itemId, mode) { return progress.srs[`${itemId}::${mode}`] || null; }
function newSrsState() {
  return { ef: 2.5, interval_days: 0, repetitions: 0, due_date: null, last_review: null, lapses: 0 };
}
// SM-2 (失敗時は同日再出題). 4択: 正解=4 / 不正解=2
function sm2Update(srs, quality) {
  const s = Object.assign({}, srs);
  if (quality < 3) {
    s.repetitions = 0; s.interval_days = 0; s.lapses = (s.lapses || 0) + 1;
  } else {
    if (s.repetitions === 0) s.interval_days = 1;
    else if (s.repetitions === 1) s.interval_days = 6;
    else s.interval_days = Math.max(1, Math.round(s.interval_days * s.ef));
    s.repetitions++;
  }
  s.ef = s.ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02));
  if (s.ef < 1.3) s.ef = 1.3;
  s.last_review = today();
  s.due_date = s.interval_days === 0 ? today() : dateAfter(s.interval_days);
  return s;
}
function isMastered(srs) { return srs && srs.repetitions >= 5 && srs.ef >= 2.5; }

// ============================================================
// TTS (Web Speech API)
// ============================================================
function pickVoice() {
  const voices = window.speechSynthesis ? window.speechSynthesis.getVoices() : [];
  if (settings.voiceName) {
    const v = voices.find(v => v.name === settings.voiceName);
    if (v) return v;
  }
  return voices.find(v => v.lang.startsWith('en') && /female|samantha|aria|jenny|zira/i.test(v.name))
      || voices.find(v => v.lang.startsWith('en-US'))
      || voices.find(v => v.lang.startsWith('en'))
      || null;
}
// rates 配列の各速度で順に読み上げる (キュー)
function speakSeq(text, rates) {
  if (!window.speechSynthesis) { alert('お使いのブラウザは音声合成に対応していません'); return; }
  window.speechSynthesis.cancel();
  const voice = pickVoice();
  rates.forEach(r => {
    const u = new SpeechSynthesisUtterance(text);
    u.lang = 'en-US'; u.rate = r;
    if (voice) u.voice = voice;
    window.speechSynthesis.speak(u);
  });
}
function speak(text, rate) { speakSeq(text, [rate != null ? rate : settings.defaultRate]); }
function speakSlow(text) { speakSeq(text, [0.65]); }
function speakRepeat(text, rate) { const r = rate != null ? rate : settings.defaultRate; speakSeq(text, [r, r, r]); }
function speakLadder(text) { speakSeq(text, [0.6, settings.defaultRate]); }

// ============================================================
// 効果音 (Web Audio APIで合成、外部ファイル不要)
// ============================================================
let _audioCtx = null;
function getAudioCtx() {
  if (_audioCtx === false) return null;
  if (!_audioCtx) {
    try { _audioCtx = new (window.AudioContext || window.webkitAudioContext)(); }
    catch (e) { _audioCtx = false; return null; }
  }
  return _audioCtx;
}
function playSound(type) {
  if (!settings.sound) return;
  const ctx = getAudioCtx();
  if (!ctx) return;
  if (ctx.state === 'suspended') ctx.resume();
  const now = ctx.currentTime;
  function tone(freq, start, dur, peak, wave) {
    const osc = ctx.createOscillator();
    const g = ctx.createGain();
    osc.type = wave || 'sine';
    osc.frequency.value = freq;
    osc.connect(g); g.connect(ctx.destination);
    g.gain.setValueAtTime(0.0001, now + start);
    g.gain.linearRampToValueAtTime(peak, now + start + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, now + start + dur);
    osc.start(now + start);
    osc.stop(now + start + dur + 0.03);
  }
  if (type === 'correct') {       // 明るい上昇2音
    tone(660, 0, 0.12, 0.22, 'sine');
    tone(988, 0.10, 0.20, 0.22, 'sine');
  } else {                        // 低い下降ブザー
    tone(233, 0, 0.20, 0.18, 'square');
    tone(165, 0.13, 0.24, 0.16, 'square');
  }
}

// ============================================================
// 出題ロジック (SRS対応)
// ============================================================
function pickRandomItems(pool, n) {
  return [...pool].sort(() => Math.random() - 0.5).slice(0, n);
}
function weightedSample(items, n, weightFn) {
  const scored = items.map(x => ({ x, key: -Math.pow(Math.random(), 1 / Math.max(0.01, weightFn(x))) }));
  scored.sort((a, b) => a.key - b.key);
  return scored.slice(0, n).map(s => s.x);
}

function selectItemsForSession(pool, mode, n = 10) {
  const progress = loadProgress();
  const t = today();
  const enriched = pool.map(item => ({ item, srs: getSrs(progress, item.id, mode) || newSrsState() }));
  const due    = enriched.filter(x => x.srs.last_review && x.srs.due_date && x.srs.due_date <= t);
  const fresh  = enriched.filter(x => !x.srs.last_review);
  const future = enriched.filter(x => x.srs.last_review && x.srs.due_date && x.srs.due_date > t);

  const dueCount = Math.min(due.length, Math.max(0, n - 3));
  const newCount = Math.min(fresh.length, n - dueCount);
  const shuffledDue = weightedSample(due, dueCount, x => 1 + (x.srs.lapses || 0) * 0.5);

  const cefrWeight = { A1: 1.15, A2: 1.05, B1: 1.0, B2: 0.9 };
  const sampledNew = weightedSample(fresh, newCount, x => cefrWeight[x.item.cefr] || 1.0);

  let selected = [...shuffledDue, ...sampledNew];
  if (selected.length < n) {
    selected = selected.concat(
      [...future].sort(() => Math.random() - 0.5).slice(0, n - selected.length));
  }
  selected.sort(() => Math.random() - 0.5);
  return selected.map(x => x.item);
}

// 音的類似度スコア
function phoneticScore(a, b) {
  if (!a || !b || a === b) return -Infinity;
  a = String(a).toLowerCase(); b = String(b).toLowerCase();
  let score = 0;
  if (a[0] === b[0]) score += 3;
  if (a[a.length-1] === b[b.length-1]) score += 1;
  score -= Math.abs(a.length - b.length) * 0.4;
  const bigramsA = new Set();
  for (let i = 0; i < a.length - 1; i++) bigramsA.add(a.substring(i, i + 2));
  for (let i = 0; i < b.length - 1; i++) if (bigramsA.has(b.substring(i, i + 2))) score += 1;
  const vA = a.replace(/[^aeiou]/g, ''), vB = b.replace(/[^aeiou]/g, '');
  if (vA && vA === vB) score += 2;
  return score;
}
// 文字列bigram類似 (慣用句用)
function bigramOverlap(a, b) {
  a = String(a).toLowerCase().replace(/\s+/g, ' ');
  b = String(b).toLowerCase().replace(/\s+/g, ' ');
  const setA = new Set();
  for (let i = 0; i < a.length - 1; i++) setA.add(a.substring(i, i + 2));
  let shared = 0;
  for (let i = 0; i < b.length - 1; i++) if (setA.has(b.substring(i, i + 2))) shared++;
  return shared;
}
function wordSet(s) { return new Set((s || '').toLowerCase().match(/[a-z']+/g) || []); }

function pickDistractors(target, pool, n = 3) {
  const cat = target.category;
  let candidates;
  if (cat === 'word') {
    candidates = pool.filter(x => x.pos === target.pos && x.lemma !== target.lemma
      && x.meaning_ja && x.meaning_ja !== target.meaning_ja);
    if (candidates.length < n + 2) {
      candidates = pool.filter(x => x.lemma !== target.lemma
        && x.meaning_ja && x.meaning_ja !== target.meaning_ja);
    }
  } else if (cat === 'idiom') {
    const tc = wordCountOf(target);
    candidates = pool.filter(x => Math.abs(wordCountOf(x) - tc) <= 1 && x.phrase !== target.phrase
      && x.meaning_ja && x.meaning_ja !== target.meaning_ja);
    if (candidates.length < n + 2) {
      candidates = pool.filter(x => x.phrase !== target.phrase
        && x.meaning_ja && x.meaning_ja !== target.meaning_ja);
    }
  } else { // phrase: 似た状況タグ + 単語オーバーラップ
    const tags = new Set(target.tags || []);
    candidates = pool.filter(x => x.phrase !== target.phrase
      && x.meaning_ja && x.meaning_ja !== target.meaning_ja
      && (x.tags || []).some(t => tags.has(t)));
    if (candidates.length < n + 2) {
      candidates = pool.filter(x => x.phrase !== target.phrase
        && x.meaning_ja && x.meaning_ja !== target.meaning_ja);
    }
  }
  if (candidates.length <= n) return candidates;

  let scored;
  if (cat === 'word') {
    const ts = getSurface(target);
    scored = candidates.map(c => ({ item: c, score: phoneticScore(ts, getSurface(c)) }));
  } else if (cat === 'idiom') {
    scored = candidates.map(c => ({ item: c, score: bigramOverlap(getSurface(target), getSurface(c)) }));
  } else {
    const tw = wordSet(getSurface(target));
    scored = candidates.map(c => {
      let shared = 0;
      for (const w of wordSet(getSurface(c))) if (tw.has(w)) shared++;
      return { item: c, score: shared };
    });
  }
  scored.sort((a, b) => b.score - a.score);
  const K = Math.min(scored.length, Math.max(n * 4, 12));
  return pickRandomItems(scored.slice(0, K).map(s => s.item), n);
}

function makeQuestion(target, pool, mode) {
  const distractors = pickDistractors(target, pool, 3);
  const allChoices = [target, ...distractors].sort(() => Math.random() - 0.5);
  return { target, mode, choices: allChoices, correctIndex: allChoices.indexOf(target) };
}

// ============================================================
// モード定義
// ============================================================
const MODES = {
  'word_audio_to_meaning':   { cat: 'word', icon: '🔊', title: '音声 → 意味', desc: 'TTSで単語を聴き、日本語意味を4択', choicesAs: 'meaning', useAudio: true },
  'word_audio_to_word':      { cat: 'word', icon: '🎧', title: '音声 → スペル', desc: 'TTSで単語を聴き、英単語のつづりを4択', choicesAs: 'surface', useAudio: true },
  'word_text_to_meaning':    { cat: 'word', icon: '👁', title: '単語 → 意味', desc: '単語表記を見て、日本語意味を4択', choicesAs: 'meaning', useAudio: false },
  'idiom_audio_to_meaning':  { cat: 'idiom', icon: '🔊', title: '音声 → 意味', desc: 'TTSで慣用句を聴き、日本語意味を4択', choicesAs: 'meaning', useAudio: true },
  'idiom_audio_to_word':     { cat: 'idiom', icon: '🎧', title: '音声 → 表記', desc: 'TTSで慣用句を聴き、英語表記を4択', choicesAs: 'surface', useAudio: true },
  'idiom_text_to_meaning':   { cat: 'idiom', icon: '👁', title: '慣用句 → 意味', desc: '慣用句を見て、日本語意味を4択', choicesAs: 'meaning', useAudio: false },
  'phrase_audio_to_meaning': { cat: 'phrase', icon: '🔊', title: '音声 → 意味', desc: 'TTSでフレーズを聴き、日本語意味を4択', choicesAs: 'meaning', useAudio: true },
  'phrase_audio_to_word':    { cat: 'phrase', icon: '🎧', title: '音声 → 表記', desc: 'TTSでフレーズを聴き、英語表記を4択', choicesAs: 'surface', useAudio: true },
  'phrase_text_to_meaning':  { cat: 'phrase', icon: '👁', title: 'フレーズ → 意味', desc: 'フレーズを見て、日本語意味を4択', choicesAs: 'meaning', useAudio: false },
};
const CAT_LABELS = { word: '単語', idiom: '慣用句', phrase: 'フレーズ' };

// 場面/機能/感情/スタイル/トピック タグの日本語ラベル
const TAG_LABELS = {
  travel:'旅行', restaurant:'レストラン', shopping:'買い物', business:'ビジネス', school:'学校',
  home:'家庭', medical:'医療', transportation:'交通', hotel:'ホテル',
  greeting:'挨拶', question:'質問', request:'依頼', apology:'謝罪', gratitude:'感謝',
  agreement:'同意', disagreement:'反対', goodbye:'別れ',
  positive:'肯定', negative:'否定', surprise:'驚き', concern:'心配', confusion:'困惑', excitement:'興奮',
  formal:'フォーマル', informal:'カジュアル', slang:'スラング', polite:'丁寧', casual:'くだけた',
  food:'食べ物', body:'身体', family:'家族', time:'時間', nature:'自然', weather:'天気',
  clothes:'衣服', color:'色', number:'数', animal:'動物', emotion:'感情',
};
function tagLabel(t) { return TAG_LABELS[t] || t; }

// ============================================================
// 状態
// ============================================================
let state = {
  view: 'home',
  category: 'word',
  mode: null,
  questions: [],
  currentIdx: 0,
  sessionScore: 0,
  sessionAnswers: [],
  selectedChoice: null,
  currentRate: settings.defaultRate,
  showFilter: false,
  filters: { cefr: new Set(), tags: new Set() },
};

const app = document.getElementById('app');

function render() {
  app.innerHTML = '';
  if (state.view === 'home') renderHome();
  else if (state.view === 'quiz') renderQuiz();
  else if (state.view === 'result') renderResult();
  else if (state.view === 'dashboard') renderDashboard();
  else if (state.view === 'settings') renderSettings();
}

function computeSrsSummary(pool, mode) {
  const progress = loadProgress();
  const t = today();
  let due = 0, mastered = 0, fresh = 0, learning = 0;
  for (const item of pool) {
    const srs = getSrs(progress, item.id, mode);
    if (!srs || !srs.last_review) { fresh++; continue; }
    if (isMastered(srs)) mastered++; else learning++;
    if (srs.due_date && srs.due_date <= t) due++;
  }
  return { due, mastered, fresh, learning };
}

// ============================================================
// ホーム画面
// ============================================================
function renderHome() {
  const progress = loadProgress();
  const accuracy = progress.totalAnswered > 0 ? Math.round((progress.totalCorrect / progress.totalAnswered) * 100) : 0;
  const cat = state.category;
  const pool = getPool(cat);
  const baseCount = basePool(cat).length;
  const modesForCat = Object.entries(MODES).filter(([_, m]) => m.cat === cat);

  function badgeBlock(modeName) {
    const s = computeSrsSummary(pool, modeName);
    return `<span class="srs-badge">
      ${s.due > 0 ? `<span class="badge badge-due">復習 ${s.due}</span>` : ''}
      <span class="badge badge-fresh">新規 ${s.fresh}</span>
      <span class="badge badge-mastered">習得 ${s.mastered}</span>
    </span>`;
  }
  const modeButtons = modesForCat.map(([name, m]) => `
    <button class="mode-btn" data-mode="${name}">
      <span class="mode-title">${m.icon} ${m.title}</span>
      <span class="mode-desc">${m.desc}</span>
      ${badgeBlock(name)}
    </button>`).join('');

  const categoryTabs = ['word','idiom','phrase'].map(c =>
    `<button class="category-tab ${c===cat?'active':''}" data-cat="${c}">${CAT_LABELS[c]}</button>`).join('');

  app.innerHTML = `
    <h1>__APP_NAME__</h1>
    <p class="subtitle">音と意味とスペルの3軸で鍛えるリスニング学習 / 1セッション=10問</p>
    <div class="category-tabs">${categoryTabs}</div>
    ${renderFilterPanel(cat, pool.length, baseCount)}
    <div class="card">
      <h3 style="margin-bottom:12px; color:var(--accent);">モードを選択</h3>
      ${pool.length === 0
        ? '<p class="small-text">この絞り込み条件に該当する項目がありません。フィルタを調整してください。</p>'
        : modeButtons}
    </div>
    <div class="stats">
      <div class="stat-item"><div class="stat-value">${progress.sessions}</div><div class="stat-label">セッション</div></div>
      <div class="stat-item"><div class="stat-value">${progress.totalAnswered}</div><div class="stat-label">解答数</div></div>
      <div class="stat-item"><div class="stat-value">${accuracy}%</div><div class="stat-label">正答率</div></div>
    </div>
    <div style="margin-top:14px; display:flex; gap:8px; flex-wrap:wrap;">
      <button class="next-btn home-nav" id="dashboard-btn" style="background:var(--panel2); color:var(--text); flex:1;">📊 ダッシュボード</button>
      <button class="next-btn home-nav" id="settings-btn" style="background:var(--panel2); color:var(--text); flex:1;">⚙️ 設定</button>
    </div>
    <p class="small-text center" style="margin-top:14px;">SM-2 間隔反復 / 不正解は同日再出題</p>
  `;

  app.querySelectorAll('.category-tab').forEach(btn =>
    btn.addEventListener('click', () => { state.category = btn.dataset.cat; render(); }));
  app.querySelectorAll('.mode-btn').forEach(btn =>
    btn.addEventListener('click', () => startQuiz(btn.dataset.mode)));
  document.getElementById('dashboard-btn').addEventListener('click', () => { state.view = 'dashboard'; render(); });
  document.getElementById('settings-btn').addEventListener('click', () => { state.view = 'settings'; render(); });
  bindFilterEvents(cat);
}

function renderFilterPanel(cat, filteredCount, baseCount) {
  const pool = basePool(cat);
  const cefrLevels = ['A1','A2','B1','B2'];
  const tagsPresent = [...new Set(pool.flatMap(x => x.tags || []))].sort();
  const f = state.filters;
  const activeCount = f.cefr.size + f.tags.size;

  const summaryParts = [];
  if (f.cefr.size) summaryParts.push([...f.cefr].join('+'));
  if (f.tags.size) summaryParts.push([...f.tags].map(tagLabel).join('+'));
  const summaryText = activeCount === 0
    ? `絞り込みなし / 全${baseCount}件`
    : `絞り込み中: ${summaryParts.join(' / ')} → ${filteredCount}件`;

  if (!state.showFilter) {
    return `<div class="card" style="padding:12px 18px;">
      <div class="filter-summary" id="filter-toggle">
        <span>🔎 ${summaryText}</span><span>${activeCount>0?'▼ 編集':'▶ フィルタ'}</span>
      </div></div>`;
  }
  const cefrChips = cefrLevels.map(l =>
    `<span class="chip ${f.cefr.has(l)?'on':''}" data-cefr="${l}">${l}</span>`).join('');
  const tagChips = tagsPresent.map(t =>
    `<span class="chip ${f.tags.has(t)?'on':''}" data-tag="${t}">${tagLabel(t)}</span>`).join('');
  return `<div class="card">
    <div class="filter-summary" id="filter-toggle"><span>🔎 ${summaryText}</span><span>▲ 閉じる</span></div>
    <div class="filter-group-label">CEFRレベル</div><div>${cefrChips}</div>
    <div class="filter-group-label">タグ</div><div>${tagChips || '<span class="small-text">タグなし</span>'}</div>
    ${activeCount>0?'<div style="margin-top:10px;"><span class="chip" id="filter-clear">✕ すべて解除</span></div>':''}
  </div>`;
}

function bindFilterEvents(cat) {
  const toggle = document.getElementById('filter-toggle');
  if (toggle) toggle.addEventListener('click', () => { state.showFilter = !state.showFilter; render(); });
  app.querySelectorAll('[data-cefr]').forEach(chip => chip.addEventListener('click', () => {
    const v = chip.dataset.cefr;
    state.filters.cefr.has(v) ? state.filters.cefr.delete(v) : state.filters.cefr.add(v);
    render();
  }));
  app.querySelectorAll('[data-tag]').forEach(chip => chip.addEventListener('click', () => {
    const v = chip.dataset.tag;
    state.filters.tags.has(v) ? state.filters.tags.delete(v) : state.filters.tags.add(v);
    render();
  }));
  const clear = document.getElementById('filter-clear');
  if (clear) clear.addEventListener('click', () => { state.filters.cefr.clear(); state.filters.tags.clear(); render(); });
}

// ============================================================
// クイズ
// ============================================================
function isAudioMode(mode) { const m = MODES[mode]; return m && m.useAudio; }

function startQuiz(mode) {
  const modeDef = MODES[mode];
  if (!modeDef) { alert('不明なモード: ' + mode); return; }
  const pool = getPool(modeDef.cat);
  const items = selectItemsForSession(pool, mode, 10);
  if (items.length === 0) { alert('出題できる問題がありません'); return; }
  state.questions = items.map(t => makeQuestion(t, pool, mode));
  state.currentIdx = 0; state.sessionScore = 0; state.sessionAnswers = [];
  state.selectedChoice = null; state.view = 'quiz'; state.mode = mode;
  state.category = modeDef.cat; state.currentRate = settings.defaultRate;
  render();
  if (isAudioMode(mode)) setTimeout(() => speak(getTtsText(state.questions[0].target), state.currentRate), 300);
}

// 発音情報ブロック (IPA + 音節)
function pronInfo(target) {
  let html = '';
  if (settings.showIpa && target.ipa) html += `<div class="pron-line">${escapeHtml(target.ipa)}</div>`;
  if (settings.showSyllables && target.syllables) html += `<div class="syll-line">🎵 ${escapeHtml(target.syllables)}</div>`;
  return html;
}

// 発音コントロール (再生ボタン群 + トグル)
function pronControls(forAudio) {
  const playLabel = forAudio ? '🔊 再生' : '🔊 発音を聴く';
  const cls = forAudio ? 'play-btn' : 'play-btn small';
  return `
    <div class="pron-controls">
      <button class="${cls}" id="play-tts">${playLabel}</button>
      <button class="play-btn small ghost" id="play-slow">🐢 ゆっくり</button>
      <button class="play-btn small ghost" id="play-repeat">🔁 3回</button>
      <button class="play-btn small ghost" id="play-ladder">🪜 ゆっくり→普通</button>
    </div>
    <div class="toggle-row">
      <button class="play-btn small ghost ${settings.showIpa?'on':''}" id="toggle-ipa">📖 IPA</button>
      <button class="play-btn small ghost ${settings.showSyllables?'on':''}" id="toggle-syll">🎵 音節</button>
      <select class="speed-select" id="speed-select">
        <option value="0.7" ${state.currentRate==0.7?'selected':''}>ゆっくり 0.7x</option>
        <option value="0.9" ${state.currentRate==0.9?'selected':''}>標準 0.9x</option>
        <option value="1.1" ${state.currentRate==1.1?'selected':''}>速め 1.1x</option>
      </select>
    </div>`;
}

function renderQuiz() {
  const q = state.questions[state.currentIdx];
  const target = q.target;
  const progress = (state.currentIdx / state.questions.length) * 100;
  const mode = state.mode, modeDef = MODES[mode], cat = modeDef.cat;
  const isAudio = modeDef.useAudio;
  const choicesAsSurface = modeDef.choicesAs === 'surface';

  const promptByCat = {
    word:   isAudio ? (choicesAsSurface ? 'いま聞こえた単語のつづりは？' : 'いま聞こえた単語の意味は？') : 'この単語の意味は？',
    idiom:  isAudio ? (choicesAsSurface ? 'いま聞こえた慣用句の英語表記は？' : 'いま聞こえた慣用句の意味は？') : 'この慣用句の意味は？',
    phrase: isAudio ? (choicesAsSurface ? 'いま聞こえたフレーズの英語表記は？' : 'いま聞こえたフレーズの意味は？') : 'このフレーズの意味は？',
  };
  const promptText = promptByCat[cat];

  let mainContent;
  if (isAudio) {
    mainContent = `<p style="color:var(--muted); margin-bottom:8px;">${promptText}</p>${pronControls(true)}`;
  } else {
    const surface = getSurface(target);
    let displayClass = 'word-display', metaLine = '';
    if (cat === 'word') {
      displayClass = 'word-display';
      metaLine = `<div class="word-meta">${POS_LABELS[target.pos] || target.pos || ''} / CEFR ${target.cefr || '?'}</div>`;
    } else if (cat === 'idiom') {
      displayClass = 'phrase-display';
      metaLine = `<div class="word-meta">慣用句 / CEFR ${target.cefr || '?'}</div>`;
    } else {
      displayClass = 'phrase-display';
      metaLine = target.situation ? `<div class="word-meta">状況: ${escapeHtml(target.situation)}</div>` : '';
    }
    mainContent = `
      <p style="color:var(--muted); margin-bottom:8px;">${promptText}</p>
      <div class="${displayClass}">${escapeHtml(surface)}</div>
      ${pronInfo(target)}
      ${metaLine}
      ${pronControls(false)}`;
  }

  const choicesHtml = q.choices.map((c, i) => {
    const key = ['A','B','C','D'][i];
    const displayText = choicesAsSurface ? getSurface(c) : (stripEnglishHints(c.meaning_ja) || '(意味未登録)');
    return `<button class="choice" data-idx="${i}"><span class="choice-key">${key}</span>${escapeHtml(displayText)}</button>`;
  }).join('');

  // フレーズ(長文)や英語表記選択肢は縦並び
  const longChoices = cat === 'phrase' || (choicesAsSurface && cat !== 'word');
  const choicesClass = longChoices ? 'choices choices-stacked' : 'choices';

  app.innerHTML = `
    <div class="progress-bar"><div class="progress-fill" style="width:${progress}%"></div></div>
    <div class="question-header">
      <span>${CAT_LABELS[cat]} ${modeDef.icon} | 問題 ${state.currentIdx + 1} / ${state.questions.length}</span>
      <span>正解 ${state.sessionScore}</span>
    </div>
    <div class="card">
      <div class="question-main">${mainContent}</div>
      <div class="${choicesClass}">${choicesHtml}</div>
      <div id="feedback-area"></div>
    </div>`;

  bindPronEvents(target);
  app.querySelectorAll('.choice').forEach(btn =>
    btn.addEventListener('click', () => handleAnswer(parseInt(btn.dataset.idx))));
}

function bindPronEvents(target) {
  const txt = getTtsText(target);
  const on = (id, fn) => { const el = document.getElementById(id); if (el) el.addEventListener('click', fn); };
  on('play-tts', () => speak(txt, state.currentRate));
  on('play-slow', () => speakSlow(txt));
  on('play-repeat', () => speakRepeat(txt, state.currentRate));
  on('play-ladder', () => speakLadder(txt));
  on('toggle-ipa', () => { settings.showIpa = !settings.showIpa; saveSettings(settings); render(); });
  on('toggle-syll', () => { settings.showSyllables = !settings.showSyllables; saveSettings(settings); render(); });
  const sel = document.getElementById('speed-select');
  if (sel) sel.addEventListener('change', e => { state.currentRate = parseFloat(e.target.value); });
}

function handleAnswer(idx) {
  if (state.selectedChoice !== null) return;
  state.selectedChoice = idx;
  const q = state.questions[state.currentIdx];
  const target = q.target;
  const correct = (idx === q.correctIndex);
  if (correct) state.sessionScore++;
  playSound(correct ? 'correct' : 'wrong');
  state.sessionAnswers.push({ itemId: target.id, correct });

  app.querySelectorAll('.choice').forEach((c, i) => {
    c.classList.add('disabled');
    if (i === q.correctIndex) c.classList.add('correct');
    else if (i === idx && !correct) c.classList.add('wrong');
  });

  const fb = document.getElementById('feedback-area');
  const symbol = correct ? '✓ 正解!' : '✗ 不正解';
  const klass = correct ? 'correct' : 'wrong';
  const surface = getSurface(target);
  let detail = `<div><strong>${symbol}</strong> ${escapeHtml(surface)} = ${escapeHtml(target.meaning_ja)}</div>`;
  if (target.literal_ja) detail += `<div class="small-text" style="margin-top:4px;">${escapeHtml(target.literal_ja)}</div>`;
  let extra = '';
  if (target.example_en) {
    extra = `<div class="example">例: "${escapeHtml(target.example_en)}"`;
    if (target.example_ja) extra += `<br><span class="example-ja">${escapeHtml(target.example_ja)}</span>`;
    extra += `</div>`;
  } else if (target.situation) {
    extra = `<div class="example">状況: ${escapeHtml(target.situation)}</div>`;
  }
  const pron = pronInfo(target);

  fb.innerHTML = `
    <div class="feedback ${klass}">${detail}${pron}${extra}</div>
    <button class="next-btn" id="next-btn">${state.currentIdx + 1 < state.questions.length ? '次の問題 →' : '結果を見る'}</button>`;
  document.getElementById('next-btn').addEventListener('click', nextQuestion);
}

function nextQuestion() {
  state.currentIdx++;
  state.selectedChoice = null;
  if (state.currentIdx >= state.questions.length) { finishSession(); return; }
  render();
  if (isAudioMode(state.mode)) setTimeout(() => speak(getTtsText(state.questions[state.currentIdx].target), state.currentRate), 300);
}

function finishSession() {
  const p = loadProgress();
  p.sessions++;
  p.totalAnswered += state.sessionAnswers.length;
  p.totalCorrect += state.sessionScore;
  state.sessionAnswers.forEach(a => {
    const key = `${a.itemId}::${state.mode}`;
    p.srs[key] = sm2Update(p.srs[key] || newSrsState(), a.correct ? 4 : 2);
  });
  p.history.unshift({ date: today(), mode: state.mode, score: state.sessionScore, total: state.sessionAnswers.length });
  p.history = p.history.slice(0, 30);
  saveProgress(p);
  state.view = 'result';
  render();
}

function renderResult() {
  const score = state.sessionScore, total = state.questions.length;
  const pct = Math.round((score / total) * 100);
  let msg = pct === 100 ? '🎉 完璧！' : pct >= 80 ? '素晴らしい!' : pct >= 60 ? 'よくできました'
          : pct >= 40 ? '練習を続けよう' : '何度でも挑戦できます';
  const progress = loadProgress();
  const itemRows = state.sessionAnswers.map((a, i) => {
    const target = state.questions[i].target;
    const srs = getSrs(progress, target.id, state.mode);
    const nextDate = srs ? srs.due_date : '';
    const interval = srs ? srs.interval_days : 0;
    const icon = a.correct ? '<span style="color:var(--good);">✓</span>' : '<span style="color:var(--bad);">✗</span>';
    const masterIcon = srs && isMastered(srs) ? ' 🏆' : '';
    return `<div style="padding:10px; background:var(--panel2); border-radius:8px; margin-bottom:6px; display:flex; justify-content:space-between; gap:8px; align-items:center;">
      <div style="flex:1; min-width:0;">${icon} <strong>${escapeHtml(getSurface(target))}</strong>${masterIcon}
        <span style="color:var(--muted); margin-left:8px; font-size:0.9em;">= ${escapeHtml(target.meaning_ja)}</span></div>
      <div class="small-text" style="white-space:nowrap;">${interval}日後<br>${nextDate}</div></div>`;
  }).join('');

  app.innerHTML = `
    <h1>セッション完了</h1>
    <div class="card">
      <div class="result-score">${score}/${total}</div>
      <p class="result-message">${msg} (${pct}%)</p>
      <p class="small-text center" style="margin-bottom:16px;">正解 → 次の復習が先に延長 / 不正解 → 翌日に再出題</p>
      ${itemRows}
      <button class="next-btn" id="restart-btn" style="margin-top:20px;">もう一度 (新セット)</button>
      <button class="next-btn" id="home-btn" style="margin-top:8px; background:var(--panel2); color:var(--text);">ホームへ</button>
    </div>`;
  document.getElementById('restart-btn').addEventListener('click', () => startQuiz(state.mode));
  document.getElementById('home-btn').addEventListener('click', () => { state.view = 'home'; render(); });
}

// ============================================================
// ダッシュボード
// ============================================================
function renderModeProgress(s, total) {
  const pct = total > 0 ? Math.round((s.mastered / total) * 100) : 0;
  return `
    <div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div>
    <div style="display:flex; justify-content:space-between; gap:8px; flex-wrap:wrap; margin-top:8px;">
      <span class="badge badge-due">復習期限切れ ${s.due}</span>
      <span class="badge badge-fresh">未学習 ${s.fresh}</span>
      <span class="badge badge-learning">学習中 ${s.learning}</span>
      <span class="badge badge-mastered">習得済み ${s.mastered}</span>
    </div>
    <p class="small-text" style="margin-top:8px;">習得率: ${pct}% (${s.mastered}/${total})</p>`;
}

function renderCatBlock(cat) {
  const pool = basePool(cat);
  const total = pool.length;
  const modesForCat = Object.entries(MODES).filter(([_, m]) => m.cat === cat);
  const blocks = modesForCat.map(([name, m]) => `
    <div style="margin-top:12px;">
      <h4 style="margin-bottom:6px; color:#8ad9b0; font-size:0.95em;">${m.icon} ${m.title}</h4>
      ${renderModeProgress(computeSrsSummary(pool, name), total)}
    </div>`).join('');
  return `<div class="card"><h3 style="margin-bottom:6px; color:var(--accent);">${CAT_LABELS[cat]} (${total}件)</h3>${blocks}</div>`;
}

// CEFR別の習得率 (全カテゴリ・全モード合算: どれか1モードで習得済みなら習得)
function renderCefrStats() {
  const progress = loadProgress();
  const levels = ['A1','A2','B1','B2'];
  const allItems = [...basePool('word'), ...basePool('idiom'), ...basePool('phrase')];
  const rows = levels.map(lv => {
    const items = allItems.filter(x => x.cefr === lv);
    let mastered = 0;
    for (const it of items) {
      const modes = Object.entries(MODES).filter(([_, m]) => m.cat === it.category).map(([n]) => n);
      if (modes.some(m => { const s = getSrs(progress, it.id, m); return s && isMastered(s); })) mastered++;
    }
    const pct = items.length > 0 ? Math.round((mastered / items.length) * 100) : 0;
    return `<div style="margin-bottom:10px;">
      <div style="display:flex; justify-content:space-between; font-size:0.9em; margin-bottom:4px;">
        <span>${lv}</span><span>${mastered}/${items.length} (${pct}%)</span></div>
      <div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div></div>`;
  }).join('');
  return `<div class="card"><h3 style="margin-bottom:12px; color:var(--accent);">CEFRレベル別の習得率</h3>${rows}</div>`;
}

// 場面タグ別の習得率 (上位)
function renderTagStats() {
  const progress = loadProgress();
  const allItems = [...basePool('word'), ...basePool('idiom'), ...basePool('phrase')];
  const tagCount = {}, tagMastered = {};
  for (const it of allItems) {
    const modes = Object.entries(MODES).filter(([_, m]) => m.cat === it.category).map(([n]) => n);
    const mastered = modes.some(m => { const s = getSrs(progress, it.id, m); return s && isMastered(s); });
    for (const t of (it.tags || [])) {
      tagCount[t] = (tagCount[t] || 0) + 1;
      if (mastered) tagMastered[t] = (tagMastered[t] || 0) + 1;
    }
  }
  const top = Object.keys(tagCount).sort((a, b) => tagCount[b] - tagCount[a]).slice(0, 12);
  if (top.length === 0) return '';
  const rows = top.map(t => {
    const tot = tagCount[t], mas = tagMastered[t] || 0;
    const pct = Math.round((mas / tot) * 100);
    return `<div style="margin-bottom:8px;">
      <div style="display:flex; justify-content:space-between; font-size:0.85em; margin-bottom:3px;">
        <span>${tagLabel(t)}</span><span>${mas}/${tot} (${pct}%)</span></div>
      <div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div></div>`;
  }).join('');
  return `<div class="card"><h3 style="margin-bottom:12px; color:var(--accent);">場面・トピックタグ別の習得率 (上位)</h3>${rows}</div>`;
}

function renderDashboard() {
  const progress = loadProgress();
  const MODE_LABELS_SHORT = {};
  Object.entries(MODES).forEach(([n, m]) => MODE_LABELS_SHORT[n] = `${CAT_LABELS[m.cat]} ${m.icon}`);
  const histRows = progress.history.slice(0, 10).map(h => {
    const pct = Math.round((h.score / h.total) * 100);
    return `<tr><td>${h.date}</td><td>${MODE_LABELS_SHORT[h.mode] || h.mode}</td><td>${h.score}/${h.total}</td><td>${pct}%</td></tr>`;
  }).join('');

  app.innerHTML = `
    <h1>📊 進捗ダッシュボード</h1>
    <button class="next-btn" id="back-btn" style="background:var(--panel2); color:var(--text); margin-bottom:14px;">← ホームへ戻る</button>
    ${renderCatBlock('word')}
    ${renderCatBlock('idiom')}
    ${renderCatBlock('phrase')}
    ${renderCefrStats()}
    ${renderTagStats()}
    <div class="card">
      <h3 style="margin-bottom:12px; color:var(--accent);">直近セッション履歴</h3>
      ${progress.history.length === 0
        ? '<p class="small-text">まだセッションがありません</p>'
        : `<table style="width:100%; font-size:0.9em;"><thead><tr style="color:var(--muted); text-align:left;">
            <th>日付</th><th>モード</th><th>スコア</th><th>正答率</th></tr></thead><tbody>${histRows}</tbody></table>`}
    </div>`;
  document.getElementById('back-btn').addEventListener('click', () => { state.view = 'home'; render(); });
}

// ============================================================
// 設定画面
// ============================================================
function renderSettings() {
  const voices = window.speechSynthesis ? window.speechSynthesis.getVoices().filter(v => v.lang.startsWith('en')) : [];
  const voiceOptions = ['<option value="">自動選択 (en-US Female優先)</option>']
    .concat(voices.map(v => `<option value="${escapeHtml(v.name)}" ${settings.voiceName===v.name?'selected':''}>${escapeHtml(v.name)} (${v.lang})</option>`)).join('');

  app.innerHTML = `
    <h1>⚙️ 設定</h1>
    <button class="next-btn" id="back-btn" style="background:var(--panel2); color:var(--text); margin-bottom:14px;">← ホームへ戻る</button>
    <div class="card">
      <div class="setting-row">
        <div><div class="setting-label">TTS音声</div><div class="setting-desc">読み上げに使う英語音声</div></div>
        <select class="speed-select" id="voice-select">${voiceOptions}</select>
      </div>
      <div class="setting-row">
        <div><div class="setting-label">デフォルト速度</div><div class="setting-desc">クイズ開始時の読み上げ速度</div></div>
        <select class="speed-select" id="rate-select">
          <option value="0.7" ${settings.defaultRate==0.7?'selected':''}>ゆっくり 0.7x</option>
          <option value="0.9" ${settings.defaultRate==0.9?'selected':''}>標準 0.9x</option>
          <option value="1.1" ${settings.defaultRate==1.1?'selected':''}>速め 1.1x</option>
        </select>
      </div>
      <div class="setting-row">
        <div><div class="setting-label">IPA発音記号を表示</div><div class="setting-desc">/təˈmeɪtoʊ/ のような発音記号</div></div>
        <label class="switch"><input type="checkbox" id="set-ipa" ${settings.showIpa?'checked':''}><span class="slider"></span></label>
      </div>
      <div class="setting-row">
        <div><div class="setting-label">音節・強勢を表示</div><div class="setting-desc">to-MA-to のような音節区切り</div></div>
        <label class="switch"><input type="checkbox" id="set-syll" ${settings.showSyllables?'checked':''}><span class="slider"></span></label>
      </div>
      <div class="setting-row">
        <div><div class="setting-label">効果音</div><div class="setting-desc">正解・不正解のサウンド</div></div>
        <label class="switch"><input type="checkbox" id="set-sound" ${settings.sound?'checked':''}><span class="slider"></span></label>
      </div>
    </div>
    <div class="card">
      <h3 style="margin-bottom:12px; color:var(--accent);">データ管理</h3>
      <button class="next-btn" id="export-btn" style="background:var(--panel2); color:var(--text);">💾 進捗をエクスポート</button>
      <button class="next-btn" id="import-btn" style="background:var(--panel2); color:var(--text); margin-top:8px;">📂 進捗をインポート</button>
      <input type="file" id="import-file" accept="application/json" style="display:none;">
      <button class="next-btn" id="reset-btn" style="background:var(--bad-bg); color:var(--bad-text); margin-top:8px;">🗑 進捗データを初期化</button>
    </div>`;

  document.getElementById('back-btn').addEventListener('click', () => { state.view = 'home'; render(); });
  document.getElementById('voice-select').addEventListener('change', e => { settings.voiceName = e.target.value || null; saveSettings(settings); });
  document.getElementById('rate-select').addEventListener('change', e => { settings.defaultRate = parseFloat(e.target.value); saveSettings(settings); });
  document.getElementById('set-ipa').addEventListener('change', e => { settings.showIpa = e.target.checked; saveSettings(settings); });
  document.getElementById('set-syll').addEventListener('change', e => { settings.showSyllables = e.target.checked; saveSettings(settings); });
  document.getElementById('set-sound').addEventListener('change', e => { settings.sound = e.target.checked; saveSettings(settings); if (e.target.checked) playSound('correct'); });
  document.getElementById('export-btn').addEventListener('click', exportProgress);
  const importFile = document.getElementById('import-file');
  document.getElementById('import-btn').addEventListener('click', () => importFile.click());
  importFile.addEventListener('change', importProgress);
  document.getElementById('reset-btn').addEventListener('click', () => {
    if (confirm('進捗データをすべて削除します。よろしいですか？')) {
      localStorage.removeItem(STORAGE_KEY);
      alert('進捗を初期化しました'); render();
    }
  });
}

function exportProgress() {
  const blob = new Blob([JSON.stringify(loadProgress(), null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `english-quiz-progress-${today()}.json`; a.click();
  URL.revokeObjectURL(url);
}
function importProgress(e) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = ev => {
    try {
      const data = JSON.parse(ev.target.result);
      if (!data || typeof data !== 'object' || !data.srs) throw new Error('形式が不正');
      saveProgress(Object.assign(defaultProgress(), data));
      alert('進捗をインポートしました'); render();
    } catch (err) { alert('インポート失敗: ' + err.message); }
  };
  reader.readAsText(file);
}

// ============================================================
// ユーティリティ
// ============================================================
function escapeHtml(s) {
  if (s == null) return '';
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
// 4択選択肢から英語混入を除去
function stripEnglishHints(text) {
  if (!text) return '';
  let result = String(text).replace(/[（(][^）)]*[a-zA-Z][^）)]*[）)]/g, '');
  result = result.replace(/[、，,／/ \s]+$/, '').trim();
  return result || text;
}

// キーボードショートカット
document.addEventListener('keydown', e => {
  if (state.view === 'quiz' && state.selectedChoice === null) {
    const idx = { '1':0, '2':1, '3':2, '4':3, 'a':0, 'b':1, 'c':2, 'd':3 }[e.key.toLowerCase()];
    if (idx !== undefined) handleAnswer(idx);
    else if (e.key === ' ' || e.key === 'Enter') { const b = document.getElementById('play-tts'); if (b) b.click(); e.preventDefault(); }
  } else if (e.key === 'Enter') {
    const b = document.getElementById('next-btn'); if (b) b.click();
  }
});

if (window.speechSynthesis) {
  window.speechSynthesis.getVoices();
  window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
}

render();
</script>
</body>
</html>
"""


def _load(path):
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [x for x in data if x.get("meaning_ja")]


def main():
    # output/data を優先、無ければ output/app/data を見る
    def find(name):
        p1 = DATA_DIR / name
        p2 = APP_DATA_DIR / name
        return p1 if p1.exists() else p2

    words = _load(find("pool_words.json"))
    idioms = _load(find("pool_idioms.json"))
    phrases = _load(find("pool_phrases.json"))

    dump = lambda d: json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    html = (HTML_TEMPLATE
            .replace("__APP_NAME__", APP_NAME)
            .replace("__WORDS_POOL_JSON__", dump(words))
            .replace("__IDIOMS_POOL_JSON__", dump(idioms))
            .replace("__PHRASES_POOL_JSON__", dump(phrases)))
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"[build_html] Generated: {OUT_HTML}")
    print(f"[build_html] Size: {OUT_HTML.stat().st_size / 1024:.1f} KB")
    print(f"[build_html] words: {len(words)} / idioms: {len(idioms)} / phrases: {len(phrases)}")


if __name__ == "__main__":
    main()
