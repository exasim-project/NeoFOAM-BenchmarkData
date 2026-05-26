import sys
import json
import warnings

import pandas as pd
import seaborn as sb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path


_EXECUTOR_ORDER = ["SerialExecutor", "CPUExecutor", "GPUExecutor"]
_EXECUTOR_PALETTE = dict(zip(_EXECUTOR_ORDER, sb.color_palette("tab10", len(_EXECUTOR_ORDER))))


def _n_cells(size_str):
    result = 1
    for part in str(size_str).strip().split("x"):
        result *= int(part.strip())
    return result


def preprocess(df):
    df = df.copy()
    df["mean"] = df["mean"].astype(float)
    df["standard_deviation"] = df["standard_deviation"].astype(float)
    df["size"] = df["size"].astype(str).str.strip()
    df["value_type"] = df["value_type"].str.replace("NeoN::", "", regex=False)
    df["n_cells"] = df["size"].apply(_n_cells)
    df["time [ns]"] = df["mean"]
    df["fvops [1/s]"] = df["n_cells"] / df["mean"] * 1e9
    return df.sort_values("n_cells")


def _ordered(values, preferred):
    present = set(values)
    ordered = [v for v in preferred if v in present]
    ordered += sorted(present - set(ordered))
    return ordered



def _fill_row(axes_row, df, metric, ylabel, variants, hue_order, log=False):
    legend_handles, legend_labels = [], []

    for col_idx, variant in enumerate(variants):
        ax = axes_row[col_idx]
        sub = df[df["variant"] == variant].sort_values("n_cells")
        size_order = sub["size"].unique().tolist()
        sb.barplot(
            data=sub, x="size", y=metric,
            hue="executor", hue_order=hue_order,
            palette=_EXECUTOR_PALETTE,
            order=size_order, ax=ax,
        )
        if log:
            ax.set_yscale("log")

        ax.set_xlabel("size", fontsize=8)
        ax.set_ylabel(ylabel, fontsize=8)
        ax.tick_params(axis="x", labelrotation=30, labelsize=7)
        ax.tick_params(axis="y", labelsize=7)

        if not legend_handles:
            leg = ax.get_legend()
            if leg:
                legend_handles, legend_labels = ax.get_legend_handles_labels()
        leg = ax.get_legend()
        if leg:
            leg.remove()

    return legend_handles, legend_labels


def plot_file(pr_file, dev_file, plots_dir):
    try:
        pr = preprocess(pd.DataFrame(json.loads(pr_file.read_text())))
    except Exception as exc:
        warnings.warn(f"Skipping {pr_file.name}: {exc}")
        return

    dev = None
    if dev_file.exists():
        try:
            dev = preprocess(pd.DataFrame(json.loads(dev_file.read_text())))
        except Exception as exc:
            warnings.warn(f"Could not read develop file {dev_file.name}: {exc}")

    plots_dir.mkdir(parents=True, exist_ok=True)

    for (bname, dim, vtype), grp in pr.groupby(["benchmark_name", "dimension", "value_type"]):
        variants = sorted(grp["variant"].unique())
        hue_order = _ordered(grp["executor"].unique(), _EXECUTOR_ORDER)
        n_cols = len(variants)

        metrics = [
            ("time [ns]", "time [ns]", True),
            ("fvops [1/s]", "fvops [1/s]", True),
        ]

        merged = None
        if dev is not None:
            dev_grp = dev[
                (dev["benchmark_name"] == bname) &
                (dev["dimension"] == dim) &
                (dev["value_type"] == vtype)
            ]
            if not dev_grp.empty:
                merged = grp.merge(
                    dev_grp[["executor", "size", "variant", "fvops [1/s]"]].rename(
                        columns={"fvops [1/s]": "dev_fvops"}
                    ),
                    on=["executor", "size", "variant"],
                    how="left",
                ).dropna(subset=["dev_fvops"])
                if not merged.empty:
                    merged["speedup"] = merged["fvops [1/s]"] / merged["dev_fvops"]
                    metrics.append(("speedup", "fvops speedup vs develop", False))

        n_rows = len(metrics)
        fig, axes = plt.subplots(
            n_rows, n_cols,
            figsize=(4.5 * n_cols, 3.5 * n_rows),
            squeeze=False,
        )

        for col_idx, variant in enumerate(variants):
            axes[0, col_idx].set_title(variant, fontsize=10, fontweight="bold")

        legend_handles, legend_labels = [], []

        for row_idx, (metric, ylabel, log) in enumerate(metrics):
            data = merged if metric == "speedup" else grp
            h, l = _fill_row(axes[row_idx], data, metric, ylabel, variants, hue_order, log)
            if not legend_handles and h:
                legend_handles, legend_labels = h, l

        if legend_handles:
            fig.legend(
                legend_handles, legend_labels,
                loc="upper left",
                bbox_to_anchor=(1.02, 1.0), fontsize=8,
            )

        fig.suptitle(f"{bname} | {dim} | {vtype}", fontsize=12)
        fig.tight_layout()
        fig.savefig(plots_dir / f"{bname}_{dim}_{vtype}.png", bbox_inches="tight")
        plt.close(fig)
        print(f"  {bname}_{dim}_{vtype}")


def plot_runner(runner_dir, pr_name, runner_name):
    plots_dir = runner_dir / "plots"
    develop_dir = runner_dir / "develop"

    for pr_file in sorted(runner_dir.glob("*.json")):
        dev_file = develop_dir / pr_file.name
        plot_file(pr_file, dev_file, plots_dir)


def main():
    neon_root = Path("NeoN")
    if not neon_root.is_dir():
        sys.exit("Run from the repository root (NeoN/ directory not found).")

    for pr_dir in sorted(neon_root.iterdir()):
        if not pr_dir.is_dir():
            continue
        print(f"PR {pr_dir.name}")
        for runner_dir in sorted(pr_dir.iterdir()):
            if not runner_dir.is_dir() or runner_dir.name == "develop":
                continue
            print(f"  Runner: {runner_dir.name}")
            plot_runner(runner_dir, pr_dir.name, runner_dir.name)


if __name__ == "__main__":
    main()
