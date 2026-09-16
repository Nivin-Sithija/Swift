"""Every figure the paper needs, generated from the tables rather than from run records.

Reading the tables and not `ml/reports/runs/` is deliberate: the tables have already had the
v5/v8 label filter, the epoch-selection screen and the split check applied to them by
`build_results_tables.py` and the analysis scripts. A figure built straight off the records
would quietly re-admit everything those screens exclude.

Output is PDF (vector, for the camera-ready) and PNG (for drafts and slides) at the same size,
so a figure never has to be regenerated to change format.

Run:
    .venv312/bin/python paper/experiments/build_figures.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
TABLES = REPO / "paper" / "results" / "tables"
FIGS = REPO / "paper" / "results" / "figures"

# A single-column ACL/IEEE figure is ~3.3in wide; double-column ~7in. Setting this once
# means the type in the figure matches the type in the paper without post-hoc scaling,
# which is what makes figures look bolted on.
ONE_COL, TWO_COL = 3.3, 6.9

plt.rcParams.update({
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8.5,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 150, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})

# Colour carries meaning in exactly one place -- native vs romanized script -- so it is
# defined once and reused, and every other figure stays greyscale-safe.
C_NATIVE, C_ROMAN = "#2b5d8a", "#c26a3d"
C_NEUTRAL, C_ACCENT = "#4a4a4a", "#a01c3f"


def save(fig, name: str) -> None:
    FIGS.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(FIGS / f"{name}.{ext}")
    plt.close(fig)
    print(f"  {name}.pdf / .png")


def fig_encoder_gain_by_script() -> None:
    """The paper's headline figure: the encoder's advantage exists only on native script."""
    path = TABLES / "encoder_gain_by_script.csv"
    if not path.exists():
        print("  SKIP encoder_gain_by_script -- run encoder_gain_by_script.py first")
        return
    d = pd.read_csv(path)
    tracks = d[d["native_script"].notna()].copy()
    tracks["native_script"] = tracks["native_script"].astype(bool)
    order = ["english", "sinhala", "tamil", "singlish", "tamilish"]
    tracks = tracks.set_index("track").reindex([t for t in order if t in set(tracks["track"])])
    tracks = tracks.reset_index()

    fig, ax = plt.subplots(figsize=(ONE_COL, 2.2))
    y = range(len(tracks))
    colors = [C_NATIVE if n else C_ROMAN for n in tracks["native_script"]]
    # `ecolor` takes one colour, not one per point, so each interval is drawn on its own.
    for yi, (_, r), color in zip(y, tracks.iterrows(), colors):
        ax.errorbar(r["gain"], yi,
                    xerr=[[r["gain"] - r["ci_low"]], [r["ci_high"] - r["gain"]]],
                    fmt="none", ecolor=color, elinewidth=1.2, capsize=2.5)
    ax.scatter(tracks["gain"], list(y), c=colors, s=22, zorder=3)
    ax.axvline(0, color="#999999", lw=0.8, ls="--", zorder=1)

    ax.set_yticks(list(y))
    ax.set_yticklabels(tracks["track"])
    ax.invert_yaxis()
    ax.set_xlabel("LaBSE − TF-IDF+SVM  (Negative-F1)")
    ax.set_title("Encoder gain is confined to native script", pad=6)
    # The default locator puts a tick every 0.025 in a 3.3in axis, which overlaps the labels.
    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.05))

    # The legend states what the colour means, since that is the figure's whole argument.
    handles = [plt.Line2D([], [], marker="o", ls="", color=C_NATIVE, ms=4, label="native script"),
               plt.Line2D([], [], marker="o", ls="", color=C_ROMAN, ms=4, label="romanized")]
    ax.legend(handles=handles, loc="lower right", frameon=False)
    save(fig, "encoder_gain_by_script")


def fig_per_language_sentiment() -> None:
    """Every system loses on romanized input; the encoder does not close the gap."""
    path = TABLES / "language_gap.csv"
    if not path.exists():
        print("  SKIP per_language_sentiment -- run language_gap.py first")
        return
    d = pd.read_csv(path)
    d = d[d["task"] == "sentiment"]
    if d.empty:
        print("  SKIP per_language_sentiment -- no sentiment rows")
        return

    # `language_gap.csv` holds each track against english; english itself is in a column.
    eng = d.groupby("model")["headline_english"].first()
    wide = d.pivot_table(index="model", columns="track", values="headline")
    wide.insert(0, "english", eng)
    order = [t for t in ["english", "sinhala", "tamil", "singlish", "tamilish"] if t in wide.columns]
    wide = wide[order]
    models = [m for m in ["tfidf-cnb", "tfidf-sgd", "tfidf-logreg", "tfidf-svm", "labse"]
              if m in wide.index]
    wide = wide.loc[models]

    fig, ax = plt.subplots(figsize=(TWO_COL, 2.4))
    n = len(models)
    width = 0.8 / n
    greys = ["#c9c9c9", "#ababab", "#8d8d8d", "#6f6f6f"]
    for i, m in enumerate(models):
        color = C_ACCENT if m == "labse" else greys[min(i, len(greys) - 1)]
        ax.bar([x + i * width for x in range(len(order))], wide.loc[m], width,
               label=m, color=color, edgecolor="none")
    ax.set_xticks([x + width * (n - 1) / 2 for x in range(len(order))])
    ax.set_xticklabels(order)
    ax.set_ylabel("Negative-F1")
    ax.set_title("Sentiment by track — the encoder's lead narrows on romanized input", pad=6)
    ax.legend(frameon=False, ncol=n, loc="upper center", bbox_to_anchor=(0.5, -0.18))
    ax.set_ylim(0, 0.9)
    save(fig, "per_language_sentiment")


def fig_ceiling() -> None:
    """What is actually reachable: the label ceiling bounds the task, not model capacity."""
    ceil_path, topic_path = TABLES / "label_ceiling.csv", TABLES / "negative_is_topic.csv"
    if not ceil_path.exists():
        print("  SKIP ceiling -- run label_ceiling.py first")
        return
    c = pd.read_csv(ceil_path)
    row = c[(c["task"] == "sentiment") & (c["compared"].str.startswith("shipped"))]
    if row.empty:
        print("  SKIP ceiling -- no shipped-labels row")
        return
    ceiling = float(row["headline"].iloc[0])
    lo, hi = float(row["ci_low"].iloc[0]), float(row["ci_high"].iloc[0])

    bars = []
    if topic_path.exists():
        t = pd.read_csv(topic_path)
        for label, sysname in (("intent label only\n(no text)", "intent-label only (no text)"),
                               ("TF-IDF+SVM", "tfidf-svm on text")):
            hit = t[t["system"] == sysname]
            if not hit.empty:
                bars.append((label, float(hit["negative_f1"].iloc[0])))
    bars.append(("LaBSE\n(fine-tuned)", 0.7138))

    fig, ax = plt.subplots(figsize=(ONE_COL, 2.2))
    xs = range(len(bars))
    ax.bar(xs, [v for _, v in bars],
           color=[C_NEUTRAL, C_NEUTRAL, C_ACCENT][-len(bars):], edgecolor="none", width=0.6)
    ax.axhspan(lo, hi, color="#d9b3c2", alpha=0.35, zorder=0)
    ax.axhline(ceiling, color=C_ACCENT, lw=1.1, ls="--", zorder=2)
    ax.annotate(f"label ceiling {ceiling:.3f}", xy=(-0.45, ceiling),
                xytext=(0, 4), textcoords="offset points", ha="left", fontsize=7,
                color=C_ACCENT)
    for x, (_, v) in zip(xs, bars):
        ax.annotate(f"{v:.3f}", xy=(x, v), xytext=(0, 2), textcoords="offset points",
                    ha="center", fontsize=7)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([b for b, _ in bars])
    ax.set_ylabel("Negative-F1 (test)")
    ax.set_ylim(0, 1.0)
    ax.set_title("Sentiment is bounded by label quality", pad=6)
    save(fig, "label_ceiling")


def fig_tokenizer() -> None:
    """MuRIL's Sinhala collapse, with the mechanism next to it."""
    path = TABLES / "tokenizer_to_downstream_sentiment_dev.csv"
    if not path.exists():
        print("  SKIP tokenizer -- run tokenizer_to_downstream.py first")
        return
    d = pd.read_csv(path)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(TWO_COL, 2.3))
    for ax, col, xlabel in ((ax1, "unk_pct", "[UNK] rate (% of characters)"),
                            (ax2, "fertility", "fertility (tokens per word)")):
        hi = d[d["unk_pct"] > 10]
        lo = d[d["unk_pct"] <= 10]
        ax.scatter(lo[col], lo["delta_vs_english"], s=18, c=C_NEUTRAL,
                   label="other model × language cells")
        ax.scatter(hi[col], hi["delta_vs_english"], s=30, c=C_ACCENT, zorder=3,
                   label="MuRIL on Sinhala")
        ax.axhline(0, color="#999999", lw=0.8, ls="--")
        ax.set_xlabel(xlabel)
    ax1.set_ylabel("Negative-F1 vs own English")
    ax1.legend(frameon=False, loc="lower left")
    fig.suptitle("Characters lost to [UNK] predict the deficit; token count does not", y=1.02)
    save(fig, "tokenizer_to_downstream")


