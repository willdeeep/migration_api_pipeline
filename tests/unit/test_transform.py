"""Tests for transform: raw ArcGIS GeoJSON feature -> ChapterRecord."""

from __future__ import annotations

from typing import Any

from migration_pipeline.transform import to_chapter_record


def _feature(**properties: Any) -> dict[str, Any]:
    """Build a GeoJSON feature with sensible defaults, overridable per test."""
    props: dict[str, Any] = {
        "OBJECTID": 19,
        "University_Chapter": "California Polytechnic State University",
        "City": "San Luis Obispo",
        "State": "CA",
        "ChapterID": "CA-0355",
        "MEVR_RD": "Derek Swindall",
    }
    props.update(properties)
    return {
        "type": "Feature",
        "id": props["OBJECTID"],
        "geometry": {"type": "Point", "coordinates": [-120.663191, 35.274309]},
        "properties": props,
    }


def test_maps_all_fields_from_geojson_feature() -> None:
    record = to_chapter_record(_feature())

    assert record.chapter_id == "CA-0355"
    assert record.chapter_name == "California Polytechnic State University"
    assert record.city == "San Luis Obispo"
    assert record.state == "CA"
    assert record.longitude == -120.663191
    assert record.latitude == 35.274309


def test_missing_geometry_yields_null_coordinates() -> None:
    feature = _feature()
    feature["geometry"] = None

    record = to_chapter_record(feature)

    assert record.longitude is None
    assert record.latitude is None


def test_missing_optional_fields_become_none() -> None:
    feature = _feature()
    del feature["properties"]["City"]
    del feature["properties"]["University_Chapter"]

    record = to_chapter_record(feature)

    assert record.city is None
    assert record.chapter_name is None
    assert record.chapter_id == "CA-0355"


def test_state_is_normalised_to_upper_and_stripped() -> None:
    record = to_chapter_record(_feature(State=" ca "))

    assert record.state == "CA"


def test_blank_optional_strings_become_none() -> None:
    record = to_chapter_record(_feature(City="   "))

    assert record.city is None


def test_coordinates_are_coerced_to_float() -> None:
    feature = _feature()
    feature["geometry"]["coordinates"] = ["-120.5", "35.5"]

    record = to_chapter_record(feature)

    assert record.longitude == -120.5
    assert record.latitude == 35.5
