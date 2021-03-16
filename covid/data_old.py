"""Functions to create datasets, Covid Tracking Project"""

import io

import numpy as np
import pandas as pd
import requests

from covid.utils import fill_dates


def get_state():
    """Get state data from Covid Tracking project"""
    url = "http://covidtracking.com/api/states/daily.csv"
    r = requests.get(url)
    data = io.StringIO(r.text)
    df = pd.read_csv(data)
    col = {
        "code": "fips",
        "name": "state",
        "date": "date",
        "cases": "positive",
        "deaths": "death",
        "tests": "totalTestResults",
        "hosp": "hospitalizedCurrently",
    }
    df = df[col.values()]
    df.columns = col.keys()
    df["code"] = [str(int(e)).zfill(2) for e in df["code"]]
    df["date"] = pd.to_datetime(df["date"].astype(str))
    df["name"] = fix_string(df["name"])
    # df = fill_dates(df, name="name")
    return df
