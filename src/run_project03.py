"""Run the complete Project03 pipeline."""

from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]

required = [
    BASE / "data" / "raw" / "augsburg_boundary.geojson",
    BASE / "data" / "raw" / "augsburg_pedestrian_network.osm",
]

missing = [p for p in required if not p.exists() or p.stat().st_size == 0]

if missing:
    print("\nMissing Project03 input file(s):")
    for p in missing:
        print(f"  - {p.relative_to(BASE)}")
    print(
        "\nThese are the two small Augsburg-specific Overpass exports. "
        "No synthetic network result will be generated.\n"
    )
    sys.exit(2)

for script in [
    "01_build_network.py",
    "02_analyse_accessibility.py",
    "03_make_outputs.py",
    "04_generate_summary.py",
]:
    print(f"\n=== Running {script} ===")
    subprocess.run(
        [sys.executable, str(BASE / "src" / script)],
        check=True,
        cwd=BASE,
    )

print("\nProject03 pipeline complete.")
