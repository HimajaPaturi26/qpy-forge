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


def test_sandbox_rejects_globals_escape() -> None:
    from q2py.sandbox import InProcessExecutor, SubprocessExecutor

    source = (
        "def q2py_program():\n"
        '    bi = q.long.__globals__["__builtins__"]\n'
        '    return bi["open"]("/etc/hostname")\n'
    )
    assert validate_generated(source)
    for executor in (InProcessExecutor(), SubprocessExecutor()):
        result = executor.run(source)
        assert result.ok is False
        assert result.signal == "sandbox"


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
    signaled = [row for row in report["rows"] if row["declared_support"] == "supported" and not row["ran"]]
    assert [row["id"] for row in signaled] == ["length-signal"]
    assert signaled[0]["matched"] is True
    assert signaled[0]["comparison"] == "signal-match"
    assert signaled[0]["signal"] == "length"
    assert report["runtime_success_rate"] == (report["sample_size"] - 1) / report["sample_size"]
    assert report["signal_sample_size"] == 1
    assert report["value_sample_size"] == report["sample_size"] - 1
    assert report["value_match_rate"] == report["value_successes"] / report["value_sample_size"]


def test_corpus_hash_and_split_are_stable() -> None:
    from q2py.corpus import corpus_hash

    cases = load_cases()
    assert corpus_hash() == corpus_hash(cases)
    assert corpus_hash() == corpus_hash(load_cases())
    splits = {case["split"] for case in cases}
    assert splits == {"holdout", "dev", "coverage"}
    by_source: dict[str, set[str]] = {}
    for case in cases:
        by_source.setdefault(case["source"], set()).add(case["split"])
    leaked = {source: found for source, found in by_source.items() if len(found) > 1}
    assert leaked == {}
    ids = [case["id"] for case in cases]
    assert len(ids) == len(set(ids))
