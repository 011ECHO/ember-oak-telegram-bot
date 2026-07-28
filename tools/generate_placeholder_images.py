"""(Re)generate the placeholder images for the default menu products.

Products added later via the in-bot editor get their image generated
automatically; this tool just (re)builds the ones for the seeded defaults.

Dev-only tool. Requires Pillow.  Run from the project root:
    python tools/generate_placeholder_images.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import images_gen  # noqa: E402
from menu import IMAGES_DIR, _DEFAULTS  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), IMAGES_DIR)

if __name__ == "__main__":
    for d in _DEFAULTS:
        path = images_gen.generate_card(d["id"], d["name"], d["price"], d["emoji"], d["accent"], OUT)
        print("wrote", path)
    print("done:", len(_DEFAULTS), "images")
