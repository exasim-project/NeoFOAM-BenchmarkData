import pandas as pd
import seaborn as sb
import os
from pathlib import Path


def is_number(f):
    try:
        _ = int(f)
        return True
    except:
        return False


def plot_file(pr_file, main_file):

    pr = pd.read_json(pr_file)
    main = pd.read_json(main_file)

    pr = pr.astype({"size":"float","mean":"float"})
    main = main.astype({"size":"float","mean":"float"})

    plot = sb.catplot(kind="bar", data=pr, x="size", y="mean", hue="executor", col="test_case")
    plot.savefig(str(pr_file).replace(".json", "_time.png"))

    pr["mean_rel"] = pr["mean"]/main["mean"]
    pr["mean_rel"] = pr["mean"] - 1.

    plot = sb.catplot(kind="bar", data=pr, x="size", y="mean_rel", hue="executor", col="test_case")
    plot.savefig(str(pr_file).replace(".json", "_relative.png"))

    pr["fvops"] = pr["size"]/pr["mean"]
    plot = sb.catplot(kind="bar", data=pr, x="size", y="fvops", hue="executor", col="test_case")
    plot.savefig(str(pr_file).replace(".json", "_fvops.png"))

def plot_fold(root, pr_number):
    """given a folder this function calls plot_fn for every json"""
    _, inst, _ = next(os.walk(root/pr_number))
    for i in inst:
        _, _, files = next(os.walk(root/pr_number/i))
        for f in files:
            print(pr_number, i, f)
            if not f.endswith("json"):
                continue
            main_path = root/pr_number/i/"main"/f
            if not main_path.exists():
                continue
            plot_file(root/pr_number/i/f, main_path)


def main():
    root, folds, _  = next(os.walk("."))
    for fold in folds:
        if is_number(fold):
            plot_fold(Path(root), Path(fold))


if __name__ == "__main__":
    main()
