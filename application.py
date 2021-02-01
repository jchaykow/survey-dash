import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table
import plotly.graph_objs as go
from plotly.io import write_image
import flask

import matplotlib.pyplot as plt
import matplotlib

from components import header, print_button, make_dash_table

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import OrderedDict

import itertools

import base64

from pdb import set_trace

matplotlib.use('agg')

external_css = ["https://cdnjs.cloudflare.com/ajax/libs/normalize/7.0.0/normalize.min.css",
                "https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css",
                "//fonts.googleapis.com/css?family=Raleway:600,500,700",
                #"https://codepen.io/bcd/pen/KQrXdb.css",
                #"https://codepen.io/anon/pen/KbpJgz.css", 
                "https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css"]

app = dash.Dash(__name__, external_stylesheets=external_css)
server = app.server

app.scripts.config.serve_locally = True

app.config.suppress_callback_exceptions = True

school = pd.read_csv('data/survey_data.csv')
pq6_dummies = pd.get_dummies(school['q1']).rename(columns={1.0:'q1_1',2.0:'q1_2',3.0:'q1_3',4.0:'q1_4',5.0:'q1_5'})
school.columns = school.columns.str.lower()
school = pd.concat([school, pq6_dummies], axis=1)
school = school[~school.email.str.contains("@rand")].reset_index(drop=True)

users = pd.read_csv('data/users.csv').drop_duplicates(subset='email')
user_count = int(len(users))

data_date = 'February 2021'

questions = pd.read_csv('data/questions.csv')

answers = ['Strongly Disagree','Disagree','Neither Agree Nor Disagree','Agree','Strongly Agree']

school_likert_df = school.loc[:,list(questions.loc[(questions['QuestionType'] == 'likert') | (questions['QuestionType'] == 'likert2'), 'QuestionID'].values)].copy()
school_tf_df = school.loc[:,list(questions.loc[questions['QuestionType'] == 'Y/N', 'QuestionID'].values)].copy()

questions_likert = questions.loc[(questions['QuestionType'] == 'likert') | (questions['QuestionType'] == 'likert2')]
questions_likert_dict = dict(zip(questions_likert['QuestionID'], questions_likert['Question']))

questions_tf = questions.loc[questions['QuestionType'] == 'Y/N']
questions_tf_dict = dict(zip(questions_tf['QuestionID'], questions_tf['Question']))

questions_dict = dict(zip(questions['QuestionID'], questions['Question']))

school_likert = {'{column}'.format(column = col):school_likert_df['{column}'.format(column = col)].value_counts().reindex([1,2,3,4,5,6], fill_value=0) for col in list(school_likert_df.columns)}
school_tf = {'{column}'.format(column = col):school_tf_df['{column}'.format(column = col)].value_counts().reindex([0,1], fill_value=0) for col in list(school_tf_df.columns)}

values = [list(school_likert[key].values) for key, value in school_likert.items()]
y1 = [value[0] for value in values]
y2 = [value[1] for value in values]
y3 = [value[2] for value in values]
y4 = [value[3] for value in values]
y5 = [value[4] for value in values]
y6 = [value[5] for value in values]

values_tf = [list(school_tf[key].values) for key, value in school_tf.items()]
y1_tf = [value[0] for value in values]
y2_tf = [value[1] for value in values]

x = list(school_likert.keys())

x_tf = list(school_tf.keys())

def wrap_by_word(s, n):
    '''returns a string where \\n is inserted between every n words'''
    a = s.split()
    ret = ''
    for i in range(0, len(a), n):
        ret += ' '.join(a[i:i+n]) + '<br>'

    return ret

questions_with_breaks = [wrap_by_word(x, 7) for x in list(questions.Question.values)]


def get_menu():
    menu = html.Div([

        dcc.Link('Tab 1   ', href='/overview', className="tab first"),

        dcc.Link('Tab 2   ', href='/dash', className="tab"),

        dcc.Link('Tab 3   ', href='/statistics', className="tab"),

    ], className="row ")
    return menu

def get_logo():
    logo = html.Div([

        html.Div([
            html.Img(src=app.get_asset_url('banner_new4.png'), height='100', width='705')
            ], className="twelve columns"),

    ], className="row gs-header")
    return logo


def Header():
    return html.Div([
        get_logo(),
        #get_header(),
        html.Br([]),
        get_menu()
    ])


def get_header():
    header = html.Div([

        html.Div([
            html.H5(
                'Response Data')
        ], className="twelve columns padded")

    ], className="row gs-header gs-text-header")
    return header

one_week_ago = pd.to_datetime(data_date, format='%B %Y') - timedelta(days = 14)

units = ['A, B','C','Other']

df_classes = pd.DataFrame({
    'A': ['1','2','3','4','5','Other'],
    'C': [
        len(school.loc[(school.interview_end.notnull()) & (school.q1 == 1),:]),
        len(school.loc[(school.interview_end.notnull()) & (school.q1 == 2),:]),
        len(school.loc[(school.interview_end.notnull()) & (school.q1 == 3),:]),
        len(school.loc[(school.interview_end.notnull()) & (school.q1 == 4),:]),
        len(school.loc[(school.interview_end.notnull()) & (school.q1 == 5),:]),
        len(school.loc[(school.interview_end.notnull()) & (school.q1 == 6),:])
        ]
})

