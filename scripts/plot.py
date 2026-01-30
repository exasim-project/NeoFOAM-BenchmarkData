import pandas as pd
import seaborn as sb
import os
import matplotlib.pyplot as plt

from pathlib import Path


def is_number(f):
    try:
        _ = int(f)
        return True
    except:
        return False


def plot_file(pr_file, main_file):
    """ time is in e-09"""

    pr = pd.read_json(pr_file)
    main = pd.read_json(main_file)

    pr = pr.astype({"size":"float","mean":"float"})
    main = main.astype({"size":"float","mean":"float"})
    pr["time [ns]"] = pr["mean"]

    plot = sb.catplot(kind="bar", data=pr, x="size", y="time [ns]", hue="executor", col="test_case")
    #plt.grid()
    plot.savefig(str(pr_file).replace(".json", "_time.png"))

    pr["rel. diff. [%]"] = pr["mean"]/main["mean"] * 100
    pr["rel. diff. [%]"] = pr["rel. diff. [%]"] - 100.

    plot = sb.catplot(kind="bar", data=pr, x="size", y="rel. diff. [%]", hue="executor", col="test_case")
    #plt.grid()
    plot.savefig(str(pr_file).replace(".json", "_relative.png"))

    pr["fvops"] = pr["size"]/pr["mean"] * 10e9

    plot = sb.catplot(kind="bar", data=pr, x="size", y="fvops", hue="executor", col="test_case")
    #plt.grid()
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
    root, folds, _  = next(os.walk("NeoN"))
    for fold in folds:
        if is_number(fold):
            plot_fold(Path(root), Path(fold))
    root, folds, _  = next(os.walk("NeoFOAM"))
    for fold in folds:
        if is_number(fold):
            plot_fold(Path(root), Path(fold))


if __name__ == "__main__":
    main()
