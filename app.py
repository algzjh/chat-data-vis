import base64
import io

import chartgpt as cg
import dash
import dash_ag_grid as dag
import dash_mantine_components as dmc
import pandas as pd
from dash import Input, Output, State, dcc, html, no_update
from dash_iconify import DashIconify

import os
import openai

# from langchain.agents import create_pandas_dataframe_agent
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.organization_id = os.getenv("OPENAI_ORGANIZATION_ID")

app = dash.Dash(
    __name__,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;900&display=swap",
    ],
    title="ChartGPT",
    update_title="ChartGPT | Loading...",
    assets_folder="assets",
    include_assets_files=True,
)
# 服务器对象
server = app.server


body = dmc.Stack(
    [
        dmc.Stepper(
            id="stepper",
            contentPadding=30,
            active=0,
            size="md",
            breakpoint="sm",
            children=[
                dmc.StepperStep(
                    label="Upload your CSV file",
                    icon=DashIconify(icon="material-symbols:upload"),
                    progressIcon=DashIconify(icon="material-symbols:upload"),
                    completedIcon=DashIconify(icon="material-symbols:upload"),
                    children=[
                        dmc.Stack(
                            [
                                dcc.Upload(
                                    id="upload-data",
                                    children=html.Div(
                                        [
                                            "Drag and Drop or",
                                            dmc.Button(
                                                "Select CSV File",
                                                ml=10,
                                                leftIcon=DashIconify(
                                                    icon="material-symbols:upload"
                                                ),
                                            ),
                                        ]
                                    ),
                                    max_size=5 * 1024 * 1024,  # 5MB
                                    style={
                                        "borderWidth": "1px",
                                        "borderStyle": "dashed",
                                        "borderRadius": "5px",
                                        "textAlign": "center",
                                        "padding": "10px",
                                        "backgroundColor": "#fafafa",
                                    },
                                    style_reject={
                                        "borderColor": "red",
                                    },
                                    multiple=False,
                                ),
                                dmc.Title("Preview", order=3, color="primary"),
                                html.Div(id="output-data-upload"),
                            ]
                        )
                    ],
                ),
                dmc.StepperStep(
                    label="Plot your data 🚀",
                    icon=DashIconify(icon="bi:bar-chart"),
                    progressIcon=DashIconify(icon="bi:bar-chart"),
                    completedIcon=DashIconify(icon="bi:bar-chart-fill"),
                    children=[
                        dmc.Stack(
                            [
                                dmc.Textarea(
                                    id="input-text",
                                    placeholder="Write here",
                                    autosize=True,
                                    description="""Type in your questions or requests related to your CSV file. GPT will write the code to visualize the data and find the answers you're looking for.""",
                                    maxRows=2,
                                ),
                                dmc.Title("Preview", order=3, color="primary"),
                                html.Div(id="output-data-upload-preview"),
                            ]
                        )
                    ],
                ),
                dmc.StepperCompleted(
                    children=[
                        dmc.Stack(
                            [
                                dmc.Textarea(
                                    id="input-text-retry",
                                    description="""Type in your questions or requests related to your CSV file. GPT will write the code to visualize the data and find the answers you're looking for.""",
                                    placeholder="Write here",
                                    autosize=True,
                                    icon=DashIconify(icon="material-symbols:search"),
                                    maxRows=2,
                                ),
                                dmc.Title("Data preview", order=3, color="primary"),
                                html.Div(id="output-data-completed-preview"),
                                dmc.LoadingOverlay(
                                    id="output-card",
                                    mih=300,
                                    loaderProps={
                                        "variant": "bars",
                                        "color": "primary",
                                        "size": "xl",
                                    },
                                ),
                            ]
                        )
                    ]
                ),
            ],
        ),
        dmc.Group(
            [
                dmc.Button(
                    "Back",
                    id="stepper-back",
                    display="none",
                    size="md",
                    variant="outline",
                    radius="xl",
                    leftIcon=DashIconify(icon="ic:round-arrow-back"),
                ),
                dmc.Button(
                    "Next",
                    id="stepper-next",
                    size="md",
                    radius="xl",
                    rightIcon=DashIconify(
                        icon="ic:round-arrow-forward", id="icon-next"
                    ),
                ),
            ],
            position="center",
            mb=20,
        ),
    ]
)


header = dmc.Center(
    html.A(
        dmc.Image(
            src="https://raw.githubusercontent.com/chatgpt/chart/9ff8b9b96f01a5ee7091ee5e69a2795381bf5031/docs/assets/chartgpt_logo.svg",
            alt="ChartGPT Logo",
            width=300,
            m=20,
            caption="Plot your data using GPT",
        ),
        href="https://github.com/chatgpt/chart",
        style={"textDecoration": "none"},
    )
)


def show_graph_card(graph, code):
    return dmc.Card(
        dmc.Stack(
            [
                html.Div(graph),
                dmc.Accordion(
                    variant="separated",
                    chevronPosition="right",
                    radius="md",
                    children=[
                        dmc.AccordionItem(
                            [
                                dmc.AccordionControl(
                                    "Show code",
                                    icon=DashIconify(icon="solar:code-bold"),
                                ),
                                dmc.AccordionPanel(
                                    dmc.Prism(
                                        code,
                                        language="python",
                                        id="output-code",
                                        withLineNumbers=True,
                                    ),
                                ),
                            ],
                            value="customization",
                        )
                    ],
                ),
            ]
        )
    )