def fig_intent_epochs() -> None:
    """Was the epoch budget neutral? On intent, no -- the roster is still climbing at 6."""
    # Read the preserved snapshot, not `ml/reports/`. The live files are overwritten by every
    # subsequent job for the same model, so a figure built from them changes meaning depending
    # on which job ran last -- which is the opposite of what a paper figure should do.
    snap = REPO / "paper" / "results" / "runs" / "history"
    curves = {}
    for h in sorted(snap.glob("history_intent-dev_*.csv")):
        model = h.stem.split("_")[2]
        curves[model] = pd.read_csv(h)
    if not curves:
        print("  SKIP intent_epochs -- no multi-epoch intent histories on disk")
        return
    # `history_<model>.csv` is written per model, not per job, so a later job for the same
    # model overwrites the earlier curve. `history_labse.csv` currently holds K6a's 3-epoch
    # *sentiment* run, so LaBSE's intent curve is gone. Say so on the figure rather than
    # letting a reader assume the roster is complete.
    missing = sorted({"labse", "mmbert", "xlmr-base", "muril-base", "indicbert", "twhin-bert"}
                     - set(curves))
    if missing:
        print(f"  NOTE intent_epochs: missing {', '.join(missing)} "
              f"(history file overwritten by a later job for the same model)")

    # Two panels, because one cannot honestly carry both facts. The left shows the whole
    # curve, where everything above epoch 2 looks flat. The right zooms to the top of the
    # range, which is the only place the budget question is decided -- plotting the zoom
    # alone would exaggerate the late gains, and plotting the full range alone would hide
    # that the argmax sits at the edge.
    fig, (ax, axz) = plt.subplots(1, 2, figsize=(TWO_COL, 2.3),
                                  gridspec_kw={"width_ratios": [1.15, 1]})
    palette = ["#1f4e79", "#c26a3d", "#4a7c59", "#7b5aa6", "#a01c3f", "#8d8d8d"]
    for (name, d), color in zip(sorted(curves.items()), palette):
        for a in (ax, axz):
            a.plot(d["epoch"], d["headline"], marker="o", ms=2.5, lw=1.0,
                   color=color, label=name)
    ax.set_xlabel("epoch")
    ax.set_ylabel("macro-F1 (dev)")
    ax.set_title("full range", pad=4)

    last = max(d["epoch"].max() for d in curves.values())
    tops = [d["headline"].max() for d in curves.values()]
    axz.set_xlim(2.6, last + 0.4)
    axz.set_ylim(min(tops) - 0.02, max(tops) + 0.01)
    axz.set_xlabel("epoch")
    axz.set_title("zoom: epochs 3–%d" % last, pad=4)
    axz.legend(frameon=False, loc="lower right", ncol=1)

    # State the budget fact as a number rather than implying it from the shape.
    still_climbing = sum(int(d["headline"].idxmax() == len(d) - 1) for d in curves.values())
    fig.suptitle(f"Intent macro-F1 by epoch — {still_climbing} of {len(curves)} models peak "
                 f"at the last epoch", y=1.03)
    save(fig, "intent_epochs")



