import datetime
import json
import os
import pathlib
import sys
import urllib.request

URL = os.environ.get(
    "JINTORI_URL",
    "https://keigamesstudio.com/jintori-api/state?v=2a8be94d",
)
OUT = pathlib.Path(os.environ.get("JINTORI_OUT", "data/jintori_members.json"))


def fetch_members():
    req = urllib.request.Request(
        URL, headers={"User-Agent": "jintori-members-logger/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        data = json.loads(res.read().decode("utf-8"))

    members = data.get("members") if isinstance(data, dict) else None
    if not isinstance(members, list) or not members:
        raise ValueError("members が配列として見つかりません")
    if not all(isinstance(x, (int, float)) for x in members):
        raise ValueError("members に数値以外が含まれています")
    return members


def load_records():
    if not OUT.exists():
        return []
    return json.loads(OUT.read_text(encoding="utf-8"))


def save_records(records):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(r, separators=(",", ":"), ensure_ascii=False) for r in records
    ]
    OUT.write_text("[\n" + ",\n".join(lines) + "\n]\n", encoding="utf-8")


def main():
    members = fetch_members()
    records = load_records()

    if records and records[-1].get("members") == members:
        print("変化なし")
        return

    records.append(
        {
            "time": datetime.datetime.now(datetime.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "members": members,
        }
    )
    save_records(records)
    print(f"記録しました: {len(records)}件目 ({len(members)}要素)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)
