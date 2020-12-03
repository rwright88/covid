# covid

Create COVID-19 datasets.

## Sources

- https://covidtracking.com/data
- https://github.com/CSSEGISandData/COVID-19
- https://github.com/owid/covid-19-data/tree/master/public/data

## Sources by geography and type

Geography         | Type         | Source
------------------|--------------|--------------------------------------------------------------
Countries         | Cases        | https://github.com/CSSEGISandData/COVID-19
Countries         | Deaths       | https://github.com/CSSEGISandData/COVID-19
Countries, non-US | Tests        | https://github.com/owid/covid-19-data/tree/master/public/data
Countries, non-US | Hospitalized | NA
US                | Tests        | https://covidtracking.com/data
US                | Hospitalized | https://covidtracking.com/data
US states         | Cases        | https://covidtracking.com/data
US states         | Deaths       | https://covidtracking.com/data
US states         | Tests        | https://covidtracking.com/data
US states         | Hospitalized | https://covidtracking.com/data
US counties       | Cases        | https://github.com/CSSEGISandData/COVID-19
US counties       | Deaths       | https://github.com/CSSEGISandData/COVID-19
US counties       | Tests        | NA
US counties       | Hospitalized | NA

## Requirements

- Python 3.6
- lxml
- numpy
- pandas
- requests
