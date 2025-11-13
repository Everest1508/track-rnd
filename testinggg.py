from coverage_planner import compute_track_coverage

track = [
    (77.5950, 12.9720),
    (77.5958, 12.9721),
    (77.5965, 12.9718),
    (77.5962, 12.9709),
    (77.5954, 12.9706),
]

farm = [
    (77.5950, 12.9720),
    (77.5960, 12.9726),
    (77.5971, 12.9719),
    (77.5968, 12.9706),
    (77.5956, 12.9701),
    (77.5948, 12.9709),
]

holes = [
    [
        (77.5954, 12.9718),
        (77.5957, 12.9719),
        (77.5958, 12.9716),
        (77.5955, 12.9713),
        (77.5953, 12.9715),
    ]
]

stats = compute_track_coverage(track, 0.00018, farm_boundary=farm, holes=holes)
for key, value in stats.items():
    if isinstance(value, float):
        print(f"{key}: {value:.6f}")
    else:
        print(f"{key}: {value}")