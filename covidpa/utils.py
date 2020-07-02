"""Utilities"""

import cProfile
from itertools import product
import os
import pstats

import numpy as np
import pandas as pd


def ffill(x):
    """Fill missing values with last non-missing value, 1-d"""
    mask = np.isnan(x)
    ind = np.where(~mask, np.arange(len(mask)), 0)
    np.maximum.accumulate(ind, out=ind)
    out = x[ind]
    return out


def fill_dates(df, name):
    """Fill missing dates in data frame for each name"""
    by = [name, "date"]
    names = df[name].unique()
    dates = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
    template = list(product(names, dates))
    template = pd.DataFrame(template, columns=by)
    df = pd.merge(template, df, how="left", on=by)
    # df = df.sort_values(by)
    return df


def profile(x, n=10):
    """Profile code using cProfile"""
    tf = "zzz-temp.txt"
    cProfile.run(x, tf)
    p = pstats.Stats(tf)
    os.remove(tf)
    p.strip_dirs().sort_stats(pstats.SortKey.CUMULATIVE).print_callees(n)


def summary(df, probs=[0, 0.25, 0.5, 0.75, 1]):
    """Summary of pandas dataframe"""
    if df.columns.size == 0:
        raise ValueError("df must have at least one column")

    _validate_probs(probs)

    probs_str = ["p" + str(round(p * 100)) for p in probs]
    cols = df.columns.tolist()
    types = df.dtypes.tolist()
    out = []

    for i, col in enumerate(cols):
        x = df[col]
        type1 = types[i]
        numeric = pd.api.types.is_numeric_dtype(x) or pd.api.types.is_bool_dtype(x)
        if numeric:
            res = _summary_numeric(x, probs=probs)
            quantiles = {p: q for p, q in zip(probs_str, res["quantiles"])}
            del res["quantiles"]
            res = {"name": col, "type": type1, **res, **quantiles}
        else:
            res = _summary_other(x)
            res = {"name": col, "type": type1, **res}
        out.append(res)

    out = pd.DataFrame(out)
    return out


def _summary_numeric(x, probs=[0, 0.25, 0.5, 0.75, 1]):
    """Summary of 1-d pandas numeric Series"""
    x = x.astype(np.float64)
    size = x.shape[0]
    nas = np.isnan(x)
    n_nas = np.sum(nas)
    na_ratio = n_nas / size

    if n_nas == size:
        m = np.nan
        q = np.full(size, np.nan)
        out = {"size": size, "na_ratio": na_ratio, "mean": m, "quantiles": q}
        return out
    elif n_nas > 0:
        x = x[~nas]

    m = np.mean(x)
    q = np.quantile(x, probs)
    out = {"size": size, "na_ratio": na_ratio, "mean": m, "quantiles": q}
    return out


def _summary_other(x):
    """Summary of 1-d pandas non-numeric Series"""
    size = x.shape[0]
    nas = x.isna()
    n_nas = nas.sum()
    na_ratio = n_nas / size
    out = {"size": size, "na_ratio": na_ratio}
    return out


def _validate_probs(probs):
    probs = np.asarray(probs)
    if np.count_nonzero(probs < 0.0) or np.count_nonzero(probs > 1.0):
        raise ValueError("Probabilities must be in the range [0, 1]")
