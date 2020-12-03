# covid estimated infections
# TODO: Unfinished
# https://covid19-projections.com/estimating-true-infections/
# https://www.microcovid.org/paper/all

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

IN_DATA = "../covid/out/covid.csv"


def est_infections(cases_ac, positivity_ac):
    """Estimated new infections"""
    delay = 7
    cases_ac = cases_ac.shift(-delay)
    positivity_ac = positivity_ac.shift(-delay) / 100
    return cases_ac * (16 * np.sqrt(positivity_ac) + 2.5)


def calc_stats(df, n=7):
    """TODO"""
    df = df.sort_values("date")
    out = []
    ind = df.groupby(["type", "name"]).indices
    for k, v in ind.items():
        df1 = df.iloc[v].copy()
        df1["infections_ac"] = est_infections(df1["cases_ac"], df1["positivity_ac"])
        df1["infections"] = np.cumsum(df1["infections_ac"])
        out.append(df1)
    out = pd.concat(out, ignore_index=True)
    cols_to_rate = ["infections", "infections_ac"]
    for col in cols_to_rate:
        out[col + "_pm"] = out[col] / out["pop"] * 1e06
    out["prevalence"] = out["infections_ac_pm"] * 7 / 1e04
    return out


def main():
    df = pd.read_csv(IN_DATA)
    df["date"] = pd.to_datetime(df["date"])
    df = calc_stats(df)

    ind = df["date"] == (df["date"].max() - pd.Timedelta(7, unit="D"))
    col = ["name", "date", "cases_ac_pm", "positivity_ac", "infections_ac_pm", "infections_pm", "prevalence"]
    df.loc[ind, col].sort_values("prevalence", ascending=False).iloc[:10]

    names = ["united states", "pa"]
    fig, ax = plt.subplots(figsize=(9, 5))
    for name in names:
        df1 = df[df["name"] == name]
        mask = df1["prevalence"].notna().to_numpy()
        x = df1["date"].to_numpy()[mask]
        y = df1["prevalence"].to_numpy()[mask]
        ax.plot(x, y, label=name)
    ax.grid()
    ax.legend()
    ax.set_title("Estimated prevalence (%)")
    plt.show()


if __name__ == "__main__":
    main()

