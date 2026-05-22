"""Golden dataset loader.

Datasets live as JSON or YAML files under eval_datasets/. We accept both so authors
can pick the format that fits the dataset shape. JSON is easier to generate
programmatically; YAML is easier to hand-edit.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from .models import EvalDataset

DEFAULT_DATASETS_DIR = Path(__file__).resolve().parents[3] / "eval_datasets"


def load_dataset(path: str | Path) -> EvalDataset:
    """Load and validate an EvalDataset from a JSON or YAML file."""
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    if p.suffix.lower() in {".yml", ".yaml"}:
        data = yaml.safe_load(raw)
    else:
        data = json.loads(raw)
    return EvalDataset.model_validate(data)


def list_datasets(directory: Path = DEFAULT_DATASETS_DIR) -> list[Path]:
    """Return every dataset file in the standard datasets directory."""
    if not directory.exists():
        return []
    return sorted(
        p for p in directory.iterdir() if p.suffix.lower() in {".json", ".yml", ".yaml"}
    )
