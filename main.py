import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
import numpy as np

from coverage_planner import generate_coverage_plan, plot_coverage_plan, summarise_plan

def calculate_polygon_area(vertices):
    """
    Calculate the area of a polygon using the Shoelace formula.
    
    Args:
        vertices (list of tuples): List of (lon, lat) coordinate pairs
        
    Returns:
        float: Area of the polygon in square degrees
    """
    if len(vertices) < 3:
        return 0
    
    vertices = np.array(vertices)
    x = vertices[:, 0]
    y = vertices[:, 1]
    
    # Shoelace formula
    area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    return area

def calculate_farmable_area(vertices, holes=None):
    """
    Calculate the actual farmable area excluding holes.
    
    Args:
        vertices (list of tuples): List of (lon, lat) coordinate pairs for outer boundary
        holes (list of lists, optional): List of hole polygons
        
    Returns:
        dict: Dictionary containing total area, excluded area, and farmable area
    """
    total_area = calculate_polygon_area(vertices)
    excluded_area = 0
    
    if holes:
        for hole in holes:
            excluded_area += calculate_polygon_area(hole)
    
    farmable_area = total_area - excluded_area
    
    # Convert to approximate square meters (very rough approximation)
    # At the equator: 1 degree ≈ 111km, so 1 square degree ≈ 12,321 km²
    # This is a rough estimate and varies with latitude
    avg_lat = np.mean([v[1] for v in vertices])
    lat_factor = np.cos(np.radians(avg_lat))
    
    sq_meters_total = total_area * 111000 * 111000 * lat_factor
    sq_meters_excluded = excluded_area * 111000 * 111000 * lat_factor
    sq_meters_farmable = farmable_area * 111000 * 111000 * lat_factor
    
    return {
        'total_area_sq_deg': total_area,
        'excluded_area_sq_deg': excluded_area,
        'farmable_area_sq_deg': farmable_area,
        'total_area_sq_m': sq_meters_total,
        'excluded_area_sq_m': sq_meters_excluded,
        'farmable_area_sq_m': sq_meters_farmable,
        'total_area_acres': sq_meters_total * 0.000247105,  # Convert to acres
        'excluded_area_acres': sq_meters_excluded * 0.000247105,
        'farmable_area_acres': sq_meters_farmable * 0.000247105
    }

