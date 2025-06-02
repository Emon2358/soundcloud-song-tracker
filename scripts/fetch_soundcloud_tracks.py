#!/usr/bin/env python3
# coding: utf-8

import os
import re
import sys
import requests
from bs4 import BeautifulSoup

README_PATH = "README.md"
START_MARKER = "<!--TRACK_LIST_START-->"
END_MARKER   = "<!--TRACK_LIST_END-->"

def fetch_track_urls(username: str) -> list[str]:
    """
    SoundCloud のモバイルページからすべてのトラックリンクをスクレイピングして返す。
    'https://m.soundcloud.com/{username}'
    """
    url = f"https://m.soundcloud.com/{username}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    track_urls = []
    # モバイルページでは、トラックへのリンクが <a href="/{username}/{slug}"> という形で出現する
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # 例: /username/track-slug という形式を抽出
        if re.fullmatch(rf"/{re.escape(username)}/[0-9A-Za-z_\-]+", href):
            full_url = f"https://soundcloud.com{href}"
            if full_url not in track_urls:
                track_urls.append(full_url)

    return track_urls

def update_readme(track_urls: list[str]):
    """
    README.md のマーカー間を最新の track_urls リストで置き換える。
    マークダウン形式で
      - [曲タイトル](URL)
    のリストを生成して挿入する。
    """
    if not os.path.isfile(README_PATH):
        print(f"Error: {README_PATH} が見つかりません。", file=sys.stderr)
        sys.exit(1)

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # マーカー行が両方存在するかチェック
    if START_MARKER not in content or END_MARKER not in content:
        print(f"Error: README.md にマーカー \"{START_MARKER}\" または \"{END_MARKER}\" が見つかりません。", file=sys.stderr)
        sys.exit(1)

    # トラックごとにタイトルを取得（必要に応じて HTTP リクエストを追加してページタイトルを取得してもよいが、
    # ここではリンクのみを出力する実装とする）
    # もしタイトルも欲しい場合は「requests.get(URL + '/oembed')」などを使う方法もある。
    # ここでは、とりあえず「URL の末尾」を曲名扱いし、Markdownリンクを作成する。
    markdown_lines = []
    for url in track_urls:
        # URL の末尾を slug としてタイトルにする
        title = url.rstrip("/").split("/")[-1]
        markdown_lines.append(f"- [{title}]({url})")

    new_section = "\n".join(markdown_lines) if markdown_lines else "（トラックが見つかりませんでした）"

    # マーカー間の置換
    pattern = re.compile(
        rf"({re.escape(START_MARKER)})(.*?)(\s*{re.escape(END_MARKER)})",
        re.DOTALL
    )
    replacement = rf"\1\n{new_section}\n\3"
    updated = pattern.sub(replacement, content)

    # 上書き保存
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)
    print(f"README.md を更新しました。{len(track_urls)} 件のトラックリンクを書き込み済み。")

def main():
    # GitHub Actions から渡される INPUT_USER を取得
    username = os.getenv("INPUT_SOUNDCLOUD_USERNAME", "").strip()
    if not username:
        print("Error: 環境変数 'INPUT_SOUNDCLOUD_USERNAME' に SoundCloud のユーザーネームを指定してください。", file=sys.stderr)
        sys.exit(1)

    print(f"SoundCloud ユーザーネーム: {username}")
    try:
        tracks = fetch_track_urls(username)
    except Exception as e:
        print(f"Error: トラック一覧の取得に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)

    update_readme(tracks)

if __name__ == "__main__":
    main()
