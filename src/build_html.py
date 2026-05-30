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
# GitHub Pages 配信用 (フォルダは root か docs しか選べない仕様)
DOCS_HTML = PROJECT_ROOT / "docs" / "index.html"

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

  /* 実績バッジ(折りたたみ) */
  details.badge-card { padding: 0; }
  details.badge-card > summary {
    display: flex; justify-content: space-between; align-items: center;
    cursor: pointer; list-style: none; padding: 16px 22px;
    font-weight: bold; color: var(--accent);
  }
  details.badge-card > summary::-webkit-details-marker { display: none; }
  .badge-chevron { display: inline-block; color: var(--muted); transition: transform 0.15s; }
  details.badge-card[open] .badge-chevron { transform: rotate(180deg); }
  .badge-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(78px, 1fr));
    gap: 8px; padding: 0 22px 18px;
  }

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
  return {
    showIpa: true, showSyllables: true, defaultRate: 0.9, voiceName: null, sound: true,
    // Dropbox同期 (PKCE方式)
    dbxAppKey: null,         // Dropbox App Console で取得した App key (公開IDなので共有しても安全)
    dbxRefreshToken: null,   // 長期トークン (この端末ブラウザ内のみに保存)
    dbxSyncEnabled: false,   // 同期スイッチ
    dbxLastSync: null,       // 最終同期時刻 (ISO文字列)
    dbxLastError: null,
  };
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
  return {
    version: 1, sessions: 0, totalAnswered: 0, totalCorrect: 0, xp: 0, srs: {}, history: [], updatedAt: 0,
    // カテゴリ/品詞/CEFR/タグ別の累計正解数 (二つ名・実績バッジ判定用)
    catCorrect: {}, posCorrect: {}, cefrCorrect: {}, tagCorrect: {},
    // 音声モード vs 表示モードの成績
    audioAnswered: 0, audioCorrect: 0, textAnswered: 0, textCorrect: 0,
    // プレイ実績
    maxCombo: 0, dayStreak: 0, lastPlayDate: '', morningSessions: 0, nightSessions: 0,
    badges: [],
  };
}
function loadProgress() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (raw) { try { return Object.assign(defaultProgress(), JSON.parse(raw)); } catch (e) {} }
  return defaultProgress();
}
function saveProgress(p, opts) {
  opts = opts || {};
  if (!opts.preserveTimestamp) p.updatedAt = Date.now();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
  // Dropbox 同期 (有効時のみ、非同期、失敗してもlocalStorageは無事)
  if (!opts.skipSync && settings.dbxSyncEnabled && settings.dbxRefreshToken) {
    Dropbox.pushProgress(p).catch(e => console.warn('[sync] push failed:', e.message));
  }
}

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
// Dropbox 同期 (PKCE方式・App folder限定)
// 設計:
//  - App key は公開IDなので localStorage 保存(settings.dbxAppKey)。
//  - refresh token は端末ブラウザ内のみ(settings.dbxRefreshToken)。コードや公開サイトに一切含めない。
//  - 競合解決は updatedAt の大きい方を採用。
//  - オフライン/失敗時は localStorage のみ更新し、次回成功時に再同期。
// ============================================================
const Dropbox = (function() {
  const FILE_PATH = '/progress.json';
  const PKCE_VERIFIER_KEY = 'english.quiz.dbx_pkce_verifier';
  let accessToken = null;       // メモリのみ(短期)
  let accessTokenExpiresAt = 0;

  function base64UrlEncode(buf) {
    const bytes = new Uint8Array(buf);
    let s = '';
    for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
    return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }
  async function sha256(str) {
    const data = new TextEncoder().encode(str);
    return crypto.subtle.digest('SHA-256', data);
  }
  function randomVerifier() {
    const a = new Uint8Array(64);
    crypto.getRandomValues(a);
    return base64UrlEncode(a.buffer);
  }
  function redirectUri() {
    // 現在の origin + path をそのまま使う
    return location.origin + location.pathname;
  }

  // 1. ログイン開始: Dropbox認可ページへ
  async function startLogin(appKey) {
    if (!appKey) throw new Error('App key が設定されていません');
    const verifier = randomVerifier();
    const challenge = base64UrlEncode(await sha256(verifier));
    localStorage.setItem(PKCE_VERIFIER_KEY, verifier);
    settings.dbxAppKey = appKey;
    saveSettings(settings);
    const url = new URL('https://www.dropbox.com/oauth2/authorize');
    url.searchParams.set('client_id', appKey);
    url.searchParams.set('response_type', 'code');
    url.searchParams.set('code_challenge', challenge);
    url.searchParams.set('code_challenge_method', 'S256');
    url.searchParams.set('redirect_uri', redirectUri());
    url.searchParams.set('token_access_type', 'offline');  // refresh token を得る
    location.href = url.toString();
  }

  // 2. リダイレクトで戻ってきたとき: code を refresh token に交換
  async function handleRedirect() {
    const params = new URLSearchParams(location.search);
    const code = params.get('code');
    if (!code) return false;
    const verifier = localStorage.getItem(PKCE_VERIFIER_KEY);
    const appKey = settings.dbxAppKey;
    if (!verifier || !appKey) return false;
    try {
      const body = new URLSearchParams({
        code, grant_type: 'authorization_code',
        client_id: appKey, code_verifier: verifier,
        redirect_uri: redirectUri(),
      });
      const r = await fetch('https://api.dropboxapi.com/oauth2/token', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: body.toString(),
      });
      if (!r.ok) throw new Error('token交換失敗 HTTP ' + r.status);
      const data = await r.json();
      settings.dbxRefreshToken = data.refresh_token;
      settings.dbxSyncEnabled = true;
      settings.dbxLastError = null;
      saveSettings(settings);
      accessToken = data.access_token;
      accessTokenExpiresAt = Date.now() + (data.expires_in - 60) * 1000;
      localStorage.removeItem(PKCE_VERIFIER_KEY);
      // URLから ?code= を消す
      history.replaceState({}, '', location.origin + location.pathname);
      return true;
    } catch (e) {
      settings.dbxLastError = '接続失敗: ' + e.message;
      saveSettings(settings);
      return false;
    }
  }

  async function getAccessToken() {
    if (accessToken && Date.now() < accessTokenExpiresAt) return accessToken;
    if (!settings.dbxRefreshToken || !settings.dbxAppKey) throw new Error('未接続');
    const body = new URLSearchParams({
      grant_type: 'refresh_token',
      refresh_token: settings.dbxRefreshToken,
      client_id: settings.dbxAppKey,
    });
    const r = await fetch('https://api.dropboxapi.com/oauth2/token', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: body.toString(),
    });
    if (!r.ok) throw new Error('refresh失敗 HTTP ' + r.status);
    const data = await r.json();
    accessToken = data.access_token;
    accessTokenExpiresAt = Date.now() + (data.expires_in - 60) * 1000;
    return accessToken;
  }

  async function pullProgress() {
    const token = await getAccessToken();
    const r = await fetch('https://content.dropboxapi.com/2/files/download', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + token,
        'Dropbox-API-Arg': JSON.stringify({path: FILE_PATH}),
      },
    });
    if (r.status === 409) return null;  // ファイル無し(初回)
    if (!r.ok) throw new Error('pull失敗 HTTP ' + r.status);
    const text = await r.text();
    return JSON.parse(text);
  }

  async function pushProgress(p) {
    const token = await getAccessToken();
    const r = await fetch('https://content.dropboxapi.com/2/files/upload', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/octet-stream',
        'Dropbox-API-Arg': JSON.stringify({
          path: FILE_PATH,
          mode: 'overwrite',
          mute: true,
        }),
      },
      body: JSON.stringify(p),
    });
    if (!r.ok) throw new Error('push失敗 HTTP ' + r.status);
    settings.dbxLastSync = new Date().toISOString();
    settings.dbxLastError = null;
    saveSettings(settings);
    return true;
  }

  // 起動時の同期: Dropbox側が新しければ取得して上書き
  async function syncOnStartup() {
    if (!settings.dbxSyncEnabled || !settings.dbxRefreshToken) return false;
    try {
      const remote = await pullProgress();
      const local = loadProgress();
      if (!remote) {
        // 初回: ローカルをpush
        await pushProgress(local);
        return true;
      }
      const localT = local.updatedAt || 0;
      const remoteT = remote.updatedAt || 0;
      if (remoteT > localT) {
        // リモートが新しい → ローカル上書き(タイムスタンプは保持)
        saveProgress(remote, {preserveTimestamp: true, skipSync: true});
        settings.dbxLastSync = new Date().toISOString();
        saveSettings(settings);
        return 'pulled';
      } else if (localT > remoteT) {
        await pushProgress(local);
        return 'pushed';
      } else {
        settings.dbxLastSync = new Date().toISOString();
        saveSettings(settings);
        return 'unchanged';
      }
    } catch (e) {
      settings.dbxLastError = '同期失敗: ' + e.message;
      saveSettings(settings);
      console.warn('[sync] startup failed:', e.message);
      return false;
    }
  }

  function disconnect() {
    settings.dbxRefreshToken = null;
    settings.dbxSyncEnabled = false;
    settings.dbxLastSync = null;
    settings.dbxLastError = null;
    accessToken = null;
    saveSettings(settings);
  }

  return { startLogin, handleRedirect, pullProgress, pushProgress, syncOnStartup, disconnect };
})();