def show_text_card(text_result):
    return dmc.Card(dmc.Stack([html.Div(text_result)]))


page = [
    dcc.Store(id="dataset-store", storage_type="local"),
    dmc.Container(
        [
            dmc.Stack(
                [
                    header,
                    body,
                ]
            ),
        ]
    ),
]

# 设置布局和全局样式/主题，将page对象作为主体内容
app.layout = dmc.MantineProvider(
    id="mantine-provider",
    theme={
        "fontFamily": "'Inter', sans-serif",
        "colorScheme": "light",
        "primaryColor": "dark",
        "defaultRadius": "md",
        "white": "#fff",
        "black": "#404040",
    },
    withGlobalStyles=True,
    withNormalizeCSS=True,
    children=page,
    inherit=True,
)


def parse_contents(contents, filename):
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    try:
        if "csv" in filename:
            # Assuming the uploaded file is a CSV, parse it
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
            return df
        else:
            return "Invalid file format, please upload a CSV file."
    except Exception as e:
        print(e)
        return "An error occurred while processing the file."


@app.callback(
    Output("dataset-store", "data"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    prevent_initial_call=True,
)
def store_data(contents, filename):
    if contents is not None:
        df = parse_contents(contents, filename)
        return df.to_json(orient="split")


@app.callback(
    Output("output-data-upload", "children"),
    Output("output-data-upload-preview", "children"),
    Output("output-data-completed-preview", "children"),
    Output("upload-data", "style"),
    Output("upload-data", "children"),
    Input("dataset-store", "data"),
)
def load_data(dataset):
    if dataset is not None:
        df = pd.read_json(dataset, orient="split")
        table_preview = dag.AgGrid(
            id="data-preview",
            rowData=df.to_dict("records"),
            style={"height": "275px"},
            columnDefs=[{"field": i} for i in df.columns],
        )
        return (
            table_preview,
            table_preview,
            table_preview,
            {
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "padding": "7px",
                "backgroundColor": "#fafafa",
            },
            dmc.Group(
                [
                    html.Div(
                        [
                            "Drag and Drop or",
                            dmc.Button(
                                "Replace file",
                                ml=10,
                                leftIcon=DashIconify(icon="mdi:file-replace"),
                            ),
                        ]
                    )
                ],
                position="center",
                align="center",
                spacing="xs",
            ),
        )
    return no_update


@app.callback(
    Output("stepper", "active"),
    Input("stepper-next", "n_clicks"),
    Input("stepper-back", "n_clicks"),
    State("stepper", "active"),
    # 初始加载不触发此回调
    prevent_initial_call=True,
)
def update_stepper(stepper_next, stepper_back, current):
    ctx = dash.callback_context
    id_clicked = ctx.triggered[0]["prop_id"]
    if id_clicked == "stepper-next.n_clicks" and current < 2:
        return current + 1
    elif id_clicked == "stepper-back.n_clicks":
        return current - 1
    return no_update


@app.callback(
    Output("stepper-next", "disabled"),
    Output("stepper-back", "disabled"),
    Output("stepper-next", "display"),
    Output("stepper-back", "display"),
    Output("stepper-next", "children"),
    Output("icon-next", "icon"),
    Input("stepper", "active"),
    Input("dataset-store", "data"),
)
def update_stepper_buttons(current, data):
    if current == 0 and data is not None:
        return (
            False,
            False,
            "block",
            "block",
            "Next",
            "ic:round-arrow-forward",
        )
    elif current == 0 and data is None:
        return (
            True,
            False,
            "block",
            "block",
            "Next",
            "ic:round-arrow-forward",
        )
    elif current == 1:
        return (
            False,
            False,
            "block",
            "block",
            "Ask ChartGPT",
            "ph:flask-bold",
        )
    elif current == 2:
        return (False, False, "block", "block", "Ask again", "ic:refresh")
    return (dash.no_update,) * 6


@app.callback(
    Output("input-text-retry", "value"),
    Output("output-card", "children"),
    Input("stepper-next", "n_clicks"),
    State("stepper", "active"),
    State("dataset-store", "data"),
    State("input-text", "value"),
    State("input-text-retry", "value"),
    prevent_initial_call=True,
)
def update_graph(n_clicks, active, df, prompt, prompt_retry):
    if n_clicks is not None and active == 1:
        return prompt, predict(df, prompt)
    elif n_clicks is not None and active == 2:
        return prompt_retry, predict(df, prompt_retry)
    return no_update


def predict(df, prompt):
    df = pd.read_json(df, orient="split")

    # 检查是否是可视化问题，目前比较简单，用关键词判断
    visualization_keywords = ["visualize", "visualization", "chart"]
    if any(keyword in prompt.lower() for keyword in visualization_keywords):
        chart = cg.Chart(df)
        fig = chart.plot(prompt, return_fig=True)
        output = show_graph_card(graph=dcc.Graph(figure=fig), code=chart.last_run_code)
    else:
        # agent = create_pandas_dataframe_agent(OpenAI(temperature=0), df, verbose=False)
        # agent = create_pandas_dataframe_agent(
        #     ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0), df, verbose=False
        # )
        agent = create_pandas_dataframe_agent(
            ChatOpenAI(model_name="gpt-4", temperature=0), df, verbose=False
        )
        result_text = agent.run(prompt)
        output = show_text_card(result_text)
    return output


if __name__ == "__main__":
    app.run_server(debug=True)
