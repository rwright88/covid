"""Create datasets"""

import os

import numpy as np
import pandas as pd

import covidpa as cp

N = 7
OUT_US = "out/us.csv"
OUT_PA = "out/pa.csv"

if __name__ == "__main__":
    dir_name = os.path.dirname(OUT_US)
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name, exist_ok=True)
    df = cp.get_data(n=N)
    df = df.round(2)
    df.to_csv(OUT_US, index=False)
    pa = df[(df["name"] == "pa") | df["name"].str.contains("pa, ")]
    pa.to_csv(OUT_PA, index=False)