// ============================================================
// プレイヤーレベル (XP)
// ============================================================
const XP_CORRECT = 10, XP_WRONG = 3;
// 連続正解コンボ: 正解で+1ずつ蓄積、不正解で-COMBO_DECAY(急減衰)。0未満にはならない(マイナスボーナスなし)。
//   各正解のXP = XP_CORRECT + min(combo-1, COMBO_CAP-1)*COMBO_STEP
const COMBO_STEP = 2, COMBO_CAP = 10, COMBO_DECAY = 3;
// レベルLに到達するのに必要な累積XP = 150*(L-1)^2.3 (急峻な曲線・気長な育成)
//   Lv2=150 / Lv5≈3,638 / Lv10≈23,488 / Lv20≈130,986 / Lv30≈346,423 / Lv50≈1.16M / Lv100≈5.84M
//   1問+10XP想定(1セッション概ね70-93XP)。序盤は数セッション、中盤以降は1レベルに数時間〜数日。
//   レベルは事実上カンストせず、はるか先(Lv100+)まで称号を用意。
function xpForLevel(L) { return Math.round(150 * Math.pow(Math.max(0, L - 1), 2.3)); }
// xpForLevel と必ず整合する逆算 (レベルは最大でも~100程度なので軽量ループ)
function levelFromXp(xp) {
  let L = 1;
  while (xpForLevel(L + 1) <= xp) L++;
  return L;
}
function levelTitle(lvl) {
  if (lvl < 3)   return '耳ならし';
  if (lvl < 5)   return 'リスナー見習い';
  if (lvl < 7)   return 'かけ出しリスナー';
  if (lvl < 10)  return '初級リスナー';
  if (lvl < 13)  return '中級リスナー';
  if (lvl < 16)  return '中堅リスナー';
  if (lvl < 20)  return '上級リスナー';
  if (lvl < 25)  return 'リスニングマスター';
  if (lvl < 30)  return '熟練リスナー';
  if (lvl < 37)  return '達人リスナー';
  if (lvl < 45)  return '英語耳の使い手';
  if (lvl < 55)  return '音感の賢者';
  if (lvl < 65)  return '聴覚の求道者';
  if (lvl < 75)  return 'ヒアリングの達人';
  if (lvl < 85)  return '英語耳マイスター';
  if (lvl < 95)  return '超越リスナー';
  if (lvl < 110) return '伝説のリスナー';
  if (lvl < 130) return '神話のリスナー';
  return '音の神';
}

