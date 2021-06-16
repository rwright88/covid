"""Functions to create datasets."""

import datetime

import numpy as np
import pandas as pd
import requests

from covid.utils import fill_dates

IN_STATE_POSTAL = "data/state-postal.csv"


def get_data(n=7):
    """Get covid data for countries, states, and counties"""
    state_postal = pd.read_csv(IN_STATE_POSTAL)
    state_postal["state_code"] = fix_string(state_postal["state_code"])

    county_cases = get_county(value_name="cases")
    county_deaths = get_county(value_name="deaths")
    by = ["code", "county", "state", "date"]
    df = pd.merge(county_cases, county_deaths, how="left", on=by)
    df = pd.merge(df, state_postal, how="left", left_on="state", right_on="state_name")
    df["name"] = [s + ", " + c for s, c in zip(df["state_code"], df["county"])]
    df["type"] = "county"
    df = df[["type", "code", "name", "date", "pop", "cases", "deaths"]]

    state_cases_deaths = get_state_cases_deaths()
    state_tests = get_state_tests()
    state_hosp = get_state_hosp()
    state_vacc = get_state_vaccs()
    state_vacc = pd.merge(
        state_vacc, state_postal, how="left", left_on="state", right_on="state_name"
    )[["state_code", "date", "vaccinations"]]
    state_vacc.columns = ["name", "date", "vaccinations"]
    state_pop = get_state_pop()
    state_pop = pd.merge(
        state_pop, state_postal, how="left", left_on="name", right_on="state_name"
    )[["state_code", "pop"]]
    state_pop.columns = ["name", "pop"]
    by = ["name", "date"]
    state = pd.merge(state_cases_deaths, state_tests, how="outer", on=by)
    state = pd.merge(state, state_hosp, how="outer", on=by)
    state = pd.merge(state, state_vacc, how="outer", on=by)
    state = pd.merge(state, state_pop, how="left", on="name")
    state["type"] = "state"
    df = pd.concat([df, state], ignore_index=True)

    country = get_country()
    country["type"] = "country"
    country_pop = get_country_pop()
    country = pd.merge(country, country_pop, how="left", on="name")
    df = pd.concat([df, country], ignore_index=True)

    df = calc_stats(df, n=n)
    return df


def get_county(value_name="cases"):
    """Get cases or deaths county data from Johns Hopkins"""
    cols_id = {"code": "FIPS", "county": "Admin2", "state": "Province_State"}
    if value_name == "cases":
        path = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"
        df = pd.read_csv(path)
        cols_dates = {x: x for x in df.columns.tolist()[11:]}
    elif value_name == "deaths":
        path = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv"
        df = pd.read_csv(path)
        cols_id["pop"] = "Population"
        cols_dates = {x: x for x in df.columns.tolist()[12:]}
    else:
        raise ValueError("Invalid value_name")
    cols = {**cols_id, **cols_dates}
    df = df[cols.values()]
    df.columns = cols.keys()
    df = df[df["code"].notna() & df["county"].notna()]
    df = pd.melt(df, id_vars=cols_id, var_name="date", value_name=value_name)
    df["code"] = [str(int(e)).zfill(5) for e in df["code"]]
    df["county"] = fix_string(df["county"])
    df["state"] = fix_string(df["state"])
    df["date"] = fix_date(df["date"])
    return df


def get_state_cases_deaths():
    """Get cases and deaths state data from CDC"""
    path = "https://data.cdc.gov/api/views/9mfq-cb36/rows.csv?accessType=DOWNLOAD"
    cols = {
        "name": "state",
        "date": "submission_date",
        "cases": "tot_cases",
        "deaths": "tot_death",
    }
    df = pd.read_csv(path)
    df = df[cols.values()]
    df.columns = cols.keys()
    df["name"] = fix_state(df["name"])
    df["date"] = fix_date(df["date"])
    df = df.groupby(["name", "date"]).sum(min_count=1).reset_index()
    # df = fill_dates(df, name="name")
    return df


