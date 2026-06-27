"""Tests for validation + quarantine of source features."""

from __future__ import annotations

from typing import Any

from migration_pipeline.validate import validate_features


def _feature(geometry: Any = "default", **properties: Any) -> dict[str, Any]:
    props: dict[str, Any] = {
        "ChapterID": "CA-0355",
        "University_Chapter": "Cal Poly",
        "City": "San Luis Obispo",
        "State": "CA",
    }
    props.update(properties)
    geom = {"type": "Point", "coordinates": [-120.66, 35.27]} if geometry == "default" else geometry
    return {"type": "Feature", "geometry": geom, "properties": props}


def test_valid_record_passes() -> None:
    result = validate_features([_feature()])

    assert len(result.valid) == 1
    assert result.quarantined == []
    assert result.valid[0].chapter_id == "CA-0355"


def test_missing_chapter_id_is_quarantined_with_raw_and_reason() -> None:
    bad = _feature(ChapterID="")
    result = validate_features([bad])

    assert result.valid == []
    assert len(result.quarantined) == 1
    assert result.quarantined[0].raw is bad
    assert "chapter_id" in result.quarantined[0].reason


def test_out_of_scope_state_is_quarantined() -> None:
    result = validate_features([_feature(State="TX")])

    assert result.valid == []
    assert "state" in result.quarantined[0].reason.lower()


def test_out_of_range_coordinates_are_quarantined() -> None:
    bad_geometry = {"type": "Point", "coordinates": [-120.0, 200.0]}
    result = validate_features([_feature(geometry=bad_geometry)])

    assert result.valid == []
    assert "latitude" in result.quarantined[0].reason.lower()


def test_null_coordinates_are_allowed() -> None:
    result = validate_features([_feature(geometry=None)])

    assert len(result.valid) == 1
    assert result.valid[0].longitude is None
    assert result.valid[0].latitude is None


def test_mixed_batch_partitions_valid_and_quarantined() -> None:
    result = validate_features([_feature(), _feature(ChapterID=""), _feature(State="NV")])

    assert len(result.valid) == 1
    assert len(result.quarantined) == 2