// --- 二つ名 (接頭辞): カテゴリ別の累計正解数で多段進化 ---
const CAT_SUBTITLES = {
  word:   [[20,'語彙の'],[100,'語彙巧者の'],[300,'語彙王の'],[700,'辞書いらずの'],[1500,'言葉の賢者の']],
  phrase: [[20,'熟語の'],[100,'熟語使いの'],[300,'連語マスターの'],[700,'句の達人の'],[1500,'熟達の']],
  idiom:  [[20,'慣用句の'],[100,'言い回し巧者の'],[300,'イディオムハンターの'],[700,'ネイティブ感覚の'],[1500,'慣用の賢者の']],
};
const ALLROUND_SUBTITLES = [[300,'万能の'],[700,'全方位の'],[1500,'完全網羅の']];
function tierFor(table, n) { let name = ''; for (const [th, t] of table) if (n >= th) name = t; return name; }
// 一番伸びているカテゴリの段位を二つ名に。3カテゴリすべて高水準なら万能系を優先。
function subTitle(p) {
  const cc = p.catCorrect || {};
  const w = cc.word || 0, ph = cc.phrase || 0, id = cc.idiom || 0;
  const allr = tierFor(ALLROUND_SUBTITLES, Math.min(w, ph, id));
  if (allr) return allr;
  const top = [['word', w], ['phrase', ph], ['idiom', id]].sort((a, b) => b[1] - a[1])[0];
  return tierFor(CAT_SUBTITLES[top[0]], top[1]);
}
// レベル称号 + 二つ名 を結合した完全な称号
function fullTitle(p, lvl) { return subTitle(p) + levelTitle(lvl); }

