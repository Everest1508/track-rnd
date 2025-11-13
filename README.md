# Farm Polygon Visualization with Excluded Patches

This program visualizes farm boundaries using latitude and longitude coordinates, with support for excluded patches (holes) within the farm area.

> 🌾 **For farmers and non-technical users**: See [FARMER_GUIDE.md](FARMER_GUIDE.md) for a simple, step-by-step guide!

## 🌟 Key Feature: ANY POLYGON SHAPE SUPPORTED!

**Your farm does NOT need to be rectangular or regular!** This program supports:
- ✨ **Irregular polygon shapes** (following natural terrain, rivers, roads, hills)
- ✨ **Non-convex polygons** (L-shaped, star-shaped, any complex boundary)
- ✨ **Any number of vertices** (3 or more points)
- ✨ **Real-world boundaries** (property lines, cadastral boundaries, GPS traces)

## Features

- ✅ **ANY polygon shape** for farm boundaries - rectangular, irregular, following natural features
- ✅ Support for excluded patches inside the farm (ponds, buildings, rocky areas, wetlands)
- ✅ Multiple excluded patches in a single farm
- ✅ **Excluded patches can also be ANY polygon shape**
- ✅ Automatic area calculation (acres and square meters)
- ✅ Interactive visualization with matplotlib
- ✅ Accounts for latitude when calculating areas

## Requirements

```bash
pip install matplotlib numpy shapely
# or use the bundled list
pip install -r requirements.txt
```

## Usage

### Irregular Polygon Farm (Realistic Natural Boundary)

**This is the most common real-world scenario!** Farms rarely have perfectly rectangular boundaries.

```python
from main import create_and_draw_polygon

# Define irregular farm boundary following natural features
# (property lines, rivers, roads, terrain)
irregular_farm = [
    (77.5950, 12.9720),  # Point following actual GPS coordinates
    (77.5955, 12.9724),  # Along a road
    (77.5965, 12.9722),  # Following river bend
    (77.5970, 12.9715),  # Property line corner
    (77.5968, 12.9705),  # Following hill contour
    (77.5955, 12.9702),  # Another boundary
    (77.5948, 12.9710)   # Back to start area
]

# Draw the irregular farm
create_and_draw_polygon(irregular_farm)
```

### Basic Rectangular Farm (No Excluded Patches)

```python
from main import create_and_draw_polygon

# Define farm boundary coordinates (lon, lat)
farm_boundary = [
    (77.5950, 12.9720),
    (77.5970, 12.9720),
    (77.5970, 12.9700),
    (77.5950, 12.9700)
]

# Draw the farm
create_and_draw_polygon(farm_boundary)
```

### Farm with Excluded Patches

```python
from main import create_and_draw_polygon

# Define farm boundary
farm_boundary = [
    (77.5950, 12.9720),
    (77.5970, 12.9720),
    (77.5970, 12.9700),
    (77.5950, 12.9700)
]

# Define excluded patches (e.g., pond, building)
excluded_patches = [
    # Patch 1: Pond
    [
        (77.5953, 12.9715),
        (77.5955, 12.9715),
        (77.5955, 12.9713),
        (77.5953, 12.9713)
    ],
    # Patch 2: Building
    [
        (77.5963, 12.9710),
        (77.5966, 12.9710),
        (77.5966, 12.9707),
        (77.5963, 12.9707)
    ]
]

# Draw the farm with excluded patches
create_and_draw_polygon(farm_boundary, holes=excluded_patches)
```

## Function Parameters

### `create_and_draw_polygon(vertices, holes=None)`

**Parameters:**
- `vertices` (list of tuples): List of (longitude, latitude) coordinate pairs defining the outer farm boundary
  - Must have at least 3 vertices
  - Coordinates should be in the format: `(lon, lat)`

- `holes` (list of lists, optional): List of excluded patch polygons
  - Each hole is a list of (longitude, latitude) coordinate pairs
  - Each hole must have at least 3 vertices
  - Use this for areas like ponds, buildings, rocky patches, roads, etc.

