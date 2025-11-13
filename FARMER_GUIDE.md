# Farmer's Quick Start Guide

## 🌾 What This Program Does

This program helps you:
- **Visualize your farm boundary** on a map
- **Calculate your farm area** in acres and square meters
- **Exclude non-farmable areas** like ponds, buildings, rocky patches
- **Get accurate cultivable area** for planning and reporting

## ✅ Works with ANY Farm Shape!

**Your farm does NOT need to be a perfect rectangle or square!**

This program works with:
- 🏞️ Irregular shapes following rivers, roads, hills
- 🌊 Boundaries along natural features
- 🛣️ Property lines at any angles
- 📍 Any shape traced with GPS coordinates

## 📱 How to Get Your Farm's Coordinates

### Method 1: Using a GPS Phone App (Easiest)
1. Download a GPS app on your phone (e.g., "GPS Test", "My GPS Coordinates")
2. Walk around your farm boundary
3. At each corner or turning point, note down the coordinates
4. Write them as: `(longitude, latitude)`

### Method 2: Using Google Maps
1. Open Google Maps on your computer
2. Right-click on each corner of your farm
3. Click "What's here?"
4. Copy the latitude and longitude shown
5. Note: Google shows as `latitude, longitude` but enter as `(longitude, latitude)` in code

### Method 3: Use Survey Data
If you have official land survey documents, they may include GPS coordinates.

## 🚀 Quick Start Example

Let's say your farm has these corner points (in lon, lat format):

```python
my_farm = [
    (77.5950, 12.9720),  # Corner 1 (Southwest)
    (77.5970, 12.9720),  # Corner 2 (Southeast)  
    (77.5970, 12.9700),  # Corner 3 (Northeast)
    (77.5950, 12.9700)   # Corner 4 (Northwest)
]
```

And you have a pond you want to exclude:

```python
pond = [
    (77.5958, 12.9712),  # Pond corner 1
    (77.5962, 12.9712),  # Pond corner 2
    (77.5962, 12.9708),  # Pond corner 3
    (77.5958, 12.9708)   # Pond corner 4
]
```

## 💻 How to Use

### Step 1: Edit the coordinates in `main.py`

Replace the example coordinates with your actual farm coordinates:

```python
# Your farm boundary
my_farm_boundary = [
    (your_lon_1, your_lat_1),
    (your_lon_2, your_lat_2),
    (your_lon_3, your_lat_3),
    # ... add as many points as you need
]

# Areas to exclude (ponds, buildings, etc.)
excluded_areas = [
    # First excluded area (e.g., pond)
    [
        (pond_lon_1, pond_lat_1),
        (pond_lon_2, pond_lat_2),
        (pond_lon_3, pond_lat_3),
        (pond_lon_4, pond_lat_4)
    ],
    # Add more excluded areas if needed
]
```

### Step 2: Run the program

```bash
python main.py
```

### Step 3: View the results

The program will show you:
- ✅ A visual map of your farm
- ✅ Total farm area in acres and square meters
- ✅ Area of excluded patches
- ✅ Actual farmable area
- ✅ Percentage of farmable land

### Step 4 (Optional): Plan the tractor spray route

If you want an *automatic* path that tells the tractor where to drive so the
sprayer covers the whole farm with minimal overlap:

```python
import matplotlib.pyplot as plt
from coverage_planner import generate_coverage_plan, plot_coverage_plan, summarise_plan

spray_width = 0.00018  # ~20 metres; change to match your boom width
plan = generate_coverage_plan(my_farm_boundary, spray_width, holes=excluded_areas)
print(summarise_plan(plan))
plot_coverage_plan(plan, my_farm_boundary, holes=excluded_areas,
                   title="Tractor Coverage Path")
plt.show()
```

This gives you:
- The **best driving direction** for the tractor (minimises overlaps)
- A list of **spray segments** vs **deadhead (boom off) segments**
- Total distance to drive with spray on/off
- A detailed map you can hand to your tractor operator or GPS guidance system

### Step 5 (Optional): Measure what area your tractor actually covered

If you recorded GPS points while the tractor was spraying, you can check how
much area was covered and how much of the farm remains untreated:

```python
from coverage_planner import compute_track_coverage

tractor_track = [
    (77.5950, 12.9720),
    (77.5958, 12.9721),
    (77.5965, 12.9718),
    (77.5962, 12.9709),
    (77.5954, 12.9706),
]

coverage_stats = compute_track_coverage(
    tractor_track,
    spray_width=0.00018,            # Match this to your boom width
    farm_boundary=my_farm_boundary,
    holes=excluded_areas,
)

print(f"Farm area covered: {coverage_stats['overlap_area_acres']:.2f} acres")
print(f"Coverage achieved: {coverage_stats['coverage_percentage']:.1f}%")
print(f"Overspray outside farm: {coverage_stats['overspray_area_acres']:.2f} acres")
```