// --- 実績バッジ ---
function countMastered(p) {
  let n = 0; for (const k in (p.srs || {})) if (isMastered(p.srs[k])) n++; return n;
}
// 各バッジ: { id, icon, name, desc, test(p)->bool }
const BADGES = [
  // 品詞 (単語のみ品詞情報あり)
  { id: 'verb',   icon: '🏃', name: '動作の達人',     desc: '動詞を150問正解',   test: p => (p.posCorrect.VERB||0) >= 150 },
  { id: 'noun',   icon: '📦', name: '物の名の番人',   desc: '名詞を150問正解',   test: p => (p.posCorrect.NOUN||0) >= 150 },
  { id: 'adj',    icon: '🎨', name: '彩りの詩人',     desc: '形容詞を120問正解', test: p => (p.posCorrect.ADJ||0)  >= 120 },
  { id: 'adv',    icon: '✨', name: 'ニュアンスの匠', desc: '副詞を80問正解',    test: p => (p.posCorrect.ADV||0)  >= 80 },
  // CEFR (難易度帯)
  { id: 'b2',     icon: '🎓', name: '上級ハンター',   desc: 'B2語を100問正解',   test: p => (p.cefrCorrect.B2||0) >= 100 },
  { id: 'a1base', icon: '🧱', name: '基礎の鬼',       desc: 'A1語を200問正解',   test: p => (p.cefrCorrect.A1||0) >= 200 },
  // タグ (トピック・機能・スタイル)
  { id: 'biz',    icon: '💼', name: 'ビジネスエリート', desc: 'ビジネス系を100問正解', test: p => (p.tagCorrect.business||0) >= 100 },
  { id: 'travel', icon: '✈️', name: '旅人',           desc: '旅行系を80問正解',  test: p => (p.tagCorrect.travel||0) >= 80 },
  { id: 'food',   icon: '🍽', name: 'グルメ',         desc: '食べ物系を60問正解', test: p => (p.tagCorrect.food||0) >= 60 },
  { id: 'emotion',icon: '💗', name: '共感者',         desc: '感情系を60問正解',  test: p => (p.tagCorrect.emotion||0) >= 60 },
  { id: 'slang',  icon: '😎', name: 'ストリート',     desc: 'スラングを30問正解', test: p => (p.tagCorrect.slang||0) >= 30 },
  { id: 'polite', icon: '🎩', name: '礼儀の人',       desc: '丁寧表現を80問正解', test: p => (p.tagCorrect.polite||0) >= 80 },
  // モード (聴く vs 読む)
  { id: 'ear',    icon: '👂', name: '真の英語耳',     desc: '音声モードで300問正解', test: p => (p.audioCorrect||0) >= 300 },
  { id: 'eye',    icon: '⚡', name: '速読家',         desc: '表示モードで300問正解', test: p => (p.textCorrect||0) >= 300 },
  // プレイ実績
  { id: 'perfect',icon: '💯', name: 'パーフェクト',   desc: '1セッション全問連続正解(コンボ10)', test: p => (p.maxCombo||0) >= 10 },
  { id: 'streak7',icon: '🔥', name: '皆勤賞',         desc: '7日連続でプレイ',   test: p => (p.dayStreak||0) >= 7 },
  { id: 'streak30',icon:'🏅', name: '継続は力',       desc: '30日連続でプレイ',  test: p => (p.dayStreak||0) >= 30 },
  { id: 'master100',icon:'🏆',name: '百冠',           desc: '100項目をマスター', test: p => countMastered(p) >= 100 },
  { id: 'volume1k',icon: '⛰', name: '千本ノック',     desc: '累計1000問に回答',  test: p => (p.totalAnswered||0) >= 1000 },
  { id: 'volume5k',icon: '🗻', name: '万里の道',       desc: '累計5000問に回答',  test: p => (p.totalAnswered||0) >= 5000 },
  { id: 'morning',icon: '🌅', name: '早起き鳥',       desc: '朝(5〜10時)に20セッション', test: p => (p.morningSessions||0) >= 20 },
  { id: 'night',  icon: '🌙', name: '夜更かし族',     desc: '夜(22〜4時)に20セッション', test: p => (p.nightSessions||0) >= 20 },
  { id: 'devoted',icon: '📚', name: '努力家',         desc: '100セッション完了', test: p => (p.sessions||0) >= 100 },
];
function earnedBadgeIds(p) { return BADGES.filter(b => b.test(p)).map(b => b.id); }

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
// 実績バッジ一覧
// ============================================================
function renderBadgeShowcase(p) {
  const earned = new Set(p.badges || []);
  const got = BADGES.filter(b => earned.has(b.id)).length;
  const cells = BADGES.map(b => {
    const has = earned.has(b.id);
    return `<div title="${escapeHtml(b.name)}：${escapeHtml(b.desc)}" style="display:flex; flex-direction:column; align-items:center; gap:3px; padding:8px 4px; border-radius:8px; background:var(--panel2); opacity:${has ? 1 : 0.4};">
      <span style="font-size:1.5em; filter:${has ? 'none' : 'grayscale(1)'};">${b.icon}</span>
      <span class="small-text" style="text-align:center; line-height:1.2;">${escapeHtml(b.name)}</span>
    </div>`;
  }).join('');
  return `<details class="card badge-card">
    <summary>
      <span>🎖 実績バッジ</span>
      <span class="small-text" style="font-weight:normal;">${got} / ${BADGES.length} <span class="badge-chevron">▼</span></span>
    </summary>
    <div class="badge-grid">${cells}</div>
  </details>`;
}

