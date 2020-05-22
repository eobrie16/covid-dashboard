import math
import numpy as np
import pandas as pd

from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool, PrintfTickFormatter
from bokeh.plotting import figure
from bokeh.transform import factor_cmap

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
        # cases_chart, death_chart, tests_chart = redraw(1)
        cases_chart, death_chart = redraw('total')
    else:
        # cases_chart, death_chart, tests_chart = redraw(selected_class)
        cases_chart, death_chart = redraw(selected_class)

    script_cases_chart, div_cases_chart = components(cases_chart)
    script_death_chart, div_death_chart = components(death_chart)
    # script_tests_chart, div_tests_chart = components(tests_chart)

    return render_template(
        'index.html',
        div_cases_chart=div_cases_chart,
        script_cases_chart=script_cases_chart,
        div_death_chart=div_death_chart,
        script_death_chart=script_death_chart,
        # div_tests_chart=div_tests_chart,
        # script_tests_chart=script_tests_chart,
        selected_class=selected_class
    )

def bar_chart(dataset, type, depend, cpalette=palette, count=15):
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
        
    cutoff = dataset.sort_values(by=[type_str], ascending=False).iloc[count][type_str]
    the_data = dataset[dataset[type_str] > cutoff]
        
    values = list(factor*the_data[type_str].values)
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

# def tests_hist(dataset, pass_class, color=palette[1]):
#     hist, edges = np.histogram(dataset[dataset['Pclass'] == int(pass_class)]['Age'].fillna(df['Age'].mean()), bins=25)
    
#     source = ColumnDataSource({
#         'hist': hist,
#         'edges_left': edges[:-1],
#         'edges_right': edges[1:]
#     })

#     hover_tool = HoverTool(
#         tooltips=[('From', '@edges_left'), ('Thru', '@edges_right'), ('Count', '@hist')], 
#         mode='vline'
#     )
    
#     p = figure(plot_height=400, title='Age Histogram', tools=[hover_tool])
#     p.quad(top='hist', bottom=0, left='edges_left', right='edges_right', source=source,
#             fill_color=color, line_color='black')

#     plot_styler(p)
#     p.sizing_mode = 'scale_width'

#     return p

def redraw(p_class):
    dataset = get_data()
    cases_chart = bar_chart(dataset, p_class, 'cases')
    death_chart = bar_chart(dataset, p_class, 'death')
    # tests_chart = age_hist(df, p_class)
    return (
        cases_chart,
        death_chart,
        # tests_chart
    )


if __name__ == '__main__':
    app.run(debug=True)

