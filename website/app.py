from flask import Flask, render_template
from common.models.base import Base, Session
from common.models.log_base import LogEntry
from common.models.pipelines_infos import PipelineInfos  # Assuming this is your model
import pandas as pd
from dash import Dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output

# Flask app
server = Flask(__name__)

# Optional: function to close database connection cleanly
@server.teardown_appcontext
def shutdown_session(exception=None):
    Session.remove()

@server.route('/')
def home():
    return render_template('index.html')

@server.route('/pipeline')
def pipeline():
    return render_template('pipeline.html')

# Dash app for Log Entries
app = Dash(__name__, server=server, routes_pathname_prefix='/dash/')

app.layout = html.Div([
    html.H1('Database Monitoring Dashboard'),
    dcc.Dropdown(
        id='table-dropdown',
        options=[
            {'label': 'Log Entries', 'value': 'log_entry'},
            {'label': 'Pipeline Info', 'value': 'pipeline_info'}
        ],
        value='log_entry'
    ),
    dash_table.DataTable(
        id='table',
        columns=[],
        data=[],
        sort_action='native'
    )
])

@app.callback(
    Output('table', 'columns'),
    Output('table', 'data'),
    Input('table-dropdown', 'value')
)
def update_table(selected_table):
    session = Session()
    if selected_table == 'log_entry':
        rows = session.query(LogEntry).all()
    elif selected_table == 'pipeline_info':
        rows = session.query(PipelineInfos).all()
    
    df = pd.DataFrame([r.to_dict() for r in rows])
    
    columns = [{'name': col, 'id': col} for col in df.columns]
    data = df.to_dict('records')
    
    return columns, data

# Dash app for Pipeline Info
pipeline_app = Dash(__name__, server=server, routes_pathname_prefix='/pipeline_dash/')

pipeline_app.layout = html.Div([
    html.H1('Pipeline Info Dashboard'),
    dash_table.DataTable(
        id='pipeline-table',
        columns=[],
        data=[],
        sort_action='native'
    )
])

@pipeline_app.callback(
    Output('pipeline-table', 'columns'),
    Output('pipeline-table', 'data'),
    Input('pipeline-table', 'id')
)
def update_pipeline_table(_):
    session = Session()
    rows = session.query(PipelineInfos).all()
    
    df = pd.DataFrame([r.to_dict() for r in rows])
    
    columns = [{'name': col, 'id': col} for col in df.columns]
    data = df.to_dict('records')
    
    return columns, data

if __name__ == "__main__":
    server.run(host='0.0.0.0', port=5000, debug=True)