def create_and_draw_polygon(vertices, holes=None):
    """
    Creates and draws a polygon using a list of (lat, lon) coordinates.
    Supports polygons with holes (excluded patches within the farm boundary).
    
    **IMPORTANT**: The farm can be ANY POLYGON SHAPE - irregular, non-convex, 
    following natural terrain, property boundaries, etc. It does NOT have to 
    be rectangular or regular!

    Args:
        vertices (list of tuples): A list of (lon, lat) coordinate pairs 
                                   defining the outer farm boundary.
                                   Can be ANY polygon shape with 3+ vertices.
                                   Examples: irregular, curved boundary following
                                   rivers, roads, hills, property lines, etc.
        holes (list of lists, optional): A list of hole polygons, where each hole 
                                         is a list of (lon, lat) coordinate pairs 
                                         defining excluded patches (e.g., ponds, buildings,
                                         rocky areas, wetlands, roads through the farm).
                                         Each hole can also be ANY polygon shape.
    """
    if not vertices or len(vertices) < 3:
        print("A polygon must have at least 3 vertices (lat, lon) coordinates.")
        return

    # 1. Convert vertices list to a NumPy array
    polygon_points = np.array(vertices)
    
    # 2. Extract coordinates for the scatter plot
    x_coords = polygon_points[:, 0]
    y_coords = polygon_points[:, 1]
    
    # 3. Create the plot
    fig, ax = plt.subplots(figsize=(10, 8))

    # 4. Create a Path with holes support
    # Build the path codes and vertices
    path_vertices = []
    path_codes = []
    
    # Add outer boundary (MOVETO for first vertex, LINETO for rest, CLOSEPOLY at end)
    path_vertices.extend(vertices)
    path_codes.append(Path.MOVETO)
    path_codes.extend([Path.LINETO] * (len(vertices) - 1))
    path_codes.append(Path.CLOSEPOLY)
    path_vertices.append((0, 0))  # Dummy vertex for CLOSEPOLY
    
    # Add holes (excluded patches)
    if holes:
        for hole in holes:
            if len(hole) < 3:
                print(f"Warning: Skipping hole with less than 3 vertices")
                continue
            path_vertices.extend(hole)
            path_codes.append(Path.MOVETO)
            path_codes.extend([Path.LINETO] * (len(hole) - 1))
            path_codes.append(Path.CLOSEPOLY)
            path_vertices.append((0, 0))  # Dummy vertex for CLOSEPOLY
    
    # Create the Path object
    path = Path(path_vertices, path_codes)
    
    # Create the PathPatch with the compound path
    poly = PathPatch(
        path,
        edgecolor='darkgreen', 
        facecolor='lightgreen', 
        alpha=0.6, 
        linewidth=2
    )
    ax.add_patch(poly)

    # 5. Add scatter points for the outer boundary vertices
    ax.scatter(x_coords, y_coords, color='darkgreen', marker='o', s=50, 
               label='Farm Boundary', zorder=5)
    
    # Add scatter points for holes if they exist
    if holes:
        for i, hole in enumerate(holes):
            hole_array = np.array(hole)
            ax.scatter(hole_array[:, 0], hole_array[:, 1], 
                      color='red', marker='x', s=50, 
                      label=f'Excluded Patch {i+1}', zorder=5)

    # 6. Calculate and display area information
    area_info = calculate_farmable_area(vertices, holes)
    
    # 7. Set labels and title
    title = "Farm Boundary with Excluded Patches (Lat/Lon Coordinates)"
    if holes:
        title += f"\nFarmable Area: {area_info['farmable_area_acres']:.2f} acres "
        title += f"({area_info['farmable_area_sq_m']:.2f} m²)"
        title += f"\nExcluded: {area_info['excluded_area_acres']:.2f} acres"
    else:
        title += f"\nTotal Area: {area_info['total_area_acres']:.2f} acres "
        title += f"({area_info['total_area_sq_m']:.2f} m²)"
    
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(loc='best')

    # 8. Calculate bounds from all vertices (outer + holes)
    all_x = list(x_coords)
    all_y = list(y_coords)
    if holes:
        for hole in holes:
            hole_array = np.array(hole)
            all_x.extend(hole_array[:, 0])
            all_y.extend(hole_array[:, 1])
    
    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)
    x_range = x_max - x_min
    y_range = y_max - y_min

    ax.set_xlim(x_min - x_range * 0.1, x_max + x_range * 0.1)
    ax.set_ylim(y_min - y_range * 0.1, y_max + y_range * 0.1)
    
    # Ensure axes are equally scaled (important for accurate shape representation)
    ax.set_aspect('equal', adjustable='box') 
    ax.grid(True, linestyle='--', alpha=0.5)

    # 9. Display the plot
    plt.tight_layout()
    plt.show()

# --- Example Usage ---

# Example 1: Irregular polygon farm (following natural terrain)
# This demonstrates that farms can be ANY polygon shape, not just rectangular!
print("Example 1: Irregular polygon farm (realistic farm boundary)")
irregular_farm_boundary = [
    (77.5950, 12.9720),  # Point 1
    (77.5953, 12.9725),  # Point 2 - follows road/river
    (77.5960, 12.9726),  # Point 3
    (77.5968, 12.9723),  # Point 4
    (77.5970, 12.9718),  # Point 5
    (77.5972, 12.9710),  # Point 6
    (77.5968, 12.9704),  # Point 7
    (77.5962, 12.9702),  # Point 8
    (77.5955, 12.9703),  # Point 9
    (77.5948, 12.9707),  # Point 10
    (77.5946, 12.9714),  # Point 11 - back to start area
]

# Uncomment to run:
# create_and_draw_polygon(irregular_farm_boundary)

