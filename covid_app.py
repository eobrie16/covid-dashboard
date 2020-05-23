import math
import numpy as np
import pandas as pd
import json

from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool, PrintfTickFormatter
from bokeh.models import GeoJSONDataSource, LinearColorMapper, LogColorMapper, ColorBar
from bokeh.plotting import figure
from bokeh.transform import factor_cmap
from bokeh.palettes import brewer

from flask import Flask, render_template, request

from covid_data import get_data


palette = ['#ba32a0', '#f85479', '#f8c260', '#00c2ba']

chart_font = 'Helvetica'
chart_title_font_size = '16pt'
chart_title_alignment = 'center'
axis_label_size = '14pt'
axis_ticks_size = '12pt'
default_padding = 30
chart_inner_left_padding = 0.015
chart_font_style_title = 'bold italic'


def palette_generator(length, palette):
    int_div = length // len(palette)
    remainder = length % len(palette)
    return (palette * int_div) + palette[:remainder]


def plot_styler(p):
    p.title.text_font_size = chart_title_font_size
    p.title.text_font  = chart_font
    p.title.align = chart_title_alignment
    p.title.text_font_style = chart_font_style_title
    p.y_range.start = 0
    p.x_range.range_padding = chart_inner_left_padding
    p.xaxis.axis_label_text_font = chart_font
    p.xaxis.major_label_text_font = chart_font
    p.xaxis.axis_label_standoff = default_padding
    p.xaxis.axis_label_text_font_size = axis_label_size
    p.xaxis.major_label_text_font_size = axis_ticks_size
    p.yaxis.axis_label_text_font = chart_font
    p.yaxis.major_label_text_font = chart_font
    p.yaxis.axis_label_text_font_size = axis_label_size
    p.yaxis.major_label_text_font_size = axis_ticks_size
    p.yaxis.axis_label_standoff = default_padding
    p.toolbar.logo = None
    p.toolbar_location = None

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def chart():
    selected_class = request.form.get('dropdown-select')

    if selected_class == 0 or selected_class == None:
        cases_chart, death_chart, us_map = redraw('total')
    else:
        cases_chart, death_chart, us_map = redraw(selected_class)

    script_cases_chart, div_cases_chart = components(cases_chart)
    script_death_chart, div_death_chart = components(death_chart)
    script_us_map, div_us_map = components(us_map)

    return render_template(
        'index.html',
        div_cases_chart=div_cases_chart,
        script_cases_chart=script_cases_chart,
        div_death_chart=div_death_chart,
        script_death_chart=script_death_chart,
        div_us_map=div_us_map,
        script_us_map=script_us_map,
        selected_class=selected_class
    )

def process_data(dataset, type, depend, count=None):
    factor = 1
    if type == 'capita':
        type_str = f'pc_{depend}'
        title = f"{depend.capitalize()} Per 100,000 residents"
        factor = 1e5
    elif type == 'percent':
        type_str = f'percent_{depend}'
        title = f"Percentage of {depend.capitalize()}"
        factor = 100
    elif type == 'total':
        type_str = depend
        title = f"Total {depend.capitalize()}"
    else:
        type_str = depend
        title = depend.title()
        
    if count:
        cutoff = dataset.sort_values(by=[type_str], ascending=False).iloc[count][type_str]
        the_data = dataset[dataset[type_str] > cutoff]
    else:
        the_data = dataset
    the_data['values'] = factor*the_data[type_str]

    return the_data, title

def bar_chart(dataset, type, depend, cpalette=palette, count=15):
    the_data, title = process_data(dataset, type, depend, count)
        
    values = list(the_data['values'])
    states = list(the_data['state'])
        
    source = ColumnDataSource(data={
        'states': states,
        'values': values
    })

    hover_tool = HoverTool(
        tooltips=[('State?', '@states'), ('Count', '@values')]
    )
    
    p = figure(x_range=states, tools=[hover_tool], plot_height=400, title=title)
    
    p.vbar(x='states', top='values', source=source, width=0.9,
           fill_color=factor_cmap('states', palette=palette_generator(len(source.data['states']), cpalette), factors=source.data['states']))
    
    
    plot_styler(p)
    # p.xaxis.ticker = source.data['states']
    # p.xaxis.major_label_overrides = dataset['states'].values
    p.sizing_mode = 'scale_width'
    
    return p

def create_map(dataset, type, depend, cpalette=palette):
    the_data, title = process_data(dataset, type, depend)

    #Read data to json.
    merged_json = json.loads(the_data.to_json())
    json_data = json.dumps(merged_json)
    geosource = GeoJSONDataSource(geojson = json_data)
    #Define a sequential multi-hue color palette.
    palette = brewer['YlGnBu'][8]
    palette = palette[::-1]
    #Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
    max_cases = max(the_data['values'])
    min_cases = min(the_data['values'])
    color_mapper = LinearColorMapper(palette = palette, low = min_cases, high = max_cases)
    #Create color bar. 
    # color_bar = ColorBar(color_mapper=color_mapper, width = 500, height = 20,
    # border_line_color=None,location = (0,0), orientation = 'horizontal')

    tools = "pan,wheel_zoom,reset,hover"

    p = figure(title = title, tools=tools, plot_height = 600 , plot_width = 950,
               toolbar_location = None, x_axis_location=None, y_axis_location=None,
               tooltips=[("State", "@state"), ("Count", "@values")])
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None  
    p.hover.point_policy = "follow_mouse"
    p.patches('xs','ys', source = geosource, fill_color = {'field' : 'values', 'transform' : color_mapper},
          line_color = 'black', line_width = 0.25, fill_alpha = 1)
    #Specify figure layout.
    # p.add_layout(color_bar, 'below')
    
    return p

def redraw(p_class):
    dataset = get_data()
    cases_chart = bar_chart(dataset, p_class, 'cases')
    death_chart = bar_chart(dataset, p_class, 'death')
    us_map = create_map(dataset, p_class, 'cases')
    return (
        cases_chart,
        death_chart,
        us_map
    )


if __name__ == '__main__':
    app.run(debug=True)

