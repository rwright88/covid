"""Functions to create datasets."""

import numpy as np
import pandas as pd

# from utils import fill_dates


def get_data(n=7):
    """Get Johns Hopkins cases and deaths data and combine"""
    in_cases = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"
    in_deaths = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv"
    cases = get_cases_or_deaths(in_cases, value_name="cases")
    deaths = get_cases_or_deaths(in_deaths, value_name="deaths")
    df = pd.merge(cases, deaths, how="left", on=["fips", "name", "date"])
    # df = fill_dates(df, "name")
    df = calc_stats(df, n=n)
    return df


def get_cases_or_deaths(file1, value_name="cases"):
    """Get cases or deaths data from Johns Hopkins CSV file"""
    df = pd.read_csv(file1)
    if value_name == "cases":
        cols_id = {"fips": "FIPS", "name": "Combined_Key"}
        cols_dates = {x: x for x in df.columns.tolist()[11:]}
    elif value_name == "deaths":
        cols_id = {"fips": "FIPS", "name": "Combined_Key", "pop": "Population"}
        cols_dates = {x: x for x in df.columns.tolist()[12:]}
    cols = {**cols_id, **cols_dates}
    df = df[cols.values()]
    df.columns = cols.keys()
    df = df[df["fips"].notna()]
    df = pd.melt(df, id_vars=cols_id, var_name="date", value_name=value_name)
    df["date"] = pd.to_datetime(df["date"])
    # df["fips"] = fix_string(df["fips"])
    df["name"] = fix_string(df["name"])
    return df


def fix_fips(x):
    x = x.copy()
    x = x.astype(str)
    x = [e.zfill(5) for e in x]
    return x


def fix_string(x):
    return x.str.lower().str.strip()


def calc_stats(df, n=7):
    """Calculate average daily change and per million stats"""
    df = df.sort_values("date")
    cols_cume = ["cases", "deaths"]
    cols_to_rate = ["cases", "deaths", "cases_ac", "deaths_ac"]
    out = []
    ind = df.groupby(["fips"]).indices
    for k, v in ind.items():
        df1 = df.iloc[v].copy()
        for col in cols_cume:
            df1[col + "_ac"] = average_change(df1[col], n=n)
        out.append(df1)
    out = pd.concat(out, ignore_index=True)
    for col in cols_to_rate:
        out[col + "_pm"] = out[col] / out["pop"] * 1e06
    return out


def average_change(x, n=7):
    """Calculate average change"""
    return (x - x.shift(n)) / n

