# covid

Script to create COVID-19 datasets. View data [here](https://rwright-covid.herokuapp.com/).

## Sources

- https://covidtracking.com/data
- https://github.com/CSSEGISandData/COVID-19
- https://github.com/govex/COVID-19
- https://github.com/owid/covid-19-data/tree/master/public/data

## Sources by geography and type

Geography   | Type         | Source
------------|--------------|--------------------------------------------------------------
Countries   | Cases        | https://github.com/owid/covid-19-data/tree/master/public/data
Countries   | Deaths       | https://github.com/owid/covid-19-data/tree/master/public/data
Countries   | Tests        | https://github.com/owid/covid-19-data/tree/master/public/data
Countries   | Hospitalized | https://github.com/owid/covid-19-data/tree/master/public/data
Countries   | Vaccinations | https://github.com/owid/covid-19-data/tree/master/public/data
US states   | Cases        | https://covidtracking.com/data
US states   | Deaths       | https://covidtracking.com/data
US states   | Tests        | https://covidtracking.com/data
US states   | Hospitalized | https://covidtracking.com/data
US states   | Vaccinations | https://github.com/govex/COVID-19
US counties | Cases        | https://github.com/CSSEGISandData/COVID-19
US counties | Deaths       | https://github.com/CSSEGISandData/COVID-19
US counties | Tests        | NA
US counties | Hospitalized | NA
US counties | Vaccinations | NA

## Requirements

- Python 3.6
- lxml
- numpy
- pandas
- requests