This calculation:
- Buffers the tractor track by half the spray width
- Clamps it to your farm boundary (so neighbouring fields are excluded)
- Reports the covered area, overspray, and % of farm completed

### Step 6 (Optional): Send the driving path to a mobile app / tractor display

If you want a tablet or tractor navigation system to show the exact passes to
drive, export the plan to GeoJSON and load it in your frontend map:

```python
import json
from coverage_planner import coverage_plan_to_geojson, generate_coverage_plan

plan = generate_coverage_plan(my_farm_boundary, spray_width, holes=excluded_areas)
geojson = coverage_plan_to_geojson(plan, boundary=my_farm_boundary, holes=excluded_areas)

with open("tractor_path.geojson", "w", encoding="utf-8") as fp:
    json.dump(geojson, fp)
```

Upload this GeoJSON to your mobile app (Leaflet, Mapbox, Google Earth, etc.).
Each line feature has an ``order`` value so you can guide the tractor pass by
pass, and the ``spray_on`` flag tells you when the boom should be active.

> Tech teams: A REST API (`app.py`) is included if you prefer to call these
> tools from a web or mobile backend instead of running scripts manually.

You can also open the ready-made map viewer in `frontend/` to see the plan on a
browser while the tractor is in the field.

## 📊 Understanding the Output

```
Total Farm Area: 11.87 acres (48026.46 m²)
Excluded Area: 0.39 acres (1560.86 m²)
Farmable Area: 11.48 acres (46465.60 m²)
Farmable Percentage: 96.7%
```

This means:
- Your entire farm boundary covers **11.87 acres**
- Ponds, buildings, etc. take up **0.39 acres**
- You can farm on **11.48 acres** (96.7% of total)

## 🎨 Visual Guide

When you see the map:
- **Green filled area** = Your farmable land
- **Green circles** = Your farm boundary points
- **Red X marks** = Excluded patch corners
- **White areas inside** = Non-farmable patches (ponds, buildings, etc.)

## ❓ Common Questions

### Q: My farm is not a rectangle. Will it work?
**A: YES!** The program works with ANY shape. Your farm can follow rivers, roads, hills, property lines - any irregular boundary.

### Q: How many corners/points can I have?
**A: At least 3, maximum unlimited.** You can have 3, 5, 10, 20, 100+ points if needed for curved boundaries.

### Q: Can I have multiple ponds/buildings to exclude?
**A: YES!** You can exclude as many patches as you need. Just add them to the `excluded_areas` list.

### Q: What coordinate format should I use?
**A: (longitude, latitude)** in decimal degrees format.
- Example: `(77.5950, 12.9716)`
- Longitude comes first, then latitude

### Q: How accurate is the area calculation?
**A: Very accurate** for most farming purposes. The calculation accounts for latitude and provides results in both acres and square meters.

### Q: I don't know how to code. Can I still use this?
**A: Yes!** You only need to:
1. Replace the example coordinates with yours
2. Run `python main.py`
3. That's it! No coding knowledge needed.

## 📞 Need Help?

If you're having trouble:
1. Check that coordinates are in format: `(longitude, latitude)`
2. Make sure you have at least 3 points for your farm boundary
3. Ensure coordinates form a closed shape (no overlapping lines)

## 🌟 Example Real Farm

Here's a real-world example of an irregular farm:

```python
# Irregular farm following road and river
realistic_farm = [
    (77.5950, 12.9720),  # Start at road intersection
    (77.5953, 12.9724),  # Follow road north
    (77.5960, 12.9725),  # Road turns
    (77.5968, 12.9722),  # Along river
    (77.5970, 12.9715),  # River bend
    (77.5966, 12.9705),  # Property line
    (77.5955, 12.9702),  # Back along fence
    (77.5948, 12.9710)   # Return to start area
]

# Small pond to exclude
pond_in_farm = [
    [
        (77.5958, 12.9717),
        (77.5961, 12.9718),
        (77.5962, 12.9715),
        (77.5960, 12.9713),
        (77.5957, 12.9714)
    ]
]

# Calculate and visualize
create_and_draw_polygon(realistic_farm, holes=pond_in_farm)
```

This will show the irregular farm shape with the pond excluded, and calculate the exact farmable area!

