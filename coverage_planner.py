"""Coverage path planning utilities for farm polygons.

This module provides helper functions to compute spray coverage paths for a
tractor that dispenses fertilizer/pesticide through a boom ("sprinkler") with a
fixed spray width.  It attempts to generate a boustrophedon (lawnmower)
coverage path that minimises overlap while covering the entire farm polygon,
including support for internal holes that must be skipped.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np

try:
    from shapely import affinity
    from shapely.geometry import LineString, MultiLineString, Polygon
except ModuleNotFoundError as exc:  # pragma: no cover - defensive, environment specific
    raise ModuleNotFoundError(
        "The 'shapely' package is required for coverage path planning. "
        "Install it with 'pip install shapely' (or use the provided virtual environment)."
    ) from exc

Coordinate = Tuple[float, float]


@dataclass(frozen=True)
class PathSegment:
    """Represents a contiguous path segment.

    Attributes:
        points: Ordered list of (lon, lat) coordinates describing the segment.
        spray_on: True if the sprayer should be active (covering ground) while
            travelling along this segment. False indicates a deadhead/relocation
            move where the boom should be shut off to avoid unwanted overlap.
    """

    points: List[Coordinate]
    spray_on: bool


@dataclass(frozen=True)
class CoveragePlan:
    """Full description of a computed coverage path."""

    segments: List[PathSegment]
    orientation_deg: float
    spray_width: float
    num_passes: int
    total_path_length: float
    spray_path_length: float
    deadhead_length: float


def _build_shapely_polygon(
    boundary: Sequence[Coordinate], holes: Optional[Sequence[Sequence[Coordinate]]] = None
) -> Polygon:
    if len(boundary) < 3:
        raise ValueError("Farm boundary must have at least 3 vertices")

    polygon = Polygon(boundary, holes=holes)
    if not polygon.is_valid:
        polygon = polygon.buffer(0)  # Attempt to fix self-intersections.

    if polygon.is_empty or not polygon.is_valid:
        raise ValueError("Unable to build a valid polygon from the supplied coordinates")

    return polygon


def _calc_segment_length(points: Sequence[Coordinate]) -> float:
    if len(points) < 2:
        return 0.0
    arr = np.asarray(points)
    diffs = np.diff(arr, axis=0)
    return float(np.sum(np.linalg.norm(diffs, axis=1)))


def _square_degrees_to_sq_m(area_sq_deg: float, reference_lat: float) -> float:
    """Convert an area from square degrees to square metres (approximate)."""

    lat_factor = math.cos(math.radians(reference_lat))
    return area_sq_deg * 111000 * 111000 * lat_factor


def _flatten_lines(geometry: LineString | MultiLineString) -> Iterable[LineString]:
    if isinstance(geometry, LineString):
        yield geometry
    elif isinstance(geometry, MultiLineString):
        for geom in geometry.geoms:
            yield geom


def generate_coverage_plan(
    boundary: Sequence[Coordinate],
    spray_width: float,
    holes: Optional[Sequence[Sequence[Coordinate]]] = None,
    angle_resolution: float = 5.0,
) -> CoveragePlan:
    """Compute a boustrophedon coverage path for the supplied farm polygon.

    Args:
        boundary: Outer farm boundary coordinates (lon, lat) in order.
        spray_width: Effective spray width (in coordinate units). For lat/lon
            coordinates, 0.0001° is roughly 11 metres near the equator.
        holes: Optional list of excluded patches that the sprayer must skip.
        angle_resolution: Step (in degrees) for evaluating candidate path
            orientations. Smaller values yield better optimisation but are
            slower.

    Returns:
        CoveragePlan with ordered spray and deadhead segments.
    """

    if spray_width <= 0:
        raise ValueError("spray_width must be positive")

    polygon = _build_shapely_polygon(boundary, holes)
    centroid = polygon.centroid

    best_angle: Optional[float] = None
    best_cost: Tuple[int, float] | None = None
    best_rotated: Optional[Polygon] = None

    angle = 0.0
    while angle < 180.0:
        rotated = affinity.rotate(polygon, -angle, origin=centroid, use_radians=False)
        minx, miny, maxx, maxy = rotated.bounds
        height = maxy - miny
        if height == 0:
            angle += angle_resolution
            continue
        passes_needed = max(1, math.ceil(height / spray_width))
        overlap = passes_needed * spray_width - height
        cost = (passes_needed, overlap)
        if best_cost is None or cost < best_cost:
            best_cost = cost
            best_angle = angle
            best_rotated = rotated
        angle += angle_resolution

    if best_angle is None or best_rotated is None or best_cost is None:
        raise RuntimeError("Unable to determine an orientation for coverage path")

    minx, miny, maxx, maxy = best_rotated.bounds
    passes = max(1, math.ceil((maxy - miny) / spray_width))

    segments: List[PathSegment] = []
    last_endpoint: Optional[Coordinate] = None
    spray_path_length = 0.0
    deadhead_length = 0.0

    # Build extended lines along the X axis in rotated space and intersect with polygon.
    sweep_lines: List[Tuple[float, List[LineString]]] = []
    for idx in range(passes + 1):  # +1 to ensure we do not leave gaps near the top edge
        y = miny + idx * spray_width
        extended_line = LineString([(minx - spray_width, y), (maxx + spray_width, y)])
        intersection = best_rotated.intersection(extended_line)
        if intersection.is_empty:
            continue
        pieces = [segment for segment in _flatten_lines(intersection)]
        if pieces:
            sweep_lines.append((y, pieces))

    sweep_lines.sort(key=lambda item: item[0])

    direction = 1  # 1 => left-to-right in rotated space, -1 => right-to-left
    for _, line_segments in sweep_lines:
        ordered = sorted(line_segments, key=lambda seg: seg.coords[0][0])
        if direction < 0:
            ordered = list(reversed(ordered))

        for segment in ordered:
            # Rotate back into original coordinate system and optionally flip direction.
            rotated_segment = affinity.rotate(segment, best_angle, origin=centroid, use_radians=False)
            coords = list(rotated_segment.coords)
            if direction < 0:
                coords = list(reversed(coords))

            if last_endpoint is not None and coords[0] != last_endpoint:
                deadhead_segment = PathSegment(points=[last_endpoint, coords[0]], spray_on=False)
                segments.append(deadhead_segment)
                deadhead_length += _calc_segment_length(deadhead_segment.points)

            spray_segment = PathSegment(points=coords, spray_on=True)
            segments.append(spray_segment)
            spray_path_length += _calc_segment_length(spray_segment.points)
            last_endpoint = coords[-1]

        direction *= -1

    total_length = spray_path_length + deadhead_length

    return CoveragePlan(
        segments=segments,
        orientation_deg=best_angle,
        spray_width=spray_width,
        num_passes=len(sweep_lines),
        total_path_length=total_length,
        spray_path_length=spray_path_length,
        deadhead_length=deadhead_length,
    )


def summarise_plan(plan: CoveragePlan) -> str:
    """Return a human readable summary string for the coverage plan."""

    spray_pc = (plan.spray_path_length / plan.total_path_length * 100.0) if plan.total_path_length else 0.0
    deadhead_pc = 100.0 - spray_pc
    return (
        f"Orientation: {plan.orientation_deg:.1f}°\n"
        f"Spray width: {plan.spray_width:.6f}\n"
        f"Passes needed: {plan.num_passes}\n"
        f"Total path length: {plan.total_path_length:.6f}\n"
        f"  • Spray-on distance: {plan.spray_path_length:.6f} ({spray_pc:.1f}%)\n"
        f"  • Deadhead distance: {plan.deadhead_length:.6f} ({deadhead_pc:.1f}%)"
    )


def plan_to_polyline(plan: CoveragePlan) -> List[List[Coordinate]]:
    """Return only the spray-on polylines for GIS export or visualisation."""

    return [segment.points for segment in plan.segments if segment.spray_on]


def compute_track_coverage(
    track_points: Sequence[Coordinate],
    spray_width: float,
    farm_boundary: Optional[Sequence[Coordinate]] = None,
    holes: Optional[Sequence[Sequence[Coordinate]]] = None,
    include_geometries: bool = False,
) -> dict:
    """Estimate how much area a recorded tractor track has covered.

    Args:
        track_points: GPS track of the tractor (ordered list of lon/lat pairs).
        spray_width: Effective width of the boom / sprayer.
        farm_boundary: Optional farm polygon to clip against.
        holes: Optional excluded patches inside the farm.
        include_geometries: If True, include shapely geometries in the response
            (useful for further GIS processing or plotting).

    Returns:
        Dictionary containing coverage areas (square degrees, square metres,
        acres) and coverage percentages.
    """

    if len(track_points) < 2:
        raise ValueError("track_points must contain at least two coordinates")
    if spray_width <= 0:
        raise ValueError("spray_width must be positive")

    track_line = LineString(track_points)
    half_width = spray_width / 2.0
    coverage_polygon = track_line.buffer(half_width, cap_style=2, join_style=2)

    avg_lat = float(np.mean([pt[1] for pt in track_points]))
    coverage_area_sq_deg = coverage_polygon.area
    coverage_area_sq_m = _square_degrees_to_sq_m(coverage_area_sq_deg, avg_lat)
    coverage_area_acres = coverage_area_sq_m * 0.000247105

    farm_polygon = None
    farm_area_sq_deg = None
    farm_area_sq_m = None
    farm_area_acres = None
    overlap_area_sq_deg = None
    overlap_area_sq_m = None
    overlap_area_acres = None
    coverage_percentage = None
    overspray_area_sq_m = None
    overspray_area_acres = None

    if farm_boundary is not None:
        farm_polygon = _build_shapely_polygon(farm_boundary, holes)
        farm_area_sq_deg = farm_polygon.area
        farm_centroid_lat = float(farm_polygon.centroid.y)
        farm_area_sq_m = _square_degrees_to_sq_m(farm_area_sq_deg, farm_centroid_lat)
        farm_area_acres = farm_area_sq_m * 0.000247105

        overlap_polygon = coverage_polygon.intersection(farm_polygon)
        overlap_area_sq_deg = overlap_polygon.area
        overlap_area_sq_m = _square_degrees_to_sq_m(overlap_area_sq_deg, farm_centroid_lat)
        overlap_area_acres = overlap_area_sq_m * 0.000247105

        if farm_area_sq_m > 0:
            coverage_percentage = (overlap_area_sq_m / farm_area_sq_m) * 100.0
        overspray_area_sq_m = max(0.0, coverage_area_sq_m - (overlap_area_sq_m or 0.0))
        overspray_area_acres = overspray_area_sq_m * 0.000247105
    else:
        overlap_polygon = None

    result = {
        "spray_width": spray_width,
        "coverage_area_sq_deg": coverage_area_sq_deg,
        "coverage_area_sq_m": coverage_area_sq_m,
        "coverage_area_acres": coverage_area_acres,
        "overlap_area_sq_deg": overlap_area_sq_deg,
        "overlap_area_sq_m": overlap_area_sq_m,
        "overlap_area_acres": overlap_area_acres,
        "overspray_area_sq_m": overspray_area_sq_m,
        "overspray_area_acres": overspray_area_acres,
        "farm_area_sq_deg": farm_area_sq_deg,
        "farm_area_sq_m": farm_area_sq_m,
        "farm_area_acres": farm_area_acres,
        "coverage_percentage": coverage_percentage,
    }

    if include_geometries:
        result["coverage_polygon"] = coverage_polygon
        if farm_polygon is not None:
            result["farm_polygon"] = farm_polygon
            result["overlap_polygon"] = overlap_polygon
    return result


def plot_coverage_plan(
    plan: CoveragePlan,
    boundary: Sequence[Coordinate],
    holes: Optional[Sequence[Sequence[Coordinate]]] = None,
    ax: Optional["plt.Axes"] = None,
    title: Optional[str] = None,
):
    """Visualise the coverage plan on top of the farm polygon using matplotlib."""

    import matplotlib.pyplot as plt  # Local import to avoid hard dependency for non-plot usage

    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MplPath

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 8))
    else:
        fig = ax.figure

    # Build a compound path (outer ring + holes) for plotting.
    vertices = list(boundary)
    codes = [MplPath.MOVETO] + [MplPath.LINETO] * (len(vertices) - 1) + [MplPath.CLOSEPOLY]
    vertices.append(vertices[0])

    path_vertices = vertices.copy()
    path_codes = codes.copy()

    if holes:
        for hole in holes:
            if len(hole) < 3:
                continue
            hole_vertices = list(hole)
            hole_codes = [MplPath.MOVETO] + [MplPath.LINETO] * (len(hole_vertices) - 1) + [MplPath.CLOSEPOLY]
            hole_vertices.append(hole_vertices[0])
            path_vertices.extend(hole_vertices)
            path_codes.extend(hole_codes)

    polygon_patch = PathPatch(MplPath(path_vertices, path_codes), facecolor="#98fb98", edgecolor="#006400", alpha=0.3)
    ax.add_patch(polygon_patch)

    # Plot coverage segments.
    for segment in plan.segments:
        xs, ys = zip(*segment.points)
        if segment.spray_on:
            ax.plot(xs, ys, color="#1f77b4", linewidth=2.0, solid_capstyle="round")
        else:
            ax.plot(xs, ys, color="#ff7f0e", linewidth=1.2, linestyle="--", alpha=0.8)

    ax.scatter([p[0] for p in boundary], [p[1] for p in boundary], color="#006400", s=30, zorder=5)

    if holes:
        for hole in holes:
            hx, hy = zip(*hole)
            ax.scatter(hx, hy, color="#d62728", marker="x", s=45, zorder=5)

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    if title:
        ax.set_title(title)
    else:
        ax.set_title("Coverage path plan")

    all_x = [p[0] for p in boundary]
    all_y = [p[1] for p in boundary]
    if holes:
        for hole in holes:
            all_x.extend([p[0] for p in hole])
            all_y.extend([p[1] for p in hole])

    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)
    x_range = x_max - x_min
    y_range = y_max - y_min

    ax.set_xlim(x_min - 0.1 * x_range, x_max + 0.1 * x_range)
    ax.set_ylim(y_min - 0.1 * y_range, y_max + 0.1 * y_range)

    ax.grid(True, linestyle="--", alpha=0.5)
    fig.tight_layout()
    return ax


def coverage_plan_to_geojson(
    plan: CoveragePlan,
    boundary: Optional[Sequence[Coordinate]] = None,
    holes: Optional[Sequence[Sequence[Coordinate]]] = None,
    include_deadhead: bool = True,
) -> dict:
    """Serialize a coverage plan and optional farm polygon to GeoJSON.

    Args:
        plan: CoveragePlan instance returned by ``generate_coverage_plan``.
        boundary: Optional farm boundary coordinates to include as a polygon.
        holes: Optional hole polygons to include inside the farm boundary.
        include_deadhead: If False, omit segments where ``spray_on`` is False.

    Returns:
        GeoJSON FeatureCollection (Python dict) suitable for exporting to
        front-end mapping libraries such as Leaflet, Mapbox GL, Cesium, etc.
    """

    features: List[dict] = []

    if boundary is not None:
        exterior = list(boundary)
        if exterior[0] != exterior[-1]:
            exterior = exterior + [exterior[0]]

        coordinates = [exterior]
        if holes:
            for hole in holes:
                if len(hole) < 3:
                    continue
                ring = list(hole)
                if ring[0] != ring[-1]:
                    ring = ring + [ring[0]]
                coordinates.append(ring)

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": coordinates,
            },
            "properties": {
                "type": "farm_boundary",
            },
        })

    for idx, segment in enumerate(plan.segments):
        if not include_deadhead and not segment.spray_on:
            continue

        length = _calc_segment_length(segment.points)
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [list(coord) for coord in segment.points],
            },
            "properties": {
                "type": "coverage_segment",
                "order": idx,
                "spray_on": segment.spray_on,
                "length": length,
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "orientation_deg": plan.orientation_deg,
            "spray_width": plan.spray_width,
            "passes": plan.num_passes,
            "total_path_length": plan.total_path_length,
            "spray_path_length": plan.spray_path_length,
            "deadhead_length": plan.deadhead_length,
        },
    }


