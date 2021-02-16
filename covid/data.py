"""Functions to create datasets."""

import io

import numpy as np
import pandas as pd
import requests

from covid.utils import fill_dates

IN_COUNTRY_CASES = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
IN_COUNTRY_DEATHS = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"
IN_COUNTRY_TESTS = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv"
IN_COUNTRY_POP = (
    "https://en.wikipedia.org/wiki/List_of_countries_and_dependencies_by_population"
)
IN_COUNTY_CASES = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"
IN_COUNTY_DEATHS = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv"
IN_STATE = "http://covidtracking.com/api/states/daily.csv"
IN_STATE_CW = "data/state-postal.csv"
IN_STATE_POP = "https://en.wikipedia.org/wiki/List_of_states_and_territories_of_the_United_States_by_population"
IN_STATE_VACC = "https://raw.githubusercontent.com/govex/COVID-19/master/data_tables/vaccine_data/us_data/time_series/vaccine_data_us_timeline.csv"


def get_data(n=7):
    """Get covid data for countries, states, and counties"""
    county_cases = get_county(IN_COUNTY_CASES, value_name="cases")
    county_deaths = get_county(IN_COUNTY_DEATHS, value_name="deaths")
    by = ["code", "county", "state", "date"]
    df = pd.merge(county_cases, county_deaths, how="left", on=by)
    state_cw = pd.read_csv(IN_STATE_CW)
    state_cw["state_code"] = fix_string(state_cw["state_code"])
    df = pd.merge(df, state_cw, how="left", left_on="state", right_on="state_name")
    df["name"] = [s + ", " + c for s, c in zip(df["state_code"], df["county"])]
    df["type"] = "county"
    df = df[["type", "code", "name", "date", "pop", "cases", "deaths"]]

    state = get_state(IN_STATE)
    state_vacc = get_state_vaccs(IN_STATE_VACC)
    state_vacc = pd.merge(
        state_vacc, state_cw, how="left", left_on="state", right_on="state_name"
    )
    state_vacc = state_vacc[["state_code", "date", "vaccinations"]]
    state_vacc.columns = ["name", "date", "vaccinations"]
    state = pd.merge(state, state_vacc, how="left", on=["name", "date"])
    state_pop = get_state_pop(IN_STATE_POP)
    state_pop = pd.merge(
        state_pop, state_cw, how="left", left_on="name", right_on="state_name"
    )
    state_pop = state_pop[["state_code", "pop"]]
    state = pd.merge(
        state, state_pop, how="left", left_on="name", right_on="state_code"
    ).drop("state_code", axis=1)
    df = pd.concat([df, state], ignore_index=True)

    us_tests = state[["date", "tests"]].groupby("date").sum().reset_index()
    us_tests["name"] = "united states"
    country_tv = get_country_tests_vaccs(IN_COUNTRY_TESTS)
    country_tests = country_tv[country_tv["name"] != "united states"].drop(
        "vaccinations", axis=1
    )
    country_tests = pd.concat([country_tests, us_tests], ignore_index=True)

    us_hosp = state[["date", "hosp"]].groupby("date").sum().reset_index()
    us_hosp["name"] = "united states"

    country_vacc = country_tv.drop("tests", axis=1)

    country_cases = get_country(IN_COUNTRY_CASES, value_name="cases")
    country_deaths = get_country(IN_COUNTRY_DEATHS, value_name="deaths")
    country = pd.merge(country_cases, country_deaths, how="left", on=["name", "date"])
    country["type"] = "country"
    country_pop = get_country_pop(IN_COUNTRY_POP)
    country = pd.merge(country, country_pop, how="left", on="name")
    country = pd.merge(country, country_tests, how="left", on=["name", "date"])
    country = pd.merge(country, us_hosp, how="left", on=["name", "date"])
    country = pd.merge(country, country_vacc, how="left", on=["name", "date"])
    df = pd.concat([df, country], ignore_index=True)

    world = df[df["type"] == "country"].groupby("date").sum().reset_index()
    world["name"] = "world"
    world["type"] = "country"
    world = world.drop(["tests", "hosp", "vaccinations"], axis=1)
    df = pd.concat([df, world], ignore_index=True)

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
    col = df.columns.tolist()
    df["type"] = "state"
    df = df[["type"] + col]
    # df = fill_dates(df, name="name")
    return df


