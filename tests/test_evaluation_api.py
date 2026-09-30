from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from nebula.core.config import Settings
from tests.support import admin_headers, configured_app


def test_router_evaluation_serves_the_replay_file(tmp_path: Path) -> None:
    replay = tmp_path / "replay.json"
    replay.write_text(json.dumps({"version": 1, "rows": [], "operating_points": []}))
    with configured_app(NEBULA_ROUTER_REPLAY_PATH=str(replay)) as app:
        with TestClient(app) as client:
            ok = client.get("/v1/admin/evaluation/router", headers=admin_headers())
            unauthorised = client.get("/v1/admin/evaluation/router")

    assert ok.status_code == 200 and ok.json()["version"] == 1
    assert unauthorised.status_code in (401, 403)


def test_router_evaluation_is_404_without_a_replay_file(tmp_path: Path) -> None:
    with configured_app(NEBULA_ROUTER_REPLAY_PATH=str(tmp_path / "missing.json")) as app:
        with TestClient(app) as client:
            response = client.get("/v1/admin/evaluation/router", headers=admin_headers())

    assert response.status_code == 404
    assert "scripts.router.train" in response.json()["detail"]


def test_the_packaged_replay_matches_the_artifact() -> None:
    settings = Settings()
    replay = json.loads(Path(settings.router_replay_path).read_text())
    artifact = json.loads(Path(settings.learned_router_path).read_text())
    assert replay["operating_points"] == artifact["operating_points"]
    assert len(replay["rows"]) == 1250