df_current_counts = pd.DataFrame({
    'Date':[
        'Lorem Ipsum',
        ' Duis aute irure', 
        # 'From Last Two Weeks'
        ],
    '{data_date}'.format(data_date=data_date):[
        len(school.loc[(school.interview_end.notnull())]), 
        user_count, 
        # len(users.loc[pd.to_datetime(users.PanelistCreatedDate, format='%m/%d/%y') >= one_week_ago,:])
        ]
    })

df_averages = pd.DataFrame({
    'Question':[
        'I like...',
        'I want...', 
        'It is going well...'],
    'Response':[
        'No responses' if school_likert_df['q1'].isnull().all() else answers[int(round(school_likert_df['q1'].mean())-1)], 
        'No responses' if school_likert_df['q3'].isnull().all() else answers[int(round(school_likert_df['q3'].mean())-1)],
        'No responses' if school_likert_df['q4'].isnull().all() else answers[int(round(school_likert_df['q4'].mean())-1)], 
        ],
    'AvgValue':[
        'No responses' if school_likert_df['q1'].isnull().all() else round(school_likert_df['q1'].mean(),3), 
        'No responses' if school_likert_df['q3'].isnull().all() else round(school_likert_df['q3'].mean(),3), 
        'No responses' if school_likert_df['q4'].isnull().all() else round(school_likert_df['q4'].mean(),3), 
        ]
    })

df_count_roles = pd.DataFrame({
    'Classes':[
        'Class 1',
        'Class 2',
        'Class 3',
        'Class 4',
        'Class 5',
        'Class 6',
        'Class 7'],
    'Count':[
        len(school.loc[(school.interview_end.notnull()) & (school.q1 == 1),:]), 
        len(school.loc[(school.interview_end.notnull()) & (school.q1 == 2),:]), 
        len(school.loc[(school.interview_end.notnull()) & (school.q1 == 3),:]),
        len(school.loc[(school.interview_end.notnull()) & (school.q1 == 4),:]),
        len(school.loc[(school.interview_end.notnull()) & (school.q1 == 5),:]),
        len(school.loc[(school.interview_end.notnull()) & (school.q1 == 6),:]),
        len(school.loc[(school.interview_end.notnull()) & (school.q1 == 7),:])]
    })

df_count_types = pd.DataFrame({
    'Types':[
        'Type', 
        'Type',
        'Type',
        'Type',
        'Type'],
    'Count':[
        len(school.loc[(school.interview_end.notnull()) & (school.q1 == 1),:]), 
        len(school.loc[(school.interview_end.notnull()) & (school.q1 == 2),:]), 
        len(school.loc[(school.interview_end.notnull()) & (school.q1 == 3),:]),
        len(school.loc[(school.interview_end.notnull()) & (school.q1 == 4),:]),
        len(school.loc[(school.interview_end.notnull()) & (school.q1 == 5),:])]
    })


## Page layouts
overview = html.Div([  # page 1
        html.Div([
            Header(),

            html.Div([

                html.Div([
                    html.H6(["Intro"], className="gs-header gs-table-header padded"),
                    dcc.Markdown('''
                    ###### Lorem ipsum dolor sit amet, consectetur adipiscing elit.

                    > ###### Ut enim ad minim veniam, quis nostrud exercitation ex ea commodo consequat.

                    > ###### Duis aute irure dolor in reprehenderit eu fugiat nulla pariatur.

                    > ###### Excepteur sint occaecat cupidatat non proident, sunt id est laborum.
                    ''')

                ], className="twelve columns"),

            ], className="row "),

            html.H6(["Summary"], className="gs-header gs-table-header"),
            html.Div([
                html.Div([
                    dash_table.DataTable(
                        id='table0',
                        data=df_current_counts.to_dict('rows'),
                        columns=[
                            {"name": i, "id": i} for i in df_current_counts.columns
                        ],
                        style_cell={
                            'textAlign': 'left',
                            'font-size':'130%',
                            'whiteSpace': 'normal',
                            'height': 'auto'},
                        style_data_conditional=[{
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }],
                        style_table={
                            'maxHeight':'180',
                            'overflowY':'scroll',
                            'border':'thin lightgrey solid'
                        }, 
                    )

                ], className="five columns"),

                html.Div([
                    dash_table.DataTable(
                        id='table_roles',
                        data=df_count_roles.to_dict('rows'),
                        columns=[
                            {"name": 'Types', "id": 'Roles'},
                            {"name": 'Count', "id": 'Count'}
                        ],
                        style_cell={'textAlign': 'left','font-size':'130%'},
                        style_data_conditional=[{
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }], 
                        style_table={
                            'maxHeight': '180',
                            'overflowY': 'scroll',
                            'border': 'thin lightgrey solid'
                        },
                    )
                ], className="four columns"),

                html.Div([
                    dash_table.DataTable(
                        id='table_systems',
                        data=df_count_types.to_dict('rows'),
                        columns=[
                            {"name": 'Classes', "id": 'Systems'},
                            {"name": 'Count', "id": 'Count'}
                        ],
                        style_cell={'textAlign': 'left','font-size':'130%'},
                        style_data_conditional=[{
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }], 
                        style_table={
                            'maxHeight': '180',
                            'overflowY': 'scroll',
                            'border': 'thin lightgrey solid'
                        },
                    )
                ], className="three columns"),

            ], className="row "),

            html.Div([
                html.H6(["Counts"], className="gs-header gs-table-header padded"),
                dash_table.DataTable(
                    id='table1',
                    data=[OrderedDict(row) for i, row in df_classes.iterrows()],
                    columns=[
                        {"name": 'Class', "id": 'A'},
                        {"name": 'Count', "id": 'C'},
                    ],
                    style_cell={'textAlign': 'left','font-size':'130%'},
                    style_data_conditional=[{
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }], 
                    style_table={
                        'maxHeight': '370',
                        'overflowY': 'scroll',
                        'border': 'thin lightgrey solid'
                    },
                )
            ], className="row "),

            # Row 2

        ], className="subpage")

    ], className="page")