# ---------------------------------------------------------------------------
# System figures (paper section 17 / tracker track E)
# ---------------------------------------------------------------------------

def fig_queue_disparity() -> None:
    """The headline: what the script gap costs a customer, and that the score closes it."""
    path = TABLES / "tus_wait_by_language.csv"
    if not path.exists():
        print("  SKIP queue_disparity -- run run_system_eval.py first")
        return
    d = pd.read_csv(path, comment="#")
    d = d[d["rho"] == 1.05]
    disparity = pd.read_csv(TABLES / "tus_disparity.csv", comment="#")
    disparity = disparity[disparity["rho"] == 1.05]
    order = ["english", "sinhala", "tamil", "singlish", "tamilish"]
    shown = [("tier", "argmax tier\n(naive deployment)"), ("tus", "TUS\n(this work)"),
             ("oracle", "gold labels\n(control)")]

    fig, axes = plt.subplots(1, 3, figsize=(TWO_COL, 2.4), sharey=True)
    # Native and romanized are the contrast the figure exists to show, so they are the
    # only thing colour encodes -- the same encoding as fig_encoder_gain_by_script.
    colours = [C_NATIVE if l in ("english", "sinhala", "tamil") else C_ROMAN
               for l in order]
    for ax, (policy, title) in zip(axes, shown):
        sub = d[d["policy"] == policy].set_index("language").reindex(order)
        ax.bar(range(len(order)), sub["mean_wait_min"], color=colours,
               yerr=1.96 * sub["std"] / sub["count"] ** 0.5, ecolor=C_NEUTRAL,
               capsize=2, linewidth=0)
        ax.set_xticks(range(len(order)))
        ax.set_xticklabels(order, rotation=45, ha="right")
        ax.set_title(title, pad=4)
        # Read the headline quantity from the tested table rather than recomputing it
        # from the plotted means. Max-minus-min of seed-averaged means is a *different*
        # statistic from the seed-wise spread the paper reports (Jensen), and an earlier
        # draft annotated one while the text quoted the other -- they differed by 2x and
        # the figure's number happened to coincide with the text's tamilish-english gap.
        sing = float(disparity.loc[(disparity["policy"] == policy)
                                   & (disparity["track"] == "singlish"),
                                   "minus_english"].iloc[0])
        taml = float(disparity.loc[(disparity["policy"] == policy)
                                   & (disparity["track"] == "tamilish"),
                                   "minus_english"].iloc[0])
        ax.annotate(f"vs english:  singlish {sing:+.2f}\ntamilish {taml:+.2f} min",
                    xy=(0.5, 0.85), xycoords="axes fraction", ha="center",
                    fontsize=7, color=C_ACCENT)
    axes[0].set_ylabel("mean wait, gold-High (min)")
    fig.suptitle("Time-to-first-response for urgent tickets, by the script the customer "
                 "wrote in (ρ = 1.05)", y=1.06)
    # The legend names the encoding rather than repeating the axis labels.
    fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=C_NATIVE),
                        plt.Rectangle((0, 0), 1, 1, color=C_ROMAN)],
               labels=["native script", "romanized"], frameon=False,
               ncol=2, loc="lower center", bbox_to_anchor=(0.5, -0.22))
    save(fig, "queue_disparity")


