"""Create datasets"""

import os

import numpy as np
import pandas as pd

import covidpa as cp
from covidpa.utils import profile, summary

N = 7
OUT_DATA = "out/data.csv"

if __name__ == "__main__":
    dir_name = os.path.dirname(OUT_DATA)
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name, exist_ok=True)
    profile("df = cp.get_data(n=N)")
    summary(df)
    df.to_csv(OUT_DATA, index=False)