statistics = html.Div([  # page 3

        html.Div([
            Header(),

            # Row 1

            html.Div([
                html.H6(["Select question"], className="gs-header gs-table-header padded"),
                dcc.Dropdown(
                    id = 'question-index-dropdown',
                    style={'margin-top': '5px'},
                    options=[
                        {'label':value, 'value':key} for key, value in questions_likert_dict.items()
                    ],
                    value='q1'
                ),

            ], className="twelve columns "), 

            html.Div([
                dash_table.DataTable(
                    id='table3',
                    data=[{'Response':''}],
                    columns=[
                        {"name": 'Average Response', "id": 'Response'}
                    ],
                    style_cell={'textAlign': 'left','font-size':'120%'},
                    style_table={
                        'maxHeight': '70',
                        'overflowY': 'scroll',
                        'border': 'thin lightgrey solid'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        },
                        {
                            'if': {
                                'column_id': 'Response',
                                'filter_query': '{Response} eq "Agree"'
                            },
                            'backgroundColor': '#3D9970',
                            'color': 'white',
                        },
                        {
                            'if': {
                                'column_id': 'Response',
                                'filter_query': '{Response} eq "Strongly Agree"'
                            },
                            'backgroundColor': '#3D9970',
                            'color': 'white',
                        },
                        {
                            'if': {
                                'column_id': 'Response',
                                'filter_query': '{Response} eq "Strongly Disagree"'
                            },
                            'backgroundColor': '#993d3d',
                            'color': 'white',
                        },
                        {
                            'if': {
                                'column_id': 'Response',
                                'filter_query': '{Response} eq "Disagree"'
                            },
                            'backgroundColor': '#993d3d',
                            'color': 'white',
                        },
                        {
                            'if': {
                                'column_id': 'Response',
                                'filter_query': '{Response} eq "Yes"'
                            },
                            'backgroundColor': '#3D9970',
                            'color': 'white',
                        },
                        {
                            'if': {
                                'column_id': 'Response',
                                'filter_query': '{Response} eq "No"'
                            },
                            'backgroundColor': '#993d3d',
                            'color': 'white',
                        },
                        {
                            'if': {
                                'column_id': 'Response',
                                'filter_query': '{Response} eq "Neither Agree Nor Disagree"'
                            },
                            'backgroundColor': '#bcbcbc',
                            'color': 'white',
                        },
                    ]
                )
            ], className="twelve columns"),
            
            html.Div([
                dcc.Dropdown(
                        id='error-drop',
                        options=[
                            {'label': 'Options', 'value': 'q4'},
                            {'label': 'Types', 'value': 'q1'}
                        ],
                        value='q4'
                    ), 
            ], className="twelve columns padded"), 

            html.Div([

                html.Div([
                    html.H6("Survey response distributions",
                            className="gs-header gs-table-header padded"),
                    dcc.Graph(
                        id='boxplot-stats',
                        config={
                            'displayModeBar': True,
                            'displaylogo': False,
                            'modeBarButtonsToRemove': ['sendDataToCloud','zoom2d','pan2d','select2d','lasso2d','zoomIn2d','zoomOut2d','autoScale2d','resetScale2d','hoverClosestCartesian','hoverCompareCartesian']
                        },
                        figure={
                            'data': [], 
                            'layout': dict(
                                yaxis=dict(
                                    autorange=False,
                                    showgrid=True,
                                    zeroline=True,
                                    dtick=5,
                                    gridcolor='rgb(230, 230, 230)',
                                    gridwidth=1,
                                    zerolinecolor='rgb(255, 255, 255)',
                                    zerolinewidth=2,
                                    range = [0,6],
                                    ticktext=answers,
                                    tickvals=[1,2,3,4,5],
                                    showticklabels=True
                                ),
                                width = 700,
                                height = 300,
                                hovermode='closest',
                                font = {
                                    "family": "Raleway",
                                    "size": 10
                                },
                                margin = {
                                    "r": 40,
                                    "t": 40,
                                    "b": 30,
                                    "l": 140
                                },
                                annotations=[], 

                                showlegend=False
                            )
                        },
                    )
                ], className="twelve columns")

            ], className="row "),

            html.Div([

                html.Div([
                    html.H6("Mean difference",
                            className="gs-header gs-table-header padded"),
                    dcc.Graph(
                        id='error-bars',
                        config={
                            'displayModeBar': True,
                            'displaylogo': False,
                            'modeBarButtonsToRemove': ['sendDataToCloud','zoom2d','pan2d','select2d','lasso2d','zoomIn2d','zoomOut2d','autoScale2d','resetScale2d','hoverClosestCartesian','hoverCompareCartesian']
                        },
                        figure={},
                    )
                ], className="twelve columns")

            ], className="row "),

        ], className="subpage")

    ], className="page")
    