def fig_alpha_frontier() -> None:
    """Urgency against starvation. A frontier, because the choice is the desk's."""
    path = TABLES / "tus_alpha_frontier.csv"
    if not path.exists():
        print("  SKIP alpha_frontier -- run run_system_eval.py first")
        return
    d = pd.read_csv(path, comment="#").sort_values("alpha")
    fig, ax = plt.subplots(figsize=(ONE_COL, 2.5))
    ax.plot(d["high_mean_wait"], d["low_p95_wait"], "-o", color=C_NEUTRAL,
            markersize=3.5, linewidth=1)
    for _, r in d.iterrows():
        if r["alpha"] in (0.0, 1.0, 8.0, 16.0, 128.0):
            ax.annotate(f"α={r['alpha']:g}", xy=(r["high_mean_wait"], r["low_p95_wait"]),
                        xytext=(4, 3), textcoords="offset points", fontsize=7)
    fitted = d[d["alpha"] == 16.0]
    ax.plot(fitted["high_mean_wait"], fitted["low_p95_wait"], "o",
            color=C_ACCENT, markersize=6, zorder=3, label="fitted on dev")
    ax.set_xlabel("mean wait, gold-High (min)  →  worse")
    ax.set_ylabel("p95 wait, gold-Low (min)  →  worse")
    ax.legend(frameon=False, loc="upper right")
    ax.set_title("The aging term is a dial, not a constant", pad=4)
    save(fig, "alpha_frontier")


