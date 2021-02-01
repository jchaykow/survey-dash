import dash_html_components as html
import dash_core_components as dcc


def get_menu():
    menu = html.Div([

        dcc.Link('Overview   ', href='/overview', className="tab first"),

        dcc.Link('Statistics   ', href='/statistics', className="tab"),

    ], className="row ")
    return menu