overview2 = html.Div([  # page 2

        html.Div([
            Header(),
            html.Div(children=[], id='placeholder'),

            html.H6(["Text Analysis"], className="gs-header gs-table-header padded"),

            html.Div([

                html.Div([
                    dcc.Dropdown(
                        id = 'free-response-dropdown0',
                        style={'margin-top': '5px'},
                        options=[
                            {'label':'Describe...', 'value':'q1'},
                            {'label':'How...', 'value':'q2'},
                            {'label':'Which...', 'value':'q3'}
                        ],
                        value='q1'
                    ),

                ], className="six columns "), 

                html.Div([
                    dcc.Dropdown(
                        id = 'free-response-dropdown1',
                        style={'margin-top': '5px'},
                        options=[
                            {'label':'In general...', 'value':'q4'},
                            {'label':'What...', 'value':'q5'},
                        ],
                        value='q4'
                    ),

                ], className="six columns "), 
            
            ], className="row "),

            ############## Free Response ##############
            
            html.Div([
                html.Div([
                    dcc.Graph(
                        id='free-response',
                        config={
                            'displayModeBar': True,
                            'displaylogo': False,
                            'modeBarButtonsToRemove': ['sendDataToCloud','zoom2d','pan2d','select2d','lasso2d','zoomIn2d','zoomOut2d','autoScale2d','resetScale2d','hoverClosestCartesian','hoverCompareCartesian']
                        },
                        figure={
                            'data': [go.Bar(
                                    x=['Positive', 'Negative','Neither'],
                                    y=[14, 4, 1],
                                    marker_color=['#3D9970','#993d3d','#bcbcbc']
                                )], 
                            'layout': go.Layout(
                                dragmode = 'pan', 
                                autosize = False,
                                width = 350,
                                height = 160,
                                hovermode='closest',
                                font = {
                                    "family": "Raleway",
                                    "size": 10
                                },
                                margin = {
                                    "r": 20,
                                    "t": 40,
                                    "b": 30,
                                    "l": 20
                                },
                                showlegend = False,
                                titlefont = {
                                    "family": "Raleway",
                                    "size": 10
                                },
                            )
                        },
                    ),
                ], className="six columns "),

                html.Div([
                    dcc.Graph(
                        id='free-response1',
                        config={
                            'displayModeBar': True,
                            'displaylogo': False,
                            'modeBarButtonsToRemove': ['sendDataToCloud','zoom2d','pan2d','select2d','lasso2d','zoomIn2d','zoomOut2d','autoScale2d','resetScale2d','hoverClosestCartesian','hoverCompareCartesian']
                        },
                        figure={
                            'data': [], 
                            'layout': go.Layout(
                                dragmode = 'pan', 
                                autosize = False,
                                width = 350,
                                height = 160,
                                hovermode='closest',
                                font = {
                                    "family": "Raleway",
                                    "size": 10
                                },
                                margin = {
                                    "r": 20,
                                    "t": 40,
                                    "b": 30,
                                    "l": 20
                                },
                                showlegend = False,
                                titlefont = {
                                    "family": "Raleway",
                                    "size": 10
                                },
                            )
                        },
                    )
                ], className="six columns "),
            
            ], className="row "),

            html.Div([

                html.Div([
                    html.H6(["Averages"], className="gs-header gs-table-header padded"),
                    dash_table.DataTable(
                        id='table2',
                        css=[{
                            'selector': '.dash-cell div.dash-cell-value',
                            'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'
                        }],
                        data=df_averages.to_dict('rows'),
                        columns=[
                            {"name": 'Question', "id": 'Question'},
                            {"name": 'Average Response', "id": 'Response'},
                        ],
                        style_cell={
                            'textAlign': 'left',
                            'font-size':'120%',
                            'whiteSpace': 'normal',
                            'height': 'auto'},
                        style_table={
                            'maxHeight': '500',
                            'overflowY': 'scroll',
                            'overflowX': 'auto',
                            'border': 'thin lightgrey solid'
                        },
                        fixed_columns={'headers': True},
                        style_cell_conditional=[
                            {'if': {'column_id': 'Question'},
                            'width': '70%'},
                            {'if': {'column_id': 'Average Response'},
                            'width': '30%'}
                        ],
                        style_data_conditional=[
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': 'rgb(248, 248, 248)'
                            },
                            {
                                'if': {'column_id': 'Question'},
                                'width': '100px'
                            },
                            {
                                'if': {
                                    'column_id': 'Response',
                                    'filter_query': '{AvgValue} >= 1'
                                },
                                'backgroundColor': '#993d3d',
                                'color': 'white',
                            },
                            {
                                'if': {
                                    'column_id': 'Response',
                                    'filter_query': '{AvgValue} > 1.5'
                                },
                                'backgroundColor': '#bc4b4b',
                                'color': 'white',
                            },
                            {
                                'if': {
                                    'column_id': 'Response',
                                    'filter_query': '{AvgValue} > 2'
                                },
                                'backgroundColor': '#8FBC8F',
                                'color': 'white',
                            },
                            {
                                'if': {
                                    'column_id': 'Response',
                                    'filter_query': '{AvgValue} > 2.5'
                                },
                                'backgroundColor': '#bcbcbc',
                                'color': 'white',
                            },
                            {
                                'if': {
                                    'column_id': 'Response',
                                    'filter_query': '{AvgValue} > 3.5'
                                },
                                'backgroundColor': '#bcd6bc',
                                'color': 'white',
                            },
                            {
                                'if': {
                                    'column_id': 'Response',
                                    'filter_query': '{AvgValue} > 4'
                                },
                                'backgroundColor': '#8FBC8F',
                                'color': 'white',
                            },
                            {
                                'if': {
                                    'column_id': 'Response',
                                    'filter_query': '{Response} eq "Strongly Agree"'
                                },
                                'backgroundColor': '#266348',
                                'color': 'white',
                            },
                            {
                                'if': {
                                    'column_id': 'Response',
                                    'filter_query': '{Response} eq "Yes"'
                                },
                                'backgroundColor': '#993d3d',
                                'color': 'white',
                            },
                            {
                                'if': {
                                    'column_id': 'Response',
                                    'filter_query': '{Response} eq "No"'
                                },
                                'backgroundColor': '#266348',
                                'color': 'white',
                            }
                        ]
                    )
                ], className="twelve columns"),
            
            ], className="row "),

            html.H6(["Individual Questions"], className="gs-header gs-table-header padded"),
            html.Div([

                html.Div([
                    dcc.Dropdown(
                        id = 'question-index-dropdown0',
                        style={'margin-top': '5px'},
                        options=[
                            {'label':value, 'value':key} for key, value in questions_likert_dict.items()
                        ],
                        value='q1'
                    ),

                ], className="six columns "), 

                html.Div([
                    dcc.Dropdown(
                        id = 'question-index-dropdown1',
                        style={'margin-top': '5px'},
                        options=[
                            {'label':value, 'value':key} for key, value in questions_tf_dict.items()
                        ],
                        value='q2'
                    ),

                ], className="six columns "), 
            
            ], className="row "),

            html.Div([

                html.Div([
                    dcc.Graph(
                        id='likert-counts',
                        config={
                            'displayModeBar': True,
                            'displaylogo': False,
                            'modeBarButtonsToRemove': ['sendDataToCloud','zoom2d','pan2d','select2d','lasso2d','zoomIn2d','zoomOut2d','autoScale2d','resetScale2d','hoverClosestCartesian','hoverCompareCartesian']
                        },
                        figure={
                            'data': [], 
                            'layout': go.Layout(
                                dragmode = 'pan', 
                                autosize = False,
                                width = 350,
                                height = 225,
                                hovermode='closest',
                                font = {
                                    "family": "Raleway",
                                    "size": 10
                                },
                                margin = {
                                    "r": 40,
                                    "t": 40,
                                    "b": 30,
                                    "l": 40
                                },
                                showlegend = True,
                                titlefont = {
                                    "family": "Raleway",
                                    "size": 10
                                },
                            )
                        },
                    )
                ], className="six columns"),

                html.Div([
                    dcc.Graph(
                        id='tf-counts',
                        figure={
                            'data': [], 
                            'layout': go.Layout(
                                dragmode = 'pan', 
                                autosize = False,
                                width = 450,
                                height = 185,
                                font = {
                                    "family": "Raleway",
                                    "size": 10
                                    },
                                margin = {
                                    "r": 40,
                                    "t": 40,
                                    "b": 70,
                                    "l": 40
                                },
                                showlegend = True,
                                titlefont = {
                                    "family": "Raleway",
                                    "size": 10
                                },
                            )
                        },
                        config={
                            'displayModeBar': True,
                            'displaylogo': False,
                            'modeBarButtonsToRemove': ['sendDataToCloud','zoom2d','pan2d','select2d','lasso2d','zoomIn2d','zoomOut2d','autoScale2d','resetScale2d','hoverClosestCartesian','hoverCompareCartesian']
                        }
                    ),

                ], className="six columns "),

            ], className="row "),

            html.Div([
                html.Button('DOWNLOAD', 
                    id='all-button', 
                    style={'background-color': '#3d4399',
                            'color': '#f7f7f7'}),
            ], style={'float': 'center', 'display': 'block', 'margin-top': '1', 'margin-left': 'auto', 'margin-right': 'auto'}),

            html.Div([
                html.A(
                    'Download Data',
                    id='download-link',
                    download=f"figures_{datetime.today().strftime('%m%d%Y')}.pdf",
                    href="",
                    target="_blank"
                )
            ], id='download-link-div', style = {'display': 'None'}),

        ], className="subpage")

    ], className="page")


