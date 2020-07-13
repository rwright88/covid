"""Functions to create datasets."""
# TODO: Should county rows with missing code or name be excluded? (currently yes)
# TODO: County sums don't always equal state

import io

import numpy as np
import pandas as pd
import requests

from covidpa.utils import fill_dates

IN_COUNTRY_CASES = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
IN_COUNTRY_DEATHS = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"
IN_COUNTRY_POP = (
    "https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)"
)
IN_COUNTY_CASES = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"
IN_COUNTY_DEATHS = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv"
IN_STATE_CW = "data/state-postal.csv"
IN_STATE_TESTS = "http://covidtracking.com/api/states/daily.csv"


def get_data(n=7):
    """Get cases, deaths, and tests data"""
    county_cases = get_county(IN_COUNTY_CASES, value_name="cases")
    county_deaths = get_county(IN_COUNTY_DEATHS, value_name="deaths")
    by = ["code", "county", "state", "date"]
    df = pd.merge(county_cases, county_deaths, how="left", on=by)
    df["type"] = "county"
    df = sum_state(df)
    tests = get_state_testing(IN_STATE_TESTS)
    df = pd.merge(df, tests, how="left", on=["name", "date"])
    df = sum_us(df)

    country_cases = get_country(IN_COUNTRY_CASES, value_name="cases")
    country_deaths = get_country(IN_COUNTRY_DEATHS, value_name="deaths")
    country = pd.merge(country_cases, country_deaths, how="left", on=["name", "date"])
    country = country[country["name"] != "us"]
    country["type"] = "country"
    country_pop = get_country_pop(IN_COUNTRY_POP)
    country = pd.merge(country, country_pop, how="left", on="name")
    df = pd.concat([df, country], ignore_index=True)

    df = df[df["date"] >= "2020-03-01"]
    df = calc_stats(df, n=n)
    return df


def get_county(file1, value_name="cases"):
    """Get cases or deaths county data from Johns Hopkins CSV file"""
    df = pd.read_csv(file1)
    cols_id = {"code": "FIPS", "county": "Admin2", "state": "Province_State"}
    if value_name == "cases":
        cols_dates = {x: x for x in df.columns.tolist()[11:]}
    elif value_name == "deaths":
        cols_id["pop"] = "Population"
        cols_dates = {x: x for x in df.columns.tolist()[12:]}
    cols = {**cols_id, **cols_dates}
    df = df[cols.values()]
    df.columns = cols.keys()
    df = df[df["code"].notna() & df["county"].notna()]
    df = pd.melt(df, id_vars=cols_id, var_name="date", value_name=value_name)
    df["code"] = fix_fips(df["code"])
    df["date"] = pd.to_datetime(df["date"])
    for col in ["county", "state"]:
        df[col] = fix_string(df[col])
    return df


def sum_state(df):
    """Sum state data from Johns Hopkins county data and combine"""
    cw = pd.read_csv(IN_STATE_CW)
    cw["state_code"] = cw["state_code"].str.lower()
    df = pd.merge(df, cw, how="left", left_on="state", right_on="state_name")
    df = df[["type", "code", "state_code", "county", "date", "pop", "cases", "deaths"]]
    state = df.groupby(["state_code", "date"]).sum().reset_index()
    state["type"] = "state"
    df = pd.concat([df, state], ignore_index=True)
    df["name"] = combine_state_county(df["type"], df["state_code"], df["county"])
    df = df[["type", "code", "name", "date", "pop", "cases", "deaths"]]
    return df


def get_state_testing(url):
    """Get state testing data from Covid Tracking project"""
    r = requests.get(url)
    data = io.StringIO(r.text)
    df = pd.read_csv(data)
    df = df[["state", "date", "positive", "negative"]]
    df.columns = ["name", "date", "cases", "negative"]
    df["tests"] = df["cases"] + df["negative"]
    df = df.drop(["cases", "negative"], axis=1)
    df["date"] = pd.to_datetime(df["date"].astype(str))
    df["name"] = fix_string(df["name"])
    df = fill_dates(df, name="name")
    return df


def sum_us(df):
    """Sum US data from state data and combine"""
    state = df[df["type"] == "state"]
    us = state.groupby("date").sum().reset_index()
    us["name"] = "us"
    us["type"] = "country"
    df = pd.concat([df, us], ignore_index=True)
    return df


def get_country(file1, value_name="cases"):
    """Get cases or deaths country data from Johns Hopkins CSV file"""
    df = pd.read_csv(file1)
    cols_id = {"name": "Country/Region"}
    cols_dates = cols_dates = {x: x for x in df.columns.tolist()[4:]}
    cols = {**cols_id, **cols_dates}
    df = df[cols.values()]
    df.columns = cols.keys()
    df = pd.melt(df, id_vars=cols_id, var_name="date", value_name=value_name)
    df["date"] = pd.to_datetime(df["date"])
    df["name"] = fix_country(df["name"])
    df = df.groupby(["name", "date"]).sum().reset_index()
    return df


def get_country_pop(url):
    """Get country populations from Wikipedia"""
    r = requests.get(url)
    df = pd.read_html(r.text)[3]
    df = df.iloc[:, [0, 4]]
    df.columns = ["name", "pop"]
    df["name"] = fix_country(df["name"])
    df["pop"] = pd.to_numeric(df["pop"])
    return df


def calc_stats(df, n=7):
    """Calculate average daily change and per million stats"""
    df = df.sort_values("date")
    cols_cume = ["cases", "tests", "deaths"]
    cols_to_rate = ["cases", "tests", "deaths", "cases_ac", "tests_ac", "deaths_ac"]
    out = []
    ind = df.groupby(["type", "name"]).indices
    for k, v in ind.items():
        df1 = df.iloc[v].copy()
        for col in cols_cume:
            df1[col + "_ac"] = average_change(df1[col], n=n)
        out.append(df1)
    out = pd.concat(out, ignore_index=True)
    for col in cols_to_rate:
        out[col + "_pm"] = out[col] / out["pop"] * 1e06
    return out


def fix_fips(x):
    return [str(int(e)).zfill(5) for e in x]


def fix_string(x):
    out = x.str.lower()
    out = out.str.replace("\[[^\]]*\]", "")
    out = out.str.strip()
    return out


def fix_country(x):
    out = fix_string(x)
    out[out == "korea, south"] = "south korea"
    out[out.str.contains("taiwan")] = "taiwan"
    return out


def combine_state_county(type1, state, county):
    out = [
        s + ", " + c if t == "county" else s for t, s, c in zip(type1, state, county)
    ]
    return out


def average_change(x, n=7):
    """Calculate average change"""
    return (x - x.shift(n)) / n

