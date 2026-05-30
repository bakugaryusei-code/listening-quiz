#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SessionStart hook: GitHub(origin)と自動同期する。
- ローカルが遅れていて作業ツリーがクリーン → git pull --ff-only で自動取り込み
- 遅れ＋未コミット変更/分岐(divergence) → 自動取り込みを保留して警告（手動対応が必要）
- 未pushのコミットがある → push を促す
非エンジニアが別PCでこのフォルダを開いたとき、古いコピーを編集しないよう守るのが目的。
"""
import sys, json, subprocess
from pathlib import Path

# Windows既定(cp932)だと絵文字/日本語のprintで落ちるためUTF-8を強制
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# このスクリプトは .claude/hooks/ にあるので、リポジトリ直下は parents[2]
REPO = Path(__file__).resolve().parents[2]


def git(*args, timeout=30):
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True, text=True, timeout=timeout,
    )


def emit(system_message, context=None):
    """ユーザーへの表示(systemMessage) + Claudeへの文脈注入(additionalContext)。"""
    out = {"systemMessage": system_message, "suppressOutput": True}
    if context:
        out["hookSpecificOutput"] = {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    print(json.dumps(out, ensure_ascii=False))


def main():
    # stdin(SessionStartのJSON)は使わないが読み捨てる
    try:
        sys.stdin.read()
    except Exception:
        pass

    # gitリポジトリでなければ何もしない
    if not (REPO / ".git").exists():
        return

    # 1) 最新情報を取得
    try:
        fetched = git("fetch", "--quiet", "origin", timeout=40)
    except Exception:
        emit("⚠️ GitHubに接続できませんでした（オフライン？）。最新かどうか確認できていません。"
             "ネット接続を確認してから作業を始めてください。")
        return
    if fetched.returncode != 0:
        emit("⚠️ GitHubへのfetchに失敗しました。最新か確認できていません。")
        return

    # 2) 追跡ブランチ(upstream)が無ければスキップ
    if git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").returncode != 0:
        return

    # 3) ahead/behind と作業ツリーの状態
    counts = git("rev-list", "--left-right", "--count", "HEAD...@{u}")
    if counts.returncode != 0:
        return
    try:
        ahead, behind = (int(x) for x in counts.stdout.split())
    except ValueError:
        return
    # 追跡ファイルの未コミット変更のみを「dirty」とみなす(未追跡ファイルはff-only pullを妨げない)
    dirty = bool(git("status", "--porcelain", "--untracked-files=no").stdout.strip())

    # 4) 判定
    if behind == 0 and ahead == 0:
        return  # 最新。静かに何もしない

    if behind > 0 and ahead == 0 and not dirty:
        pull = git("pull", "--ff-only", "--quiet", timeout=90)
        if pull.returncode == 0:
            emit(
                f"✅ GitHubの最新を取り込みました（{behind}件の更新を同期）。最新の状態で作業できます。",
                context=(f"At SessionStart this repo was {behind} commit(s) behind origin and was "
                         "auto-synced via `git pull --ff-only`. Working tree is now current."),
            )
        else:
            emit(
                "⚠️ 自動同期(git pull)に失敗しました。編集を始める前に手動対応が必要かもしれません。",
                context=("Auto `git pull --ff-only` failed at SessionStart despite a clean tree. "
                         "Investigate and help the user resolve before editing. stderr: "
                         + (pull.stderr or "").strip()),
            )
        return

    if behind > 0 and (ahead > 0 or dirty):
        if ahead > 0 and dirty:
            reason = "ローカルに未コミットの変更があり、かつGitHubと分岐している"
        elif ahead > 0:
            reason = "ローカルとGitHubの両方に別々の変更がある（分岐している）"
        else:
            reason = "ローカルに未コミットの変更がある"
        emit(
            f"⚠️ GitHubに{behind}件の新しい更新がありますが、{reason}ため自動取り込みを保留しました。"
            "編集を始める前に整理が必要です（Claudeに「同期を整理して」と頼んでください）。",
            context=(f"At SessionStart: behind={behind}, ahead={ahead}, dirty={dirty}. "
                     "Auto-pull was skipped to avoid conflicts/data loss. BEFORE making edits, help the "
                     "non-engineer user reconcile: show local changes, commit or stash them, then pull. "
                     "Never blindly overwrite either side."),
        )
        return

    if ahead > 0 and behind == 0:
        emit(
            f"ℹ️ ローカルに未pushのコミットが{ahead}件あります（GitHubはこのPCより古い）。"
            "作業が一段落したらpushしてください。",
            context=(f"Repo is {ahead} commit(s) ahead of origin (unpushed). "
                     "Remind the user to push when convenient."),
        )


if __name__ == "__main__":
    main()