# Describe the layout, or the UI, of the app
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


noPage = html.Div([  # 404

    html.P(["Under Construction"])

    ], className="no-page")


@app.callback(
    Output('free-response', 'figure'),
    [Input('free-response-dropdown0', 'value')])
def update_boxplot(value):
    """"""
    if value != 'q1': return {}
    
    data = go.Bar(
        x=['Positive', 'Negative','Neither'],
        y=[14, 4, 1],
        marker_color=['#3D9970','#993d3d','#bcbcbc']
    )

    layout = go.Layout(
                dragmode = 'pan', 
                autosize = False,
                width = 350,
                height = 160,
                hovermode='closest',
                font = {
                    "family": "Raleway",
                    "size": 10
                },
                margin = {
                    "r": 20,
                    "t": 40,
                    "b": 30,
                    "l": 20
                },
                showlegend = False,
                titlefont = {
                    "family": "Raleway",
                    "size": 10
                },
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
    
    fig = go.Figure(data=data, layout=layout)

    return fig


@app.callback(
    Output('free-response1', 'figure'),
    [Input('free-response-dropdown1', 'value')])
def update_boxplot(value):
    """"""
    data = go.Bar(
        x=['Apple', 'Orange', 'Banana'],
        y=[2, 5, 13],
        marker_color=['#3D9970','#deb06f','#e3dd86']
    )

    layout = go.Layout(
                dragmode = 'pan', 
                autosize = False,
                width = 350,
                height = 160,
                hovermode='closest',
                font = {
                    "family": "Raleway",
                    "size": 10
                },
                margin = {
                    "r": 20,
                    "t": 40,
                    "b": 30,
                    "l": 20
                },
                showlegend = False,
                titlefont = {
                    "family": "Raleway",
                    "size": 10
                },
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
    
    fig = go.Figure(data=data, layout=layout)

    return fig


@app.callback(
    Output('download-link-div', 'style'),
    [Input('all-button', 'n_clicks')])
def download_shawn(n_clicks):
    if n_clicks is None or n_clicks % 2 == 0: return {'display': 'None'}
    return None


@app.callback(
    Output('download-link', 'href'),
    [Input('all-button', 'n_clicks')])
def download_figs(n_clicks):
    if n_clicks is None or n_clicks % 2 == 0: return None

    fmt = "pdf"
    mimetype = "application/pdf"
    filename = "figure.%s" % fmt

    data = base64.b64encode(open("assets/plots/" + filename, "rb").read()).decode("utf-8")
    pdf_string = f"data:{mimetype};base64,{data}"

    return pdf_string


@app.callback(dash.dependencies.Output('markdown', 'children'),
              [dash.dependencies.Input('question-index-dropdown', 'value')])
def display_markdown(value):
    return '''{q}'''.format(q = value)


@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/' or pathname == '/overview':
        return overview
    elif pathname == '/statistics':
        return statistics # noPage
    elif pathname == '/dash':
        return overview2


@app.callback(
    Output('error-bars', 'figure'),
    [Input('question-index-dropdown', 'value'),
    Input('error-drop', 'value')])
def update_boxplot(value, group):

    layout = go.Layout(
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(
            autorange=True,
            showgrid=True,
            zeroline=True,
            dtick=10,
            gridcolor='rgb(230, 230, 230)',
            gridwidth=1,
            zerolinecolor='rgb(230, 230, 230)',
            zerolinewidth=2,
        ),
        width = 700,
        height = 110,
        hovermode='closest',
        font = {
            "family": "Raleway",
            "size": 10
        },
        margin = {
            "r": 40,
            "t": 10,
            "b": 30,
            "l": 40
        },
        showlegend=False
    )

    if group == 'q4':

        results = pd.read_csv('data/Results-for-q4Mike.csv')
        combs = itertools.combinations(['Option1', 'Option2', 'Option3', 'Option4', 
                                'Option5', 'Option6', 'Option7'], r=2)
        pairs = []
        for pair in list(combs):
            pairs.append(pair[0]+'-'+pair[1])
        
        pairs = [role for role in pairs if 'Difference {role}'.format(role=role) in list(results.columns)]
        
        results.Variable = results.Variable.str.lower()
        if str(value) not in list(results.Variable.values):
            return go.Figure(data=[], layout=layout)

        results = results.loc[results.Variable == str(value),:]
        y_data = [float(results['Difference {role}'.format(role=role)]) for role in pairs]
        er = [float(results['Upper CI {role}'.format(role=role)]) - float(results['Lower CI {role}'.format(role=role)]) for role in pairs]
        pval = [float(results['p-value {role}'.format(role=role)]) for role in pairs]

        colors = ['#3D9970' if p < 0.05 else '#993d3d' for p in pval]
    
    if group == 'q1':

        results = pd.read_csv('data/Results-for-q1Mike.csv')
        pairs = [
            'Type2-Type1','Type3-Type1','Type4-Type1','Type1-Type5',
            'Type3-Type2','Type4-Type2','Type2-Type5','Type4-Type3','Type3-Type5','Type4-Type5'
        ]
        pairs = [proto for proto in pairs if 'Difference {proto}'.format(proto=proto) in list(results.columns)]
        
        results.Variable = results.Variable.str.lower()
        if str(value) not in list(results.Variable.values):
            return go.Figure(data=[], layout=layout)

        results = results.loc[results.Variable == str(value),:]
        y_data = [float(results['Difference {proto}'.format(proto=proto)]) for proto in pairs]
        er = [float(results['Upper CI {proto}'.format(proto=proto)]) - float(results['Lower CI {proto}'.format(proto=proto)]) for proto in pairs]
        pval = [float(results['p-value {proto}'.format(proto=proto)]) for proto in pairs]

        colors = ['#3D9970' if p < 0.05 else '#993d3d' for p in pval]

    data = [
        go.Scatter(
            x=pairs,
            y=y_data,
            error_y=dict(
                type='data',
                array=er,
                visible=True
            ),
            marker=dict(color=colors, size=10),
        )
    ]

    fig = go.Figure(data=data, layout=layout)

    return fig

@app.callback(
    Output('boxplot-stats', 'figure'),
    [Input('question-index-dropdown', 'value'),
    Input('error-drop', 'value')])
def update_boxplot(value, group):

    proto_df = school_likert_df.copy()
    proto_df = pd.concat([proto_df, school.loc[:, ['q1_1','q1_2','q1_3','q1_4','q1_5']]], axis=1)
    proto_df['q4'] = school['q4']

    if group == 'q4':
        x_data = ['Option 1','Option 2','Option 3','Option 4','Option 5','Option 6','Option 7']

        y0 = proto_df.loc[proto_df.q4 == 1,'{value}'.format(value=value)]; y0 = pd.Series([-3]) if y0.empty else y0
        y1 = proto_df.loc[proto_df.q4 == 2,'{value}'.format(value=value)]; y1 = pd.Series([-3]) if y1.empty else y1
        y2 = proto_df.loc[proto_df.q4 == 3,'{value}'.format(value=value)]; y2 = pd.Series([-3]) if y2.empty else y2
        y3 = proto_df.loc[proto_df.q4 == 4,'{value}'.format(value=value)]; y3 = pd.Series([-3]) if y3.empty else y3
        y4 = proto_df.loc[proto_df.q4 == 5,'{value}'.format(value=value)]; y4 = pd.Series([-3]) if y4.empty else y4
        y5 = proto_df.loc[proto_df.q4 == 6,'{value}'.format(value=value)]; y5 = pd.Series([-3]) if y5.empty else y5
        y6 = proto_df.loc[proto_df.q4 == 7,'{value}'.format(value=value)]; y6 = pd.Series([-3]) if y6.empty else y6
        y_data = [y0,y1,y2,y3,y4,y5,y6]
        # y_data = [pd.Series([np.nan if y == 6 else y for y in yd]) for yd in y_data]
    
    if group == 'q2':
        x_data = ['No','Yes']
        y0 = proto_df.loc[proto_df.pq5 == 0,'{value}'.format(value=value)]
        y1 = proto_df.loc[proto_df.pq5 == 1,'{value}'.format(value=value)]
        y_data = [y0,y1]
        y_data = [pd.Series([np.nan if y == 6 else y for y in yd]) for yd in y_data]

        z0 = proto_df.loc[(proto_df.pq5 == 0) & (proto_df.q4 == 1),'{value}'.format(value=value)]
        z1 = proto_df.loc[(proto_df.pq5 == 0) & (proto_df.q4 == 2),'{value}'.format(value=value)]
        z2 = proto_df.loc[(proto_df.pq5 == 1) & (proto_df.q4 == 1),'{value}'.format(value=value)]
        z3 = proto_df.loc[(proto_df.pq5 == 1) & (proto_df.q4 == 2),'{value}'.format(value=value)]
        z_data = [(len(z0.dropna()),len(z1.dropna())), (len(z2.dropna()),len(z3.dropna()))]

    if group == 'q1':

        x_data = ['Type 1', 'Type 2', 'Type 3', 'Type 4', 'Type 5']

        # set_trace()
        y0 = proto_df.loc[proto_df.q1 == 1,'{value}'.format(value=value)]
        y1 = proto_df.loc[proto_df.q1 == 2,'{value}'.format(value=value)]
        y2 = proto_df.loc[proto_df.q1 == 3,'{value}'.format(value=value)]
        y3 = proto_df.loc[proto_df.q1 == 4,'{value}'.format(value=value)]
        y4 = proto_df.loc[proto_df.q1 == 5,'{value}'.format(value=value)]
        y0 = pd.Series([-3]) if y0.empty else y0
        y1 = pd.Series([-3]) if y1.empty else y1
        y2 = pd.Series([-3]) if y2.empty else y2
        y3 = pd.Series([-3]) if y3.empty else y3
        y4 = pd.Series([-3]) if y4.empty else y4
        y_data = [y0,y1,y2,y3,y4]
        y_data = [pd.Series([5 if y == 6 else y for y in yd]) for yd in y_data]

    colors = ['rgba(93, 164, 214, 0.5)', 'rgba(255, 144, 14, 0.5)', 'rgba(44, 160, 101, 0.5)', 'rgba(255, 65, 54, 0.5)', 'rgba(221, 53, 255, 0.5)', 'rgba(93, 164, 214, 0.5)', 'rgba(255, 144, 14, 0.5)']
    traces = []
    for xd, yd, clr in zip(x_data, y_data, colors):
        traces.append(go.Box(
            y=yd,
            name=xd,
            boxpoints=False,
            jitter=0.5,
            whiskerwidth=0.2,
            fillcolor=clr,
            marker=dict(
                size=2,
            ),
            text=[len(yd)],
            line=dict(width=1),
        ))

    layout = dict(
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(
            autorange=False,
            showgrid=True,
            zeroline=True,
            dtick=5,
            gridcolor='rgb(230, 230, 230)',
            gridwidth=1,
            zerolinecolor='rgb(255, 255, 255)',
            zerolinewidth=2,
            range = [0,5.5],
            ticktext=answers,
            tickvals=[1,2,3,4,5],
            showticklabels=True
        ),
        width = 700,
        height = 300,
        hovermode='closest',
        font = {
            "family": "Raleway",
            "size": 10
        },
        margin = {
            "r": 40,
            "t": 40,
            "b": 30,
            "l": 140
        },
        annotations=[
            dict(
                x=i,
                y=5.5,
                xref='x',
                yref='y',
                text='n = {n}'.format(n=0 if len(yd.dropna()) == 1 else len(yd.dropna())),
                showarrow=False,
                font = dict(
                    color = "black",
                    size = 11,
                    family='Times New Roman',
                ),
            )
        for i, yd in enumerate(y_data)
        ], 

        showlegend=False
    )
    fig = go.Figure(data=traces, layout=layout)

    return fig


@app.callback(
    Output('likert-counts', 'figure'),
    [Input('question-index-dropdown0', 'value')])
def update_boxplot(value):

    school_likert_small = {'{column}'.format(column = value):school_likert_df['{column}'.format(column = value)].value_counts().reindex([1,2,3,4,5,6], fill_value=0)}

    values = [list(school_likert_small[key].values) for key, val in school_likert_small.items()]
    y1 = [val[0] for val in values]
    y2 = [val[1] for val in values]
    y3 = [val[2] for val in values]
    y4 = [val[3] for val in values]
    y5 = [val[4] for val in values]
    y6 = [val[5] for val in values]

    x = list(school_likert_small.keys())

    trace1 = go.Bar(
        x=x,
        y=y1,
        textposition = 'auto',
        marker=dict(
            color='#8B0000',
            line=dict(
                color='rgb(8,48,107)',
                width=1.5),
            ),
        opacity=0.6, 
        name = 'Strongly Disagree'
    )

    trace2 = go.Bar(
        x=x,
        y=y2,
        textposition = 'auto',
        marker=dict(
            color='#E9967A',
            line=dict(
                color='rgb(8,48,107)',
                width=1.5),
            ),
        opacity=0.6, 
        name = 'Disagree'
    )

    trace3 = go.Bar(
        x=x,
        y=y3,
        textposition = 'auto',
        marker=dict(
            color='#bcbcbc',
            line=dict(
                color='rgb(8,48,107)',
                width=1.5),
            ),
        opacity=0.6, 
        name = 'Neither Agree Nor Disagree'
    )

    trace4 = go.Bar(
        x=x,
        y=y4,
        textposition = 'auto',
        marker=dict(
            color='#8FBC8F',
            line=dict(
                color='rgb(8,48,107)',
                width=1.5),
            ),
        opacity=0.6, 
        name = 'Agree'
    )

    trace5 = go.Bar(
        x=x,
        y=y5,
        textposition = 'auto',
        marker=dict(
            color='#266348',
            line=dict(
                color='rgb(8,48,107)',
                width=1.5),
            ),
        opacity=0.6, 
        name = 'Strongly Agree'
    )

    trace6 = go.Bar(
        x=x,
        y=y6,
        textposition = 'auto',
        marker=dict(
            color='#6495ED',
            line=dict(
                color='rgb(8,48,107)',
                width=1.5),
            ),
        opacity=0.6, 
        name = 'N/A Not able to answer'
    )

    data = [trace1, trace2, trace3, trace4, trace5, trace6]

    data = data

    layout = go.Layout(
        dragmode = 'pan', 
        autosize = False,
        width = 390,
        height = 200,
        #hovermode='closest',
        font = {
            "family": "Raleway",
            "size": 10
        },
        margin = {
            "r": 20,
            "t": 10,
            "b": 10,
            "l": 15
        },
        showlegend = True,
        titlefont = {
            "family": "Raleway",
            "size": 10
        },
        xaxis = dict(
            range = [-0.5,0.5],
            showticklabels=False
        )
    )

    fig = go.Figure(data=data, layout=layout)

    return fig


@app.callback(
    Output('tf-counts', 'figure'),
    [Input('question-index-dropdown1', 'value')])
def update_boxplot(value):

    school_tf = {'{column}'.format(column = value):school_tf_df['{column}'.format(column = value)].value_counts().reindex([0,1], fill_value=0)}

    values_tf = [list(school_tf[key].values) for key, val in school_tf.items()]
    y1_tf = [val[0] for val in values_tf]
    y2_tf = [val[1] for val in values_tf]

    x_tf = list(school_tf.keys())

    trace1_tf = go.Bar(
        x=x,
        y=y1_tf,
        textposition = 'auto',
        marker=dict(
            color='#8B0000',
            line=dict(
                color='rgb(8,48,107)',
                width=0.5),
            ),
        opacity=0.8, 
        name = 'False'
    )

    trace2_tf = go.Bar(
        x=x,
        y=y2_tf,
        textposition = 'auto',
        marker=dict(
            color='#E9967A',
            line=dict(
                color='rgb(8,48,107)',
                width=0.5),
            ),
        opacity=0.8, 
        name = 'True'
    )

    data_tf = [trace1_tf, trace2_tf]

    data = data_tf

    layout = go.Layout(
        dragmode = 'pan', 
        autosize = False,
        width = 350,
        height = 200,
        font = {
            "family": "Raleway",
            "size": 10
            },
        margin = {
            "r": 40,
            "t": 10,
            "b": 10,
            "l": 40
        },
        showlegend = True,
        titlefont = {
            "family": "Raleway",
            "size": 10
        },
        xaxis = dict(
            range = [-0.5,0.5],
            showticklabels=False
        )
    )

    fig = go.Figure(data=data, layout=layout)

    return fig


@app.callback(
    Output('table3','data'),
    [Input('question-index-dropdown', 'value')])
def update_average_response(value):

    questions_likert_dict['{value}'.format(value=value)]

    df = pd.DataFrame({
        'Question':[
            questions_likert_dict['{value}'.format(value=value)]
            ],
        'Response':[
            'No responses' if school_likert_df['{value}'.format(value=value)].isnull().all() else answers[int(school_likert_df['{value}'.format(value=value)].mean())-1]
            ]
    })

    return df.to_dict('rows')

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)