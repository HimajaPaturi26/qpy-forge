import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["Q2PY_DB"] = str(Path("/tmp/q2py-test.sqlite"))

from q2py.api import app  # noqa: E402
from q2py.corpus import load_cases  # noqa: E402
from q2py.metrics import measure  # noqa: E402
from q2py.sandbox import validate_generated  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_translate_and_history(client: TestClient) -> None:
    response = client.post("/api/v1/translate", json={"source": "2*3+4"})
    assert response.status_code == 200
    body = response.json()
    assert body["support"] == "supported"
    assert "q.mul" in body["python"]
    assert body["oracle"]["status"] == "oracle-unavailable"
    history = client.get("/api/v1/history")
    assert history.status_code == 200
    assert history.json()["events"]


def test_refusal(client: TestClient) -> None:
    response = client.post("/api/v1/translate", json={"source": "1|2"})
    assert response.status_code == 200
    body = response.json()
    assert body["support"] == "unsupported"
    assert body["python"] == ""


def test_validate_case(client: TestClient) -> None:
    response = client.post("/api/v1/validate", json={"source": "2*3+4", "case_id": "arith-rtl-mul-add"})
    assert response.status_code == 200
    assert response.json()["matched"] is True


def test_sandbox_rejects_import() -> None:
    source = "import os\n\ndef q2py_program():\n    return os.getcwd()\n"
    problems = validate_generated(source)
    assert problems


def test_corpus_provenance() -> None:
    cases = load_cases()
    assert cases
    for case in cases:
        assert case["provenance"].startswith("hand-authored")
        assert "translator" not in case["provenance"] or "not produced by the translator" in case["provenance"]


def test_measured_accuracy_is_a_ratio() -> None:
    report = measure("holdout")
    assert report["sample_size"] == 95
    assert report["semantic_accuracy"] == report["successes"] / report["sample_size"]
    assert report["oracle"]["status"] == "oracle-unavailable"
    assert report["oracle_match_rate"] is None
    assert report["target_met"] is (report["semantic_accuracy"] >= report["target"])