## Coordinate Format

- Coordinates should be in **decimal degrees**
- Format: `(longitude, latitude)` 
- Example: `(77.5950, 12.9716)` represents a point in Bangalore, India

## Examples

The `main.py` file contains three examples:

1. **Irregular boundary farm** (no excluded patches)
2. **Uneven (non-rectangular) farm** with 2 excluded patches (pond + shed)
3. **Highly irregular farm** with 1 excluded patch

You can run any example by uncommenting the respective function call in `main.py`.

## Running the Program

### Run the main example (uneven farm with holes)
```bash
python main.py
```

If you installed the dependencies inside the bundled virtual environment, run:

```bash
venv/bin/python main.py
```

This will execute the default example (Example 2: Uneven farm with excluded patches).

### See ALL polygon shape examples
```bash
python examples_showcase.py
```

This demonstrates 6 different polygon types:
1. Triangle farm (3 vertices)
2. Pentagon farm (5 vertices, irregular)
3. L-shaped farm (non-convex)
4. Highly irregular farm (15 vertices, following natural boundaries)
5. Irregular farm with excluded patches (most realistic)
6. Star-shaped farm (complex non-convex)

You can uncomment any example in `examples_showcase.py` to visualize it.

### Optimised Tractor Coverage Path Planning

To generate a boustrophedon (lawnmower) spray path that minimises overlap while
covering the entire farm:

```python
import matplotlib.pyplot as plt
from coverage_planner import generate_coverage_plan, plot_coverage_plan, summarise_plan

spray_width = 0.0002  # ≈22 m at the equator (adjust to your boom width)
plan = generate_coverage_plan(farm_boundary, spray_width, holes=excluded_patches)
print(summarise_plan(plan))
plot_coverage_plan(plan, farm_boundary, holes=excluded_patches,
                   title="Coverage Path")
plt.show()
```

The planner:
- searches for the best driving orientation that reduces the number of passes
- spaces passes by the boom width to avoid unnecessary overlap
- automatically skips excluded patches (ponds/buildings)
- returns spray vs. deadhead segments with length summaries
- exportable as GeoJSON (see next section) for mobile/tractor navigation

### Export Paths to the Frontend (GeoJSON)

When you are ready to feed the coverage path into a navigation UI, serialize it
as GeoJSON and send it to the frontend:

```python
import json
from coverage_planner import coverage_plan_to_geojson

plan = generate_coverage_plan(farm_boundary, spray_width, holes=excluded_patches)
geojson_payload = coverage_plan_to_geojson(
    plan,
    boundary=farm_boundary,
    holes=excluded_patches,
    include_deadhead=False,  # send only spray-on lines
)

with open("coverage-plan.geojson", "w", encoding="utf-8") as fp:
    json.dump(geojson_payload, fp, indent=2)
```

Your frontend (Leaflet, Mapbox GL JS, Cesium, etc.) can draw the polygon and the
ordered spray passes directly from this payload. Each feature contains
``properties.order`` and ``properties.spray_on`` flags so the navigation logic
knows which segments should have the boom enabled.

### REST API (Flask)

For integration with other services you can spin up the bundled Flask API.

```bash
python app.py           # on bare Python
# or
venv/bin/python app.py  # using the provided virtualenv
```

Endpoints:

- `GET /health` – simple health probe
- `POST /plan-coverage`
  - Request JSON:

    ```json
    {
      "boundary": [[77.5950, 12.9720], ...],
      "holes": [[[...]], ...],           // optional
      "spray_width": 0.0002,
      "angle_resolution": 5.0,          // optional
      "include_deadhead": false         // optional
    }
    ```

  - Response JSON contains a `summary` object and a `geojson` feature
    collection that you can feed into a frontend map or guidance system.

- `POST /track-coverage`
  - Request JSON:

    ```json
    {
      "track": [[77.5950, 12.9720], ...],
      "spray_width": 0.00018,
      "boundary": [[...]],              // optional
      "holes": [[[...]]]                // optional
    }
    ```

  - Response returns the coverage statistics (acres, square metres,
    percentage, overspray) identical to the Python helper.

