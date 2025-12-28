from importlib import util
from pathlib import Path


def test_app_instance() -> None:
    main_path = Path(__file__).resolve().parents[1] / "main.py"
    spec = util.spec_from_file_location("main", main_path)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.app.title == "ChapterVerse API"
