import argparse
import random
from pathlib import Path

from intent_api.application.check_training_set import CheckTrainingSet
from intent_api.application.build_training_set import BuildTrainingSet, Settings, normalised
from intent_api.domain.errors import LibraryError
from intent_api.infrastructure.eval_loader import load_cases
from intent_api.infrastructure.family_loader import load_families
from intent_api.infrastructure.library_loader import load_library
from intent_api.infrastructure.training_files import write_files

OUT_FOLDER = Path(__file__).resolve().parents[5] / "Training" / "out"


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="intent-api training")
    parser.add_argument("command", choices=["build", "check"])
    parser.add_argument("--out", type=Path, default=OUT_FOLDER)
    parser.add_argument("--seed", type=int, default=Settings.seed)
    parser.add_argument("--fraction", type=float, default=1.0, help="keep this share of the training items (learning curve)")
    args = parser.parse_args(argv)
    try:
        library = load_library()
        families, slots = load_families(library)
        evaluation = frozenset(normalised(case.question) for case in load_cases(library))
    except LibraryError as error:
        raise SystemExit("\n".join(error.problems))
    items = BuildTrainingSet(library, families, slots, Settings(seed=args.seed), evaluation).execute()
    if args.command == "check":
        report = CheckTrainingSet(library, families, items, evaluation).execute()
        print("\n".join(report.lines))
        if report.problems:
            raise SystemExit("problems:\n" + "\n".join(f"  {problem}" for problem in report.problems))
        print("ok")
        return
    if args.fraction < 1.0:
        rng = random.Random(f"{args.seed}:fraction")
        items = [item for item in items if item.heldout or rng.random() < args.fraction]
    counts = write_files(items, library, args.out)
    print(f"wrote {counts['train']} training and {counts['heldout']} held-out items to {args.out}")
