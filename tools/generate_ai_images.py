"""Generate photorealistic product images with Stable Diffusion (Diffusers).

Dev-only tool. CPU by default (no CUDA on this machine). Slow — a couple of
minutes per image. Usage from the project root:

    python tools/generate_ai_images.py                # all products -> images/
    python tools/generate_ai_images.py espresso croissant --out preview

Replaces images/<id>.png so the bot picks the photos up on next restart.
"""

import argparse
import os
import sys

import torch
from diffusers import DPMSolverMultistepScheduler, StableDiffusionPipeline

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from menu import IMAGES_DIR, _DEFAULTS  # noqa: E402

MODEL = "stable-diffusion-v1-5/stable-diffusion-v1-5"
SIZE = 512
STEPS = 28
GUIDANCE = 7.0

_STYLE = ("professional food photography, on a rustic wooden café table, "
          "warm natural light, shallow depth of field, high detail, appetizing, 50mm")
NEGATIVE = ("blurry, low quality, distorted, deformed, text, watermark, logo, "
            "ugly, oversaturated, cartoon, illustration, plastic, extra objects")

# Per-product subject prompts (combined with the shared style above).
PROMPTS: dict[str, str] = {
    "espresso": "a single espresso shot in a small white cup on a saucer",
    "cappuccino": "a cappuccino in a white cup with latte-art foam on top",
    "latte": "a caffè latte in a tall glass with milky foam",
    "flat_white": "a flat white coffee in a white cup with smooth microfoam",
    "croissant": "a fresh golden flaky butter croissant on a ceramic plate",
    "cinnamon_roll": "a warm cinnamon roll with white glaze on a small plate",
    "muffin": "a blueberry muffin on a small plate",
    "avocado_toast": "avocado toast on sourdough bread with seeds, on a plate",
    "granola_bowl": "a bowl of granola with yogurt and fresh berries",
}


def build_pipe() -> StableDiffusionPipeline:
    pipe = StableDiffusionPipeline.from_pretrained(MODEL, torch_dtype=torch.float32, safety_checker=None)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.to("cpu")
    torch.set_num_threads(os.cpu_count() or 4)
    return pipe


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ids", nargs="*", help="product ids to generate (default: all)")
    parser.add_argument("--out", default=None, help="output dir (default: project images/)")
    parser.add_argument("--seed", type=int, default=12345)
    args = parser.parse_args()

    ids = args.ids or [d["id"] for d in _DEFAULTS]
    out_dir = args.out or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), IMAGES_DIR)
    os.makedirs(out_dir, exist_ok=True)

    print(f"Loading {MODEL} (first run downloads ~4 GB)…", flush=True)
    pipe = build_pipe()

    for i, pid in enumerate(ids):
        subject = PROMPTS.get(pid)
        if not subject:
            print("skip (no prompt):", pid); continue
        prompt = f"{subject}, {_STYLE}"
        generator = torch.Generator(device="cpu").manual_seed(args.seed + i)
        print(f"[{i+1}/{len(ids)}] {pid}…", flush=True)
        image = pipe(prompt, negative_prompt=NEGATIVE, num_inference_steps=STEPS,
                     guidance_scale=GUIDANCE, height=SIZE, width=SIZE, generator=generator).images[0]
        path = os.path.join(out_dir, f"{pid}.png")
        image.save(path)
        print("   wrote", path, flush=True)

    print("done.")


if __name__ == "__main__":
    main()
