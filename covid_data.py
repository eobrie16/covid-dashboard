import math
import pandas as pd
import us

COVID_CURRENT = r"https://covidtracking.com/api/v1/states/current.csv"
COVID_HISTORY = r"https://covidtracking.com/api/v1/states/daily.csv"


def get_covid():
    # global _COVID_DATA
    # if _COVID_DATA:
    #     return _COVID_DATA
    
    # read covid data
    cur_df = pd.read_csv(COVID_CURRENT)
    cur_df = cur_df.filter(['state', 'positive', 'negative', 'death', 'dateChecked'])
    cur_df.rename(columns={'positive': 'cases'}, inplace=True)
    cur_df['total'] = cur_df['cases'] + cur_df['negative']

    #percent columns
    cur_df['percent_cases'] = cur_df['cases'] / cur_df['total']
    cur_df['percent_death'] = cur_df['death'] / cur_df['total']
    cur_df['percent_tests'] = cur_df['total'] / cur_df['total']

    return cur_df

def get_pop():
    # process state population
    pop = pd.read_csv('data/SCPRC-EST2019-18+POP-RES.csv')
    # drop first and last rows
    pop.rename(columns={'POPESTIMATE2019': 'population'}, inplace=True)
    pop = pop[1:-1]
    pop['NAME'] = [us.states.lookup(name).abbr for name in pop['NAME']]
    pop = pop.filter(['NAME', 'population'])

    return pop

def get_data():
    # merge covid and population data
    cur_pop = get_covid().merge(right=get_pop(), left_on=['state'], right_on=['NAME'])
    cur_pop.drop(['NAME'], axis=1)

    #per capita columns
    cur_pop['pc_cases'] = cur_pop['cases'] / cur_pop['population']
    cur_pop['pc_death'] = cur_pop['death'] / cur_pop['population']
    cur_pop['pc_tests'] = cur_pop['total'] / cur_pop['population']

    return cur_pop






