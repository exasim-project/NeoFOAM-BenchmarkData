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

def plot_file_neon(pr_file, main_file):
    """ time is in e-09"""

    pr = pd.read_csv(pr_file)
    main = pd.read_csv(pr_file)

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


def plot_file_neofoam(pr_file):
    """ time is in e-09"""

    pr = pd.read_csv(pr_file)

    pr['benchmark_name'] = pr['benchmark_name'].apply(lambda x: x.replace("Executor",""))
    pr['section1'] = pr['section1'].apply(lambda x: x.replace("OpenFOAM",""))
    pr['section2'] = pr['section2'].apply(lambda x: x.replace("OF_",""))
    pr['section1'] = pr['section1'].apply(lambda x: x.replace("NeoN",""))
    pr['section2'] = pr['section2'].apply(lambda x: x.replace("NeoN","NN_"))
    pr['Resolution'] = pr['Resolution'].apply(lambda x: int(x[1:]))
    pr["Cells"] = 0
    pr.loc[pr["MeshType"] == '2DSquare', 'Cells'] = pr['Resolution']**2
    pr.loc[pr["MeshType"] == '3DCube', 'Cells'] = pr['Resolution']**3
    pr["Time/Cell"] = pr["avg_runtime"]/ pr["Cells"]
    
    # print(df.pivot(columns=["section1", "MeshType", "benchmark_name"], values="Time/Cell", index=["section2", "Resolution"]))


    pr["time [ns]"] = pr["avg_runtime"]
    pr["size"] = pr["Cells"]
    pr["mean"] = pr["avg_runtime"]
    pr["executor"] = pr["benchmark_name"]
    pr["test_case"] = pr["section1"] + pr["MeshType"]

    plot = sb.catplot(kind="bar", data=pr, x="size", y="time [ns]", hue="executor", col="test_case")
    #plt.grid()
    plot.savefig(str(pr_file).replace(".csv", "_time.png"))

    #plt.grid()
    pr["fvops"] = pr["size"]/pr["mean"] * 10e9

    pr["executor_sec2"] = pr["benchmark_name"] + pr["section2"] 
    plot = sb.catplot(kind="bar", data=pr, x="size", y="fvops", hue="executor_sec2", col="test_case")
    #plt.grid()
    plot.set(yscale="log")
    plot.savefig(str(pr_file).replace(".csv", "_fvops.png"))

    plot = sb.catplot(kind="bar", data=pr, x="size", y="Time/Cell", hue="executor_sec2",  col="test_case")
    plot.set(yscale="log")
    plot.savefig(str(pr_file).replace(".csv", "_timp_per_cell.png"))


def plot_fold(root, pr_number):
    """given a folder this function calls plot_fn for every json"""
    _, inst, _ = next(os.walk(root/pr_number))
    for i in inst:
        _, _, files = next(os.walk(root/pr_number/i))
        for f in files:
            print(pr_number, i, f)
            if f.endswith("csv"):
                plot_file_neofoam(root/pr_number/i/f)


def main():
    root, folds, _  = next(os.walk("NeoFOAM"))
    for fold in folds:
        if is_number(fold):
            plot_fold(Path(root), Path(fold))


if __name__ == "__main__":
    main()
