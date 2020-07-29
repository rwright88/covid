"""Functions to create datasets."""
# TODO: Should county rows with missing code or name be excluded? (currently yes)

import io

import numpy as np
import pandas as pd
import requests

from covidpa.utils import fill_dates

IN_COUNTRY_CASES = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
IN_COUNTRY_DEATHS = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"
IN_COUNTRY_POP = (
    "https://en.wikipedia.org/wiki/List_of_countries_and_dependencies_by_population"
)
IN_COUNTY_CASES = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"
IN_COUNTY_DEATHS = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv"
IN_STATE = "http://covidtracking.com/api/states/daily.csv"
IN_STATE_CW = "data/state-postal.csv"
IN_STATE_POP = "https://en.wikipedia.org/wiki/List_of_states_and_territories_of_the_United_States_by_population"


def get_data(n=7):
    """Get cases, deaths, and tests data for countries, states, and counties"""
    county_cases = get_county(IN_COUNTY_CASES, value_name="cases")
    county_deaths = get_county(IN_COUNTY_DEATHS, value_name="deaths")
    by = ["code", "county", "state", "date"]
    df = pd.merge(county_cases, county_deaths, how="left", on=by)
    cw = pd.read_csv(IN_STATE_CW)
    cw["state_code"] = fix_string(cw["state_code"])
    df = pd.merge(df, cw, how="left", left_on="state", right_on="state_name")
    df["name"] = [s + ", " + c for s, c in zip(df["state_code"], df["county"])]
    df["type"] = "county"
    df = df[["type", "code", "name", "date", "pop", "cases", "deaths"]]

    state = get_state(IN_STATE)
    state_pop = get_state_pop(IN_STATE_POP)
    state_pop = pd.merge(
        state_pop, cw, how="left", left_on="name", right_on="state_name"
    )
    state_pop = state_pop[["state_code", "pop"]]
    state = pd.merge(
        state, state_pop, how="left", left_on="name", right_on="state_code"
    ).drop("state_code", axis=1)
    df = pd.concat([df, state], ignore_index=True)

    us_tests = state[["date", "tests"]].groupby("date").sum().reset_index()
    us_tests["name"] = "united states"

    country_cases = get_country(IN_COUNTRY_CASES, value_name="cases")
    country_deaths = get_country(IN_COUNTRY_DEATHS, value_name="deaths")
    country = pd.merge(country_cases, country_deaths, how="left", on=["name", "date"])
    country["type"] = "country"
    country_pop = get_country_pop(IN_COUNTRY_POP)
    country = pd.merge(country, country_pop, how="left", on="name")
    country = pd.merge(country, us_tests, how="left", on=["name", "date"])
    df = pd.concat([df, country], ignore_index=True)

    world = df[df["type"] == "country"].groupby("date").sum().reset_index()
    world["name"] = "world"
    world["type"] = "country"
    world = world.drop("tests", axis=1)
    df = pd.concat([df, world], ignore_index=True)

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
    df["code"] = [str(int(e)).zfill(5) for e in df["code"]]
    df["county"] = fix_string(df["county"])
    df["date"] = pd.to_datetime(df["date"])
    df["state"] = fix_string(df["state"])
    return df


def get_state(url):
    """Get state data from Covid Tracking project"""
    r = requests.get(url)
    data = io.StringIO(r.text)
    df = pd.read_csv(data)
    df = df[["fips", "state", "date", "positive", "negative", "death"]]
    df.columns = ["code", "name", "date", "cases", "negative", "deaths"]
    df["code"] = [str(int(e)).zfill(2) for e in df["code"]]
    df["date"] = pd.to_datetime(df["date"].astype(str))
    df["name"] = fix_string(df["name"])
    df["tests"] = df["cases"] + df["negative"]
    df["type"] = "state"
    df = df[["type", "code", "name", "date", "cases", "tests", "deaths"]]
    # df = fill_dates(df, name="name")
    return df


def get_state_pop(url):
    """Get state populations from Wikipedia"""
    r = requests.get(url)
    df = pd.read_html(r.text)[0]
    df = df.iloc[:52, [2, 3]]
    df.columns = ["name", "pop"]
    df["name"] = fix_string(df["name"])
    df["pop"] = pd.to_numeric(df["pop"])
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
    df = pd.read_html(r.text)[0]
    df = df.iloc[:, [1, 2]]
    df.columns = ["name", "pop"]
    df["name"] = fix_country(df["name"])
    df["pop"] = pd.to_numeric(df["pop"])
    return df


def calc_stats(df, n=7):
    """Calculate average daily change and per million stats"""
    df = df.sort_values("date")
    out = []
    ind = df.groupby(["type", "name"]).indices
    for k, v in ind.items():
        df1 = df.iloc[v].copy()
        for col in ["cases", "tests", "deaths"]:
            df1[col + "_ac"] = average_change(df1[col], n=n)
        out.append(df1)
    out = pd.concat(out, ignore_index=True)
    out["positivity"] = out["cases"] / out["tests"] * 100
    out["positivity_ac"] = out["cases_ac"] / out["tests_ac"] * 100
    cols_to_rate = ["cases", "tests", "deaths", "cases_ac", "tests_ac", "deaths_ac"]
    for col in cols_to_rate:
        out[col + "_pm"] = out[col] / out["pop"] * 1e06
    return out


def fix_string(x):
    out = x.str.lower()
    out = out.str.replace("\[[^\]]*\]", "")
    out = out.str.strip()
    return out


def fix_country(x):
    out = fix_string(x)
    out[out == "czech republic"] = "czechia"
    out[out == "burma"] = "myanmar"
    out[out == "korea, south"] = "south korea"
    out[out.str.contains("taiwan")] = "taiwan"
    out[out == "us"] = "united states"
    return out


def average_change(x, n=7):
    """Calculate average change"""
    return (x - x.shift(n)) / n

