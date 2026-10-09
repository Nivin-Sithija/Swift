"""Run the authenticated JMeter plan using credentials from the final Newman flow."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent


def response_json(execution: dict) -> dict:
    stream = execution["response"]["stream"]
    raw = bytes(stream["data"]) if isinstance(stream, dict) else stream.encode()
    return json.loads(raw)


def main() -> None:
    report = json.loads((HERE / "newman-final.json").read_text())
    executions = {item["item"]["name"]: item for item in report["run"]["executions"]}
    token = response_json(executions["Register customer"])["access_token"]
    ticket = response_json(executions["Create support ticket"])["id"]
    properties = f"token={token}\nticket={ticket}\n"
    with tempfile.NamedTemporaryFile("w", suffix=".properties") as handle:
        handle.write(properties)
        handle.flush()
        subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", f"{HERE}:/tests",
                "-v", f"{handle.name}:/load.properties:ro",
                "justb4/jmeter:5.5",
                "-n", "-q", "/load.properties",
                "-t", "/tests/business_load_test.jmx",
                "-l", "/tests/jmeter-business-final.jtl",
                "-e", "-o", "/tests/jmeter-business-final-report",
            ],
            check=True,
        )


if __name__ == "__main__":
    main()
