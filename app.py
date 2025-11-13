"""Simple Flask API exposing coverage planning and coverage tracking utilities."""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

from flask import Flask, jsonify, request

from coverage_planner import (
    compute_track_coverage,
    coverage_plan_to_geojson,
    generate_coverage_plan,
)

Coordinate = Tuple[float, float]

app = Flask(__name__)


@app.after_request
def _apply_cors_headers(response):  # pragma: no cover - trivial header hook
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response


def _parse_coordinate_pair(value: Iterable[float]) -> Coordinate:
    try:
        lon, lat = value  # type: ignore[misc]
    except (TypeError, ValueError):
        raise ValueError("Each coordinate must be an iterable of two numbers") from None

    try:
        return float(lon), float(lat)
    except (TypeError, ValueError):  # pragma: no cover - defensive usage
        raise ValueError("Coordinate values must be numeric") from None


def _parse_coordinates(payload: Sequence[Iterable[float]], name: str) -> List[Coordinate]:
    if not isinstance(payload, (list, tuple)) or len(payload) < 3:
        raise ValueError(f"'{name}' must be a list with at least three [lon, lat] pairs")
    return [_parse_coordinate_pair(item) for item in payload]


def _parse_holes(payload, name: str = "holes") -> List[List[Coordinate]]:
    if payload in (None, [], ()):  # type: ignore[comparison-overlap]
        return []
    if not isinstance(payload, (list, tuple)):
        raise ValueError(f"'{name}' must be a list of hole polygons")
    holes: List[List[Coordinate]] = []
    for idx, hole in enumerate(payload):
        try:
            holes.append(_parse_coordinates(hole, f"{name}[{idx}]"))
        except ValueError as exc:
            raise ValueError(str(exc)) from None
    return holes


def _json_error(message: str, status: int = 400):
    response = jsonify({"error": message})
    response.status_code = status
    return response


@app.route("/health", methods=["GET"])
def health():  # pragma: no cover - trivial route
    return jsonify({"status": "ok"})


@app.route("/plan-coverage", methods=["POST"])
def plan_coverage():
    payload = request.get_json(force=True, silent=True)
    if payload is None:
        return _json_error("Invalid or missing JSON payload")

    try:
        boundary = _parse_coordinates(payload["boundary"], "boundary")
    except KeyError:
        return _json_error("'boundary' field is required")
    except ValueError as exc:
        return _json_error(str(exc))

    try:
        spray_width = float(payload.get("spray_width", 0))
    except (TypeError, ValueError):
        return _json_error("'spray_width' must be a number")
    if spray_width <= 0:
        return _json_error("'spray_width' must be greater than zero")

    try:
        holes = _parse_holes(payload.get("holes"))
    except ValueError as exc:
        return _json_error(str(exc))

    try:
        angle_resolution = float(payload.get("angle_resolution", 5.0))
    except (TypeError, ValueError):
        return _json_error("'angle_resolution' must be a number")

    include_deadhead = bool(payload.get("include_deadhead", True))

    try:
        plan = generate_coverage_plan(
            boundary,
            spray_width=spray_width,
            holes=holes if holes else None,
            angle_resolution=angle_resolution,
        )
    except Exception as exc:  # pragma: no cover - passes through from planner
        return _json_error(str(exc))

    summary = {
        "orientation_deg": plan.orientation_deg,
        "spray_width": plan.spray_width,
        "passes": plan.num_passes,
        "total_path_length": plan.total_path_length,
        "spray_path_length": plan.spray_path_length,
        "deadhead_path_length": plan.deadhead_length,
    }

    geojson_payload = coverage_plan_to_geojson(
        plan,
        boundary=boundary,
        holes=holes if holes else None,
        include_deadhead=include_deadhead,
    )

    return jsonify({
        "summary": summary,
        "geojson": geojson_payload,
    })


@app.route("/track-coverage", methods=["POST"])
def track_coverage():
    payload = request.get_json(force=True, silent=True)
    if payload is None:
        return _json_error("Invalid or missing JSON payload")

    try:
        track = [_parse_coordinate_pair(coord) for coord in payload["track"]]
    except KeyError:
        return _json_error("'track' field is required")
    except ValueError as exc:
        return _json_error(str(exc))

    if len(track) < 2:
        return _json_error("'track' must contain at least two coordinates")

    try:
        spray_width = float(payload.get("spray_width", 0))
    except (TypeError, ValueError):
        return _json_error("'spray_width' must be a number")
    if spray_width <= 0:
        return _json_error("'spray_width' must be greater than zero")

    boundary = None
    holes = None
    if "boundary" in payload:
        try:
            boundary = _parse_coordinates(payload["boundary"], "boundary")
        except ValueError as exc:
            return _json_error(str(exc))
        try:
            holes = _parse_holes(payload.get("holes"))
        except ValueError as exc:
            return _json_error(str(exc))

    try:
        stats = compute_track_coverage(
            track,
            spray_width=spray_width,
            farm_boundary=boundary,
            holes=holes if holes else None,
            include_geometries=False,
        )
    except Exception as exc:  # pragma: no cover - from coverage helper
        return _json_error(str(exc))

    return jsonify(stats)


if __name__ == "__main__":  # pragma: no cover
    app.run(host="0.0.0.0", port=5000, debug=True)


