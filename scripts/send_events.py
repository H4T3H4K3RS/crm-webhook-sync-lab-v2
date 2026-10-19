"""Отправка сценария webhook-событий в запущенный сервис (для демонстрации в видеоотчёте).

Пример:
    python scripts/send_events.py events/scenarios/03_out_of_order.json
    python scripts/send_events.py events/scenarios/02_duplicate_delivery.json --url http://127.0.0.1:8000
"""

import argparse
import json
from pathlib import Path

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("scenario", type=Path, help="JSON-файл из events/scenarios")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    scenario = json.loads(args.scenario.read_text(encoding="utf-8"))
    print(f"Сценарий: {scenario['description']}\n")

    with httpx.Client(base_url=args.url) as client:
        for i, (event, expected) in enumerate(
            zip(scenario["events"], scenario["expected_results"]), start=1
        ):
            response = client.post("/webhooks/crm", json=event)
            got = response.json().get("result", response.status_code)
            mark = "OK " if got == expected else "ERR"
            print(
                f"[{mark}] #{i} {event['event_id']:<22} v{event['version']} "
                f"{event['status']:<13} -> {got} (ожидалось: {expected})"
            )

        print("\nИтоговое состояние:")
        for final in scenario["expected_final_state"]:
            deal = client.get(f"/deals/{final['deal_id']}").json()
            print(f"  {final['deal_id']}: {deal}  (ожидалось: {final['status']} v{final['version']})")


if __name__ == "__main__":
    main()
