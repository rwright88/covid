# covid

Script to create COVID-19 datasets. View data [here](https://rwright-covid.herokuapp.com/).

## Sources

- https://beta.healthdata.gov/dataset/COVID-19-Diagnostic-Laboratory-Testing-PCR-Testing/j8mb-icvb
- https://beta.healthdata.gov/Hospital/COVID-19-Reported-Patient-Impact-and-Hospital-Capa/g62h-syeh
- https://data.cdc.gov/Case-Surveillance/United-States-COVID-19-Cases-and-Deaths-by-State-o/9mfq-cb36
- https://github.com/CSSEGISandData/COVID-19
- https://github.com/govex/COVID-19
- https://github.com/owid/covid-19-data/tree/master/public/data

## Sources by geography and type

Geography   | Type         | Source
------------|--------------|----------------------------------------------------------------------------------------------------
Countries   | Cases        | https://github.com/owid/covid-19-data/tree/master/public/data
Countries   | Deaths       | https://github.com/owid/covid-19-data/tree/master/public/data
Countries   | Tests        | https://github.com/owid/covid-19-data/tree/master/public/data
Countries   | Hospitalized | https://github.com/owid/covid-19-data/tree/master/public/data
Countries   | Vaccinations | https://github.com/owid/covid-19-data/tree/master/public/data
US states   | Cases        | https://data.cdc.gov/Case-Surveillance/United-States-COVID-19-Cases-and-Deaths-by-State-o/9mfq-cb36
US states   | Deaths       | https://data.cdc.gov/Case-Surveillance/United-States-COVID-19-Cases-and-Deaths-by-State-o/9mfq-cb36
US states   | Tests        | https://beta.healthdata.gov/dataset/COVID-19-Diagnostic-Laboratory-Testing-PCR-Testing/j8mb-icvb
US states   | Hospitalized | https://beta.healthdata.gov/Hospital/COVID-19-Reported-Patient-Impact-and-Hospital-Capa/g62h-syeh
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
