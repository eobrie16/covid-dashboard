import math
from datetime import date
import itertools
import pandas as pd
import geopandas as gpd
import us

COVID_CURRENT = r"https://covidtracking.com/api/v1/states/current.csv"
COVID_HISTORY = r"https://covidtracking.com/api/v1/states/daily.csv"
US_MAP = "data/ne_50m_admin_1_states_provinces/ne_50m_admin_1_states_provinces.shp"

all_data = None
all_states = {}


def get_covid():
    
    cur_df = get_all_data()
    cur_df = cur_df[cur_df['date'] == cur_df['date'][0]]

    #percent columns
    cur_df['percent_cases'] = cur_df['total_cases'] / cur_df['total_tests']
    cur_df['percent_death'] = cur_df['total_death'] / cur_df['total_tests']

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

def get_map():
    gdf = gpd.read_file(US_MAP)[['iso_3166_2', 'name', 'geometry']]
    gdf.columns = ['abbr', 'name', 'geometry']
    gdf = gdf[gdf['abbr'].str.contains('US')]
    gdf['abbr'] = gdf['abbr'].apply(lambda x: x[3:])
    # remove AK/HI to scale map
    gdf = gdf[(gdf['abbr'] != 'AK') & (gdf['abbr'] != 'HI')]

    return gdf


def get_data():
    # merge covid and population data
    cur_pop = get_covid().merge(right=get_pop(), left_on=['state'], right_on=['NAME'])
    cur_pop.drop(['NAME'], axis=1)

    # merge map data
    cur_pop = get_map().merge(cur_pop, left_on='abbr', right_on='state')

    # percentage
    cur_pop['percent_tests'] = cur_pop['total_tests'] / cur_pop['population']

    #per capita columns
    cur_pop['pc_cases'] = cur_pop['total_cases'] / cur_pop['population']
    cur_pop['pc_death'] = cur_pop['total_death'] / cur_pop['population']
    cur_pop['pc_tests'] = cur_pop['total_tests'] / cur_pop['population']

    return cur_pop

def get_all_data():
    global all_data
    if all_data is None or pd.Timestamp(date.today()) - all_data['date'][0] < pd.Timedelta('24h'):
        all_data = pd.read_csv(COVID_HISTORY)
        all_data = all_data.filter(['date', 'state', 'positive', 'negative', 'death', 'total', 'deathIncrease', 'negativeIncrease', 'positiveIncrease'])
        all_data['date'] = pd.to_datetime(all_data['date'], format="%Y%m%d")
        all_data.rename(columns={'positive': 'total_cases'}, inplace=True)
        all_data.rename(columns={'death': 'total_death'}, inplace=True)
        all_data.rename(columns={'total': 'total_tests'}, inplace=True)
    return all_data

def get_state(state='MI', window=1):
    global all_states
    if state not in all_states or pd.Timestamp(date.today()) - all_states[state]['date'][0] < pd.Timedelta('24h'):
        # read covid data
        alls = get_all_data()
        df = alls[alls['state'] == state]
        count = len(df.index)
        df = df[:window * math.floor(count/window)]
        df['group'] = list(itertools.chain.from_iterable([x]*window for x in range(count//window)))
        state2 = df.groupby('group').first()
        state2[['deathIncrease', 'negativeIncrease', 'positiveIncrease']] = state2.groupby('group')[['deathIncrease', 'negativeIncrease', 'positiveIncrease']].mean()
        
        # per capita
        pop_df = get_pop()
        pop = pop_df[pop_df['NAME'] == state]['population']
        state2['pc_case_increase'] = 1e5 * state2['positiveIncrease'] / float(pop)
        state2['pc_death_increase'] = 1e5 * state2['deathIncrease'] / float(pop)
        # percent
        state2['percent_case_increase'] = 100 * state2['positiveIncrease'].pct_change(-1)
        state2['percent_death_increase'] = 100 * state2['deathIncrease'].pct_change(-1)
        # rename
        state2.rename(columns={'positiveIncrease': 'total_case_increase'}, inplace=True)
        state2.rename(columns={'deathIncrease': 'total_death_increase'}, inplace=True)
        all_states[state] = state2

    return all_states[state]