def get_state_tests():
    """Get tests state data from HHS"""
    path = "https://beta.healthdata.gov/api/views/j8mb-icvb/rows.csv?accessType=DOWNLOAD"
    cols = {
        "name": "state",
        "date": "date",
        "tests": "total_results_reported",
    }
    df = pd.read_csv(path)
    df = df[cols.values()]
    df.columns = cols.keys()
    df["name"] = fix_state(df["name"])
    df["date"] = fix_date(df["date"])
    df = df.groupby(["name", "date"]).sum(min_count=1).reset_index()
    # df = fill_dates(df, name="name")
    return df


def get_state_hosp():
    """Get hospitalization state data from HHS"""
    path = (
        "https://beta.healthdata.gov/api/views/g62h-syeh/rows.csv?accessType=DOWNLOAD"
    )
    cols = {
        "name": "state",
        "date": "date",
        "hosp_adult": "total_adult_patients_hospitalized_confirmed_and_suspected_covid",
        "hosp_pediatric": "total_pediatric_patients_hospitalized_confirmed_and_suspected_covid",
    }
    df = pd.read_csv(path)
    df = df[cols.values()]
    df.columns = cols.keys()
    df["name"] = fix_state(df["name"])
    df["date"] = fix_date(df["date"])
    df["hosp"] = df["hosp_adult"] + df["hosp_pediatric"]
    df = df.drop(["hosp_adult", "hosp_pediatric"], axis=1)
    df = df.groupby(["name", "date"]).sum(min_count=1).reset_index()
    # df = fill_dates(df, name="name")
    return df


def get_state_vaccs():
    """Get vaccination state data from Centers for Civic Impact"""
    path = "https://raw.githubusercontent.com/govex/COVID-19/master/data_tables/vaccine_data/us_data/time_series/vaccine_data_us_timeline.csv"
    cols = {
        "state": "Province_State",
        "date": "Date",
        "vaccine_type": "Vaccine_Type",
        "vaccinations": "Stage_One_Doses",
    }
    df = pd.read_csv(path)
    df = df[cols.values()]
    df.columns = cols.keys()
    df = df[df["vaccine_type"] == "All"].drop("vaccine_type", axis=1)
    df["date"] = fix_date(df["date"])
    df["state"] = fix_string(df["state"])
    df = df.drop_duplicates(["state", "date"])
    # df = fill_dates(df, name="name")
    return df


def get_state_pop():
    """Get state populations from Wikipedia"""
    url = "https://en.wikipedia.org/wiki/List_of_states_and_territories_of_the_United_States_by_population"
    r = requests.get(url)
    df = pd.read_html(r.text)[0]
    df = df.iloc[:52, [2, 3]]
    df.columns = ["name", "pop"]
    df["name"] = fix_string(df["name"])
    df["pop"] = pd.to_numeric(df["pop"], errors="coerce")
    return df


def get_country():
    """Get country data from Our World in Data"""
    path = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv"
    cols = {
        "code": "iso_code",
        "name": "location",
        "date": "date",
        "cases": "total_cases",
        "deaths": "total_deaths",
        "tests": "total_tests",
        "hosp": "hosp_patients",
        "vaccinations": "people_vaccinated",
    }
    df = pd.read_csv(path)
    df = df[cols.values()]
    df.columns = cols.keys()
    df["date"] = fix_date(df["date"])
    df["name"] = fix_country(df["name"])
    return df


def get_country_pop():
    """Get country populations from Wikipedia"""
    url = (
        "https://en.wikipedia.org/wiki/List_of_countries_and_dependencies_by_population"
    )
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


def fix_date(x):
    date_min = datetime.date(year=2020, month=1, day=1).strftime(r"%Y-%m-%d")
    date_max = datetime.date.today().strftime(r"%Y-%m-%d")
    out = pd.to_datetime(x)
    out[out < date_min] = date_min
    out[out > date_max] = date_max
    return out


def fix_string(x):
    out = x.str.lower()
    out = out.str.replace("\[[^\]]*\]", "", regex=True)
    out = out.str.replace("†", "", regex=True)
    out = out.str.strip()
    return out


def fix_state(x):
    out = fix_string(x)
    out[out == "nyc"] = "ny"
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