Use a reverse proxy (nginx, Traefik, etc.) if you plan to expose this API
publicly. Enable HTTPS and add authentication as needed for production.

### Browser Frontend

A lightweight Leaflet-based viewer lives in `frontend/`. It can talk to the
Flask API and render polygons, spray passes, and tractor tracks.

```bash
# Terminal 1 – start the API
venv/bin/python app.py

# Terminal 2 – serve the static frontend
cd frontend
python -m http.server 8000
```

Open <http://localhost:8000> in a browser. Use "Load Example" to pre-fill the
demo farm, then click "Plan Coverage" or "Analyse Track". The map will render:
- Farm boundary + holes (green)
- Spray passes (blue for spray-on, orange dashed for deadhead)
- Tractor track (pink) when you analyse coverage

Edit `frontend/app.js` if you want to integrate with your own authentication or
API host.

### Track a Tractor's Actual Coverage

If you collect GPS points from a tractor (or spray boom) while working, you can
measure how much of the farm was actually covered:

```python
from coverage_planner import compute_track_coverage

# Example GPS track (longitude, latitude pairs)
tractor_track = [
    (77.5950, 12.9720),
    (77.5958, 12.9721),
    (77.5965, 12.9718),
    (77.5962, 12.9709),
    (77.5954, 12.9706),
]

stats = compute_track_coverage(
    tractor_track,
    spray_width=0.00018,           # ≈20 m boom width
    farm_boundary=farm_boundary,   # Optional: clip to your field
    holes=excluded_patches,
)

print(f"Area covered (within farm): {stats['overlap_area_acres']:.2f} acres")
print(f"Coverage achieved: {stats['coverage_percentage']:.1f}% of the farm")
print(f"Overspray outside farm: {stats['overspray_area_acres']:.2f} acres")
```

The function buffers the recorded path by half the spray width, clips it to the
farm polygon (if supplied), and returns the covered area in square metres and
acres along with coverage percentage.

## Polygon Shape Support

### ✅ Supported Polygon Types

1. **Regular polygons**: Rectangles, squares, triangles
2. **Irregular polygons**: Any shape with 3+ vertices
3. **Non-convex polygons**: L-shaped, C-shaped, star-shaped
4. **Complex boundaries**: Following roads, rivers, property lines, terrain contours
5. **GPS traced boundaries**: Direct GPS coordinates from walking the perimeter

### ❓ How to Get Your Farm Coordinates

You can obtain farm boundary coordinates in several ways:

1. **GPS Walk**: Walk around your farm perimeter with a GPS device/phone app
2. **Google Maps**: Right-click on map points to get lat/lon coordinates
3. **Survey Data**: Use existing cadastral/survey boundary data
4. **Drone/Satellite**: Extract boundaries from aerial imagery
5. **Government Records**: Land registry boundary data

### 📐 Polygon Requirements

- **Minimum vertices**: 3 (forms a triangle)
- **Maximum vertices**: Unlimited (can have hundreds of points for curved boundaries)
- **Coordinate order**: Define vertices in order (clockwise or counter-clockwise)
- **Closed polygon**: The program automatically closes the shape

## Real-World Use Cases

This tool is useful for:

- 🚜 Agricultural land mapping with **real, irregular farm boundaries**
- 🌾 Calculating actual cultivable area (excluding non-farmable patches)
- 📊 Farm planning and visualization for **any farm shape**
- 🗺️ Geographic Information Systems (GIS) applications
- 📱 Farm management mobile applications
- 🏞️ Natural feature-based boundary mapping (rivers, hills, roads)

## Visualization Details

- **Green area**: Farmable land
- **Green circles**: Farm boundary vertices
- **Red X markers**: Excluded patch vertices
- **White areas inside**: Excluded patches (non-farmable areas)

## Notes

- The program uses matplotlib's `PathPatch` to create compound paths supporting holes
- All coordinates are visualized with equal aspect ratio for accurate representation
- The grid helps in identifying coordinate positions

