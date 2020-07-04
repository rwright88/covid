"""Functions to create datasets."""

import numpy as np
import pandas as pd

IN_GEO = "data/state-postal.csv"


def get_data(n=7):
    """Get Johns Hopkins cases and deaths data and combine"""
    in_cases = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"
    in_deaths = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv"
    cases = get_county(in_cases, value_name="cases")
    deaths = get_county(in_deaths, value_name="deaths")
    df = pd.merge(cases, deaths, how="left", on=["fips", "county", "state", "date"])
    df = get_state(df)
    df = calc_stats(df, n=n)
    return df


def get_county(file1, value_name="cases"):
    """Get cases or deaths county data from Johns Hopkins CSV file"""
    df = pd.read_csv(file1)
    cols_id = {"fips": "FIPS", "county": "Admin2", "state": "Province_State"}
    if value_name == "cases":
        cols_dates = {x: x for x in df.columns.tolist()[11:]}
    elif value_name == "deaths":
        cols_id["pop"] = "Population"
        cols_dates = {x: x for x in df.columns.tolist()[12:]}
    cols = {**cols_id, **cols_dates}
    df = df[cols.values()]
    df.columns = cols.keys()
    df = df[df["fips"].notna() & df["county"].notna()]
    df = pd.melt(df, id_vars=cols_id, var_name="date", value_name=value_name)
    df["date"] = pd.to_datetime(df["date"])
    df["fips"] = fix_fips(df["fips"])
    for col in ["county", "state"]:
        df[col] = fix_string(df[col])
    df = df[df["date"] >= "2020-03-01"]
    return df


def fix_fips(x):
    return [str(int(e)).zfill(5) for e in x]


def fix_string(x):
    return x.str.lower().str.strip()


def get_state(df):
    """Get state data from county data"""
    cw = pd.read_csv(IN_GEO)
    cw["state_code"] = cw["state_code"].str.lower()
    df = pd.merge(df, cw, how="left", left_on="state", right_on="state_name")
    df_cols = ["fips", "state_code", "county", "date", "pop", "cases", "deaths"]
    df = df[df_cols]
    state = df.groupby(["state_code", "date"]).sum().reset_index()
    state_cols = state.columns.tolist()
    us = state.groupby("date").sum().reset_index()
    us["state_code"] = "us"
    us = us[state_cols]
    state = pd.concat([state, us], ignore_index=True)
    state["fips"] = ""
    state["county"] = ""
    state = state[df_cols]
    df = pd.concat([df, state], ignore_index=True)
    df["name"] = combine_state_county(df["state_code"], df["county"])
    df = df[["fips", "name", "date", "pop", "cases", "deaths"]]
    return df


def combine_state_county(state, county):
    out = [s + ", " + c if c != "" else s for s, c in zip(state, county)]
    return out


def calc_stats(df, n=7):
    """Calculate average daily change and per million stats"""
    df = df.sort_values("date")
    cols_cume = ["cases", "deaths"]
    cols_to_rate = ["cases", "deaths", "cases_ac", "deaths_ac"]
    out = []
    ind = df.groupby(["name"]).indices
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

