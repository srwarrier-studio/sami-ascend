# Fine-tune Laya on the generated training set. Run it on Google Colab (Runtime > Change runtime type > GPU, a T4 is enough).
#
# Before you start, on your own machine:
#   uv run --package intent-api intent-api training check          (must print ok)
#   uv run --package intent-api intent-api training build          (writes training/out/train.jsonl and heldout.jsonl)
# The two files contain invented questions only. Upload nothing else to Colab: no real questions, names or figures.
#
# In Colab: paste this whole file into one cell (or upload it and run `%run colab_finetune.py`), run it, upload train.jsonl and
# heldout.jsonl when asked, wait, and it downloads intent-tuned.zip. Unzip it into a folder on the machine that runs laya-serve.
#
# The table printed after training compares the checkpoint before and after on the held-out families (accuracy, ECE, loss).
#
# Learning curve: build with `training build --fraction 0.25` (then 0.5 and 1.0), run this script once for each, and set RUN_NAME
# to tell the three downloads apart.

import os
import shutil
import subprocess
import sys

BASE = os.environ.get("BASE", "typed-decisions")
RUN_NAME = os.environ.get("RUN_NAME", "intent-tuned")
EPOCHS = int(os.environ.get("EPOCHS", "10"))
LIMIT = int(os.environ.get("LIMIT", "0"))
FREEZE_ENCODER = os.environ.get("FREEZE_ENCODER", "0") == "1"
SEED = int(os.environ.get("SEED", "0"))

if os.environ.get("SKIP_INSTALL") != "1":
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "laya"], check=True)

try:
    from google.colab import files

    if not (os.path.exists("train.jsonl") and os.path.exists("heldout.jsonl")):
        print("Upload train.jsonl and heldout.jsonl")
        files.upload()
except ImportError:
    files = None

if LIMIT:
    for name in ("train.jsonl", "heldout.jsonl"):
        lines = open(name, encoding="utf-8").read().splitlines()[:LIMIT]
        open(f"limited_{name}", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    TRAIN, HELDOUT = "limited_train.jsonl", "limited_heldout.jsonl"
else:
    TRAIN, HELDOUT = "train.jsonl", "heldout.jsonl"

from laya.train import TrainConfig, dry_run, finetune, resolve_checkpoint_dir

check = dry_run(TRAIN, resolve_checkpoint_dir(BASE))
print(check)
assert not check["skipped"], f"some rows cannot be used: {check['skipped']}"

config = TrainConfig(epochs=EPOCHS, loss="soft-ce", shuffle_options=("choice",), freeze_encoder=FREEZE_ENCODER, eval_data=HELDOUT, seed=SEED)
report = finetune(TRAIN, BASE, RUN_NAME, config)
for key in ("train_items", "calibration_items", "skipped", "epoch_loss", "temperature", "calibration"):
    print(key, report.get(key))

archive = shutil.make_archive(RUN_NAME, "zip", RUN_NAME)
print("wrote", archive)
if files is not None:
    files.download(archive)
