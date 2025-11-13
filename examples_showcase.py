"""
Examples Showcase - Demonstrating Various Polygon Shapes
This file shows that the program works with ANY polygon shape!
"""

from main import create_and_draw_polygon, calculate_farmable_area
from coverage_planner import generate_coverage_plan, summarise_plan

print("=" * 80)
print("FARM POLYGON VISUALIZATION - SHAPE SUPPORT DEMONSTRATION")
print("=" * 80)
print("\nThis demonstrates that farms can be ANY POLYGON SHAPE!")
print("Not limited to rectangles or regular shapes.\n")

# Example 1: Triangle Farm
print("\n1. TRIANGLE FARM (3 vertices)")
print("-" * 40)
triangle_farm = [
    (77.5950, 12.9720),
    (77.5970, 12.9720),
    (77.5960, 12.9700)
]
area = calculate_farmable_area(triangle_farm)
print(f"   Area: {area['total_area_acres']:.2f} acres")
print("   Shape: Simple triangle")
# Uncomment to visualize: create_and_draw_polygon(triangle_farm)


# Example 2: Pentagon Farm (5 vertices)
print("\n2. PENTAGON FARM (5 vertices)")
print("-" * 40)
pentagon_farm = [
    (77.5950, 12.9715),
    (77.5958, 12.9720),
    (77.5968, 12.9717),
    (77.5965, 12.9708),
    (77.5952, 12.9708)
]
area = calculate_farmable_area(pentagon_farm)
print(f"   Area: {area['total_area_acres']:.2f} acres")
print("   Shape: 5-sided irregular polygon")
# Uncomment to visualize: create_and_draw_polygon(pentagon_farm)


# Example 3: L-Shaped Farm (Non-convex)
print("\n3. L-SHAPED FARM (non-convex polygon)")
print("-" * 40)
l_shaped_farm = [
    (77.5950, 12.9720),  # Top-left
    (77.5965, 12.9720),  # Top-right
    (77.5965, 12.9712),  # Inner corner 1
    (77.5958, 12.9712),  # Inner corner 2
    (77.5958, 12.9705),  # Bottom-right
    (77.5950, 12.9705)   # Bottom-left
]
area = calculate_farmable_area(l_shaped_farm)
print(f"   Area: {area['total_area_acres']:.2f} acres")
print("   Shape: L-shaped (non-convex)")
# Uncomment to visualize: create_and_draw_polygon(l_shaped_farm)


# Example 4: Highly Irregular Farm (Following Natural Boundaries)
print("\n4. HIGHLY IRREGULAR FARM (following river/road/terrain)")
print("-" * 40)
irregular_farm = [
    (77.5950, 12.9720),
    (77.5952, 12.9723),
    (77.5955, 12.9725),
    (77.5960, 12.9726),
    (77.5965, 12.9724),
    (77.5970, 12.9720),
    (77.5972, 12.9715),
    (77.5971, 12.9710),
    (77.5968, 12.9705),
    (77.5963, 12.9702),
    (77.5957, 12.9701),
    (77.5952, 12.9703),
    (77.5948, 12.9707),
    (77.5946, 12.9712),
    (77.5947, 12.9717)
]
area = calculate_farmable_area(irregular_farm)
print(f"   Area: {area['total_area_acres']:.2f} acres")
print("   Shape: 15 vertices, highly irregular")
# Uncomment to visualize: create_and_draw_polygon(irregular_farm)


# Example 5: Irregular Farm WITH Excluded Patches
print("\n5. IRREGULAR FARM + EXCLUDED PATCHES (most realistic)")
print("-" * 40)
realistic_farm = [
    (77.5950, 12.9720),
    (77.5953, 12.9724),
    (77.5960, 12.9725),
    (77.5968, 12.9722),
    (77.5970, 12.9715),
    (77.5966, 12.9705),
    (77.5955, 12.9702),
    (77.5948, 12.9710)
]

# Multiple irregular excluded patches
excluded = [
    # Irregular pond
    [
        (77.5958, 12.9717),
        (77.5961, 12.9718),
        (77.5962, 12.9715),
        (77.5960, 12.9713),
        (77.5957, 12.9714)
    ],
    # Small building
    [
        (77.5963, 12.9710),
        (77.5965, 12.9710),
        (77.5965, 12.9708),
        (77.5963, 12.9708)
    ]
]

area = calculate_farmable_area(realistic_farm, holes=excluded)
print(f"   Total Area: {area['total_area_acres']:.2f} acres")
print(f"   Excluded Area: {area['excluded_area_acres']:.2f} acres")
print(f"   Farmable Area: {area['farmable_area_acres']:.2f} acres")
print(f"   Farmable: {(area['farmable_area_acres']/area['total_area_acres']*100):.1f}%")
print("   Shape: Irregular boundary + 2 irregular holes")
# Uncomment to visualize: create_and_draw_polygon(realistic_farm, holes=excluded)


# Example 6: Star-Shaped Farm (Complex Non-convex)
print("\n6. STAR-SHAPED FARM (complex non-convex)")
print("-" * 40)
star_farm = [
    (77.5960, 12.9720),  # Top point
    (77.5962, 12.9715),  # Inner right
    (77.5968, 12.9714),  # Right point
    (77.5963, 12.9710),  # Inner bottom-right
    (77.5964, 12.9704),  # Bottom-right point
    (77.5960, 12.9708),  # Inner bottom
    (77.5956, 12.9704),  # Bottom-left point
    (77.5957, 12.9710),  # Inner bottom-left
    (77.5952, 12.9714),  # Left point
    (77.5958, 12.9715)   # Inner left
]
area = calculate_farmable_area(star_farm)
print(f"   Area: {area['total_area_acres']:.2f} acres")
print("   Shape: Star-like (10 vertices, non-convex)")
# Uncomment to visualize: create_and_draw_polygon(star_farm)


# Example 7: Coverage Path Planning on Irregular Farm
print("\n7. COVERAGE PATH PLANNING (tractor spray path)")
print("-" * 40)
spray_width = 0.0002  # ≈22 m
coverage_plan = generate_coverage_plan(realistic_farm, spray_width, holes=excluded)
print(summarise_plan(coverage_plan))
print("   • Spray segments:", sum(1 for seg in coverage_plan.segments if seg.spray_on))
print("   • Deadhead segments:", sum(1 for seg in coverage_plan.segments if not seg.spray_on))
# Uncomment to visualise the plan:
# plot_coverage_plan(coverage_plan, realistic_farm, holes=excluded,
#                    title="Coverage Path (spray width ≈ 22 m)")
# plt.show()


print("\n" + "=" * 80)
print("CONCLUSION: The program supports ALL polygon shapes!")
print("=" * 80)
print("\nKey Points:")
print("  • Any number of vertices (3 or more)")
print("  • Regular or irregular shapes")
print("  • Convex or non-convex polygons")
print("  • With or without excluded patches (holes)")
print("  • Holes can also be any polygon shape")
print("\nTo visualize any example above, uncomment the create_and_draw_polygon() line")
print("in the code and run this script again.")
print("=" * 80)