# Example 2: Uneven (non-rectangular) farm with excluded patches
print("\nExample 2: Uneven farm with excluded patches")

# Define the outer farm boundary (intentionally irregular)
farm_boundary = [
    (77.5950, 12.9720),  # Northwest edge along hedgerow
    (77.5960, 12.9726),  # Northern bulge following river bend
    (77.5971, 12.9719),  # North-east fence corner
    (77.5968, 12.9706),  # South-east dip around a ravine
    (77.5956, 12.9701),  # Southern low ground
    (77.5948, 12.9709),  # South-west corner near access road
]

# Define excluded patches inside the farm
excluded_patches = [
    # Patch 1: Irregular pond near the west side
    [
        (77.5954, 12.9718),
        (77.5957, 12.9719),
        (77.5958, 12.9716),
        (77.5955, 12.9713),
        (77.5953, 12.9715)
    ],
    # Patch 2: Machinery shed/rocky area in the south-east
    [
        (77.5964, 12.9712),
        (77.5967, 12.9712),
        (77.5966, 12.9709),
        (77.5963, 12.9709)
    ]
]

# Calculate and display area information
area_info = calculate_farmable_area(farm_boundary, holes=excluded_patches)
print(f"Total Farm Area: {area_info['total_area_acres']:.2f} acres ({area_info['total_area_sq_m']:.2f} m²)")
print(f"Excluded Area: {area_info['excluded_area_acres']:.2f} acres ({area_info['excluded_area_sq_m']:.2f} m²)")
print(f"Farmable Area: {area_info['farmable_area_acres']:.2f} acres ({area_info['farmable_area_sq_m']:.2f} m²)")
print(f"Farmable Percentage: {(area_info['farmable_area_acres'] / area_info['total_area_acres'] * 100):.1f}%")

# Run the function to create and draw the farm with excluded patches
create_and_draw_polygon(farm_boundary, holes=excluded_patches)

# Coverage path planning for the uneven farm example
print("\nCoverage Path Planning (Example 2 - Uneven Farm)")
spray_width_deg = 0.0002  # ~22 metres at the equator
plan = generate_coverage_plan(
    farm_boundary,
    spray_width=spray_width_deg,
    holes=excluded_patches,
    angle_resolution=2.5,
)
print(summarise_plan(plan))
plot_coverage_plan(
    plan,
    farm_boundary,
    holes=excluded_patches,
    title="Example 2: Coverage Path (spray width ≈ 22 m)",
)
plt.show()

# Example 3: REALISTIC - Irregular shaped farm with excluded patches
# This is the most common real-world scenario!
print("\nExample 3: Irregular polygon farm with excluded patches (MOST REALISTIC)")
irregular_farm = [
    (77.5950, 12.9720),  # Following natural terrain/property lines
    (77.5955, 12.9724),
    (77.5965, 12.9722),
    (77.5970, 12.9715),
    (77.5968, 12.9705),
    (77.5955, 12.9702),
    (77.5948, 12.9710)
]

# Excluded patches within irregular farm
irregular_patches = [
    # Patch 1: Natural pond
    [
        (77.5958, 12.9716),
        (77.5960, 12.9717),
        (77.5961, 12.9715),
        (77.5960, 12.9713),
        (77.5958, 12.9714)
    ],
    # Patch 2: Rocky area (non-farmable)
    [
        (77.5963, 12.9710),
        (77.5965, 12.9710),
        (77.5965, 12.9708),
        (77.5963, 12.9708)
    ]
]

# Uncomment to run this example:
# area_info = calculate_farmable_area(irregular_farm, holes=irregular_patches)
# print(f"Total Farm Area: {area_info['total_area_acres']:.2f} acres")
# print(f"Farmable Area: {area_info['farmable_area_acres']:.2f} acres")
# print(f"Farmable Percentage: {(area_info['farmable_area_acres'] / area_info['total_area_acres'] * 100):.1f}%")
# create_and_draw_polygon(irregular_farm, holes=irregular_patches)