def fig_attainment() -> None:
    """How much of a perfect classifier's benefit the score already delivers."""
    path = TABLES / "tus_attainment.csv"
    if not path.exists():
        print("  SKIP attainment -- run run_system_eval.py first")
        return
    d = pd.read_csv(path, comment="#")
    metrics = ["high_mean_wait", "high_p95_wait", "sla_breach_rate", "rel_tardiness"]
    labels = ["mean wait\n(High)", "p95 wait\n(High)", "SLA breach\nrate",
              "relative\ntardiness"]
    fig, ax = plt.subplots(figsize=(ONE_COL, 2.4))
    width = 0.26
    for i, rho in enumerate(sorted(d["rho"].unique())):
        sub = d[d["rho"] == rho].set_index("metric").reindex(metrics)
        x = [j + (i - 1) * width for j in range(len(metrics))]
        ax.bar(x, sub["attainment"], width,
               yerr=[sub["attainment"] - sub["ci_lo"], sub["ci_hi"] - sub["attainment"]],
               ecolor=C_NEUTRAL, capsize=1.5, linewidth=0,
               color=plt.cm.Blues(0.4 + 0.25 * i), label=f"ρ = {rho}")
    ax.axhline(1.0, color=C_ACCENT, linewidth=0.8, linestyle="--")
    ax.annotate("perfect classifier", xy=(len(metrics) - 0.5, 1.0), xytext=(0, 3),
                textcoords="offset points", ha="right", fontsize=7, color=C_ACCENT)
    ax.set_xticks(range(len(metrics)))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("attainment  (FIFO−TUS)/(FIFO−oracle)")
    ax.legend(frameon=False, ncol=3, loc="lower center", fontsize=7)
    ax.set_title("Share of the achievable gain the score delivers", pad=4)
    save(fig, "attainment")


def main() -> None:
    print(f"writing figures to {FIGS.relative_to(REPO)}/")
    fig_encoder_gain_by_script()
    fig_per_language_sentiment()
    fig_ceiling()
    fig_tokenizer()
    fig_intent_epochs()
    fig_queue_disparity()
    fig_alpha_frontier()
    fig_attainment()


if __name__ == "__main__":
    main()
