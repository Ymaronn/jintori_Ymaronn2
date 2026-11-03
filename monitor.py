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


def is_number_list(value):
    return (
        isinstance(value, list)
        and len(value) > 0
        and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in value)
    )


def fetch_state():
    req = urllib.request.Request(
        URL, headers={"User-Agent": "jintori-members-logger/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        data = json.loads(res.read().decode("utf-8"))

    if not isinstance(data, dict):
        raise ValueError("JSONの形式が想定と違います")

    members = data.get("members")
    if not is_number_list(members):
        raise ValueError("members が数値の配列として見つかりません")

    today = data.get("today")
    act = today.get("act") if isinstance(today, dict) else None
    if not is_number_list(act):
        raise ValueError("today.act が数値の配列として見つかりません")

    return {
        "day": data.get("day"),
        "players": today.get("players"),
        "takes": today.get("takes"),
        "members": members,
        "act": act,
    }


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
    state = fetch_state()
    records = load_records()

    previous = records[-1] if records else None
    if (
        previous
        and previous.get("members") == state["members"]
        and previous.get("act") == state["act"]
    ):
        print("変化なし")
        return

    record = {
        "time": datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "day": state["day"],
        "players": state["players"],
        "takes": state["takes"],
        "members": state["members"],
        "act": state["act"],
    }
    records.append(record)
    save_records(records)
    print(
        f"記録しました: {len(records)}件目 "
        f"(members {len(state['members'])}要素 / act {len(state['act'])}要素)"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)