def get_state_vaccs(file1):
    """Get vaccination state data from Centers for Civic Impact"""
    cols = {
        "state": "Province_State",
        "date": "Date",
        "vaccine_type": "Vaccine_Type",
        "vaccinations": "Stage_One_Doses",
    }
    df = pd.read_csv(file1)
    df = df[cols.values()]
    df.columns = cols.keys()
    df = df[df["vaccine_type"] == "All"].drop("vaccine_type", axis=1)
    df["date"] = pd.to_datetime(df["date"])
    df["state"] = fix_string(df["state"])
    df = df.drop_duplicates(["state", "date"])
    return df


def get_state_pop(url):
    """Get state populations from Wikipedia"""
    r = requests.get(url)
    df = pd.read_html(r.text)[0]
    df = df.iloc[:52, [2, 3]]
    df.columns = ["name", "pop"]
    df["name"] = fix_string(df["name"])
    df["pop"] = pd.to_numeric(df["pop"], errors="coerce")
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


def get_country_tests_vaccs(file1):
    """Get tests/vaccinations country data from Our World in Data CSV file"""
    cols = {
        "name": "location",
        "date": "date",
        "tests": "total_tests",
        "vaccinations": "people_vaccinated",
    }
    df = pd.read_csv(file1)
    df = df[cols.values()]
    df.columns = cols.keys()
    df["date"] = pd.to_datetime(df["date"])
    df["name"] = fix_country(df["name"])
    return df


def get_country_pop(url):
    """Get country populations from Wikipedia"""
    r = requests.get(url)
    df = pd.read_html(r.text)[0]
    df = df.iloc[:, [1, 2]]
    df.columns = ["name", "pop"]
    df["name"] = fix_country(df["name"])
    df["pop"] = pd.to_numeric(df["pop"], errors="coerce")
    return df


def calc_stats(df, n=7):
    """Calculate average daily change and per million stats"""
    df = df.sort_values("date")
    ind = df.groupby(["type", "name"]).indices
    out = []
    for k, v in ind.items():
        df1 = df.iloc[v].copy()
        for col in ["cases", "deaths", "tests", "vaccinations"]:
            df1[col + "_ac"] = average_change(df1[col], n=n)
        df1["hosp_a"] = df1["hosp"].rolling(n).mean()
        out.append(df1)
    out = pd.concat(out, ignore_index=True)
    cols_rate = [
        "cases_ac",
        "cases",
        "deaths_ac",
        "deaths",
        "hosp_a",
        "hosp",
        "tests_ac",
        "tests",
        "vaccinations_ac",
        "vaccinations",
    ]
    for col in cols_rate:
        out[col + "_pm"] = out[col] / out["pop"] * 1e06
    return out


def fix_string(x):
    out = x.str.lower()
    out = out.str.replace("\[[^\]]*\]", "")
    out = out.str.strip()
    return out


def fix_country(x):
    out = fix_string(x)
    out[out == "congo (brazzaville)"] = "congo"
    out[out == "czechia"] = "czech republic"
    out[out == "congo (kinshasa)"] = "dr congo"
    out[out == "democratic republic of congo"] = "dr congo"
    out[out == "cote d'ivoire"] = "ivory coast"
    out[out == "burma"] = "myanmar"
    out[out == "korea, south"] = "south korea"
    out[out.str.contains("taiwan")] = "taiwan"
    out[out == "us"] = "united states"
    return out


def average_change(x, n=7):
    """Calculate average change"""
    return (x - x.shift(n)) / n
