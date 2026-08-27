import io
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent ambient environment from influencing CLI option resolution."""
    for var in ('DUMPTHINGS_APIURL', 'DUMPTHINGS_TOKEN', 'QRI_RECORD_CACHE'):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def api_url() -> str:
    return 'https://api.example.test'


@pytest.fixture
def run_callback(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    """Run a Click callback with controlled stdin and captured stdout/stderr."""

    def _run(callback: Any, input_text: str = '', **kwargs: Any) -> Any:
        monkeypatch.setattr('sys.stdin', io.StringIO(input_text))
        callback(**kwargs)
        return capsys.readouterr()

    return _run


@pytest.fixture
def write_pid_file(tmp_path: Path):
    """Create PID files for tests."""

    def _write(
        name: str,
        pids: Sequence[str] | None = None,
        content: str | None = None,
    ) -> Path:
        path = tmp_path / name
        if content is None:
            content = ''.join(f'{pid}\n' for pid in (pids or []))
        path.write_text(content, encoding='utf-8')
        return path

    return _write