// ============================================================
// ホーム画面
// ============================================================
function renderHome() {
  const progress = loadProgress();
  const accuracy = progress.totalAnswered > 0 ? Math.round((progress.totalCorrect / progress.totalAnswered) * 100) : 0;
  const lvl = levelFromXp(progress.xp || 0);
  const xpInto = (progress.xp || 0) - xpForLevel(lvl);
  const xpSpan = xpForLevel(lvl + 1) - xpForLevel(lvl);
  const xpPct = xpSpan > 0 ? Math.round(xpInto / xpSpan * 100) : 0;
  const levelCard = `
    <div class="card" style="padding:14px 18px;">
      <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:8px;">
        <span style="font-weight:bold; color:var(--accent); font-size:1.1em;">Lv.${lvl}</span>
        <span class="small-text">${escapeHtml(fullTitle(progress, lvl))}</span>
      </div>
      <div class="progress-bar"><div class="progress-fill" style="width:${xpPct}%"></div></div>
      <div class="small-text" style="text-align:right; margin-top:4px;">${xpInto} / ${xpSpan} XP（累計 ${progress.xp || 0}）</div>
    </div>`;
  const badgeShowcase = renderBadgeShowcase(progress);
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
    ${levelCard}
    ${badgeShowcase}
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
  state.sessionAnswers.push({
    itemId: target.id, correct,
    category: target.category, pos: target.pos || null, cefr: target.cefr || null,
    tags: target.tags || [], useAudio: isAudioMode(state.mode),
  });

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

  // XP / レベル / コンボ (回答順に再生してコンボボーナスを計算)
  let combo = 0, xpGained = 0, sessionMaxCombo = 0;
  state.sessionAnswers.forEach(a => {
    if (a.correct) {
      combo += 1;
      if (combo > sessionMaxCombo) sessionMaxCombo = combo;
      xpGained += XP_CORRECT + Math.min(combo - 1, COMBO_CAP - 1) * COMBO_STEP;
    } else {
      combo = Math.max(0, combo - COMBO_DECAY); // 急減衰・マイナスにはしない
      xpGained += XP_WRONG;
    }
  });
  const prevLevel = levelFromXp(p.xp || 0);
  p.xp = (p.xp || 0) + xpGained;
  const newLevel = levelFromXp(p.xp);
  state.sessionXpGained = xpGained;
  state.sessionMaxCombo = sessionMaxCombo;
  state.leveledUp = newLevel > prevLevel ? newLevel : 0;
  p.maxCombo = Math.max(p.maxCombo || 0, sessionMaxCombo);

  // カテゴリ/品詞/CEFR/タグ別の正解カウント + 音声/表示モード成績 + SRS更新
  if (!p.catCorrect) p.catCorrect = {}; if (!p.posCorrect) p.posCorrect = {};
  if (!p.cefrCorrect) p.cefrCorrect = {}; if (!p.tagCorrect) p.tagCorrect = {};
  state.sessionAnswers.forEach(a => {
    if (a.correct) {
      if (a.category) p.catCorrect[a.category] = (p.catCorrect[a.category] || 0) + 1;
      if (a.pos)      p.posCorrect[a.pos]      = (p.posCorrect[a.pos] || 0) + 1;
      if (a.cefr)     p.cefrCorrect[a.cefr]    = (p.cefrCorrect[a.cefr] || 0) + 1;
      (a.tags || []).forEach(t => { p.tagCorrect[t] = (p.tagCorrect[t] || 0) + 1; });
    }
    if (a.useAudio) { p.audioAnswered = (p.audioAnswered||0)+1; if (a.correct) p.audioCorrect = (p.audioCorrect||0)+1; }
    else            { p.textAnswered  = (p.textAnswered||0)+1;  if (a.correct) p.textCorrect  = (p.textCorrect||0)+1; }
    const key = `${a.itemId}::${state.mode}`;
    p.srs[key] = sm2Update(p.srs[key] || newSrsState(), a.correct ? 4 : 2);
  });

  // 連続プレイ日数
  const td = today();
  if (p.lastPlayDate !== td) {
    const yd = (() => { const d = new Date(); d.setDate(d.getDate() - 1);
      return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; })();
    p.dayStreak = (p.lastPlayDate === yd) ? (p.dayStreak || 0) + 1 : 1;
    p.lastPlayDate = td;
  }
  // 時間帯
  const hr = new Date().getHours();
  if (hr >= 5 && hr < 10) p.morningSessions = (p.morningSessions || 0) + 1;
  if (hr >= 22 || hr < 4) p.nightSessions = (p.nightSessions || 0) + 1;

  // 実績バッジ判定 (新規解除分を結果画面で表示)
  const prevBadges = new Set(p.badges || []);
  const earned = earnedBadgeIds(p);
  state.newBadges = earned.filter(id => !prevBadges.has(id));
  p.badges = earned;

  p.history.unshift({ date: td, mode: state.mode, score: state.sessionScore, total: state.sessionAnswers.length });
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

  // XP / レベル表示
  const lvl = levelFromXp(progress.xp);
  const into = progress.xp - xpForLevel(lvl);
  const span = xpForLevel(lvl + 1) - xpForLevel(lvl);
  const pctXp = span > 0 ? Math.round(into / span * 100) : 0;
  const levelUpLine = state.leveledUp
    ? `<p class="center" style="color:var(--accent); font-weight:bold; font-size:1.15em; margin-bottom:8px;">🎉 レベルアップ！ Lv.${state.leveledUp} ${escapeHtml(fullTitle(progress, state.leveledUp))}</p>`
    : '';
  const comboLine = (state.sessionMaxCombo || 0) >= 3
    ? `<p class="center small-text" style="margin-bottom:6px;">🔥 最大 ${state.sessionMaxCombo} コンボ</p>`
    : '';
  const newBadgeLine = (state.newBadges && state.newBadges.length)
    ? `<p class="center" style="color:var(--accent); font-weight:bold; margin:8px 0;">🎖 実績解除！ ${state.newBadges.map(id => { const b = BADGES.find(x => x.id === id); return b ? escapeHtml(b.icon + ' ' + b.name) : ''; }).join(' / ')}</p>`
    : '';
  const xpBlock = `
    <div style="margin:14px 0 4px;">
      <p class="center" style="color:var(--accent); font-weight:bold; margin-bottom:6px;">+${state.sessionXpGained || 0} XP</p>
      ${comboLine}
      ${levelUpLine}
      ${newBadgeLine}
      <div style="display:flex; justify-content:space-between; font-size:0.8em; color:var(--muted); margin-bottom:4px;">
        <span>Lv.${lvl} ${escapeHtml(fullTitle(progress, lvl))}</span><span>${into} / ${span} XP</span>
      </div>
      <div class="progress-bar"><div class="progress-fill" style="width:${pctXp}%"></div></div>
    </div>`;
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
      <div class="small-text" style="white-space:nowrap;">${interval|0}日後<br>${escapeHtml(nextDate || '')}</div></div>`;
  }).join('');

  app.innerHTML = `
    <h1>セッション完了</h1>
    <div class="card">
      <div class="result-score">${score}/${total}</div>
      <p class="result-message">${msg} (${pct}%)</p>
      ${xpBlock}
      <p class="small-text center" style="margin:14px 0 16px;">正解 → 次の復習が先に延長 / 不正解 → 翌日に再出題</p>
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
    // 防御: 外部由来JSON(インポート/同期)の文字列フィールドは必ずエスケープ
    const dateStr = escapeHtml(h.date);
    const modeStr = MODE_LABELS_SHORT[h.mode] || escapeHtml(String(h.mode || ''));
    return `<tr><td>${dateStr}</td><td>${modeStr}</td><td>${h.score|0}/${h.total|0}</td><td>${pct}%</td></tr>`;
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
function renderDropboxCard() {
  const connected = !!settings.dbxRefreshToken;
  const lastSync = settings.dbxLastSync ? new Date(settings.dbxLastSync).toLocaleString('ja-JP') : 'なし';
  const errLine = settings.dbxLastError ? `<p class="small-text" style="color:var(--bad); margin-top:6px;">⚠ ${escapeHtml(settings.dbxLastError)}</p>` : '';
  if (!connected) {
    return `<div class="card">
      <h3 style="margin-bottom:8px; color:var(--accent);">☁️ Dropbox 同期 (3端末で進捗共有)</h3>
      <p class="small-text" style="margin-bottom:10px; line-height:1.6;">
        進捗を自分のDropbox(アプリ専用フォルダ)に保存して、PC/携帯で共有します。
        鍵はこの端末ブラウザ内のみに保存され、コードや公開サイトには一切含まれません。
      </p>
      <p class="small-text" style="margin-bottom:6px;">App key (Dropbox App Console で取得):</p>
      <input type="text" id="dbx-app-key" value="${escapeHtml(settings.dbxAppKey || '')}" placeholder="例: ab12cd34ef56gh7"
        style="width:100%; padding:9px 11px; background:var(--panel2); color:var(--text); border:1px solid var(--border); border-radius:6px; font-family:monospace; font-size:0.88em;">
      <button class="next-btn" id="dbx-connect" style="margin-top:10px;">🔗 Dropboxと接続</button>
      ${errLine}
    </div>`;
  }
  return `<div class="card">
    <h3 style="margin-bottom:8px; color:var(--accent);">☁️ Dropbox 同期</h3>
    <p style="color:var(--good); font-size:0.92em; margin-bottom:6px;">✓ 接続済み</p>
    <p class="small-text" style="margin-bottom:10px;">最終同期: ${lastSync}</p>
    <div class="setting-row" style="border:none; padding:6px 0;">
      <div><div class="setting-label">自動同期</div><div class="setting-desc">起動時に取得・保存時に送信</div></div>
      <label class="switch"><input type="checkbox" id="dbx-toggle" ${settings.dbxSyncEnabled?'checked':''}><span class="slider"></span></label>
    </div>
    <button class="next-btn" id="dbx-sync-now" style="background:var(--panel2); color:var(--text); margin-top:8px;">🔄 いま同期する</button>
    <button class="next-btn" id="dbx-disconnect" style="background:var(--bad-bg); color:var(--bad-text); margin-top:8px;">🔌 切断 (この端末から鍵を削除)</button>
    ${errLine}
  </div>`;
}

function bindDropboxEvents() {
  const connectBtn = document.getElementById('dbx-connect');
  if (connectBtn) connectBtn.addEventListener('click', () => {
    const key = (document.getElementById('dbx-app-key').value || '').trim();
    if (!key) { alert('App keyを入力してください'); return; }
    Dropbox.startLogin(key).catch(e => alert('接続失敗: ' + e.message));
  });
  const toggle = document.getElementById('dbx-toggle');
  if (toggle) toggle.addEventListener('change', e => { settings.dbxSyncEnabled = e.target.checked; saveSettings(settings); });
  const syncBtn = document.getElementById('dbx-sync-now');
  if (syncBtn) syncBtn.addEventListener('click', async () => {
    syncBtn.disabled = true; syncBtn.textContent = '同期中…';
    const r = await Dropbox.syncOnStartup();
    syncBtn.disabled = false;
    render();
    alert(r ? '同期しました (' + r + ')' : '同期に失敗しました');
  });
  const dis = document.getElementById('dbx-disconnect');
  if (dis) dis.addEventListener('click', () => {
    if (confirm('この端末からDropbox接続を解除します。進捗データは消えません。')) {
      Dropbox.disconnect(); render();
    }
  });
}

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
    ${renderDropboxCard()}
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
  bindDropboxEvents();
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

// Dropbox 起動シーケンス: OAuthリダイレクトの戻り処理 → 自動同期
(async () => {
  if (location.search.includes('code=')) {
    const ok = await Dropbox.handleRedirect();
    if (ok) {
      alert('Dropboxと接続しました');
      await Dropbox.syncOnStartup();
      render();
      return;
    }
  }
  if (settings.dbxSyncEnabled && settings.dbxRefreshToken) {
    Dropbox.syncOnStartup().then(r => { if (r === 'pulled') render(); });
  }
})();

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
    DOCS_HTML.parent.mkdir(parents=True, exist_ok=True)
    DOCS_HTML.write_text(html, encoding="utf-8")
    print(f"[build_html] Generated: {OUT_HTML}")
    print(f"[build_html]            {DOCS_HTML}")
    print(f"[build_html] Size: {OUT_HTML.stat().st_size / 1024:.1f} KB")
    print(f"[build_html] words: {len(words)} / idioms: {len(idioms)} / phrases: {len(phrases)}")


if __name__ == "__main__":
    main()
