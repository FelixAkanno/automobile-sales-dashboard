import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px


# ============================================================
# Load data
# ============================================================

df = pd.read_csv("automobile-sales.csv")


# ============================================================
# Create Dash app
# ============================================================

app = dash.Dash(__name__)


# ============================================================
# App layout
# ============================================================

app.layout = html.Div([

    html.H1(
        "Automobile Sales Statistics Dashboard",
        style={
            "textAlign": "center",
            "color": "#503D36",
            "fontSize": 24
        }
    ),

    # Report type dropdown
    html.Div([
        html.Label("Select Statistics:"),

        dcc.Dropdown(
            id="dropdown-statistics",
            options=[
                {
                    "label": "Yearly Statistics",
                    "value": "Yearly Statistics"
                },
                {
                    "label": "Recession Period Statistics",
                    "value": "Recession Period Statistics"
                }
            ],
            value="Yearly Statistics",
            placeholder="Select a report type"
        )
    ]),

    html.Br(),

    # Year dropdown
    html.Div([
        html.Label("Select Year:"),

        dcc.Dropdown(
            id="select-year",
            options=[
                {"label": year, "value": year}
                for year in sorted(df["Year"].unique())
            ],
            value=df["Year"].min()
        )
    ]),

    html.Br(),

    # Graph output area
    html.Div(
        id="output-container",
        className="chart-grid"
    )
])


# ============================================================
# Callback 1:
# Enable/disable year dropdown
# ============================================================

@app.callback(
    Output("select-year", "disabled"),
    Input("dropdown-statistics", "value")
)
def update_input_container(selected_statistics):

    if selected_statistics == "Yearly Statistics":
        return False

    return True


# ============================================================
# Callback 2:
# Generate dashboard charts
# ============================================================

@app.callback(
    Output("output-container", "children"),
    [
        Input("dropdown-statistics", "value"),
        Input("select-year", "value")
    ]
)
def update_output_container(selected_statistics, input_year):

    # ========================================================
    # YEARLY STATISTICS
    # ========================================================

    if selected_statistics == "Yearly Statistics":

        yearly_data = df[df["Year"] == input_year]

        # ----------------------------------------------------
        # Plot 1:
        # Average automobile sales by year
        # ----------------------------------------------------

        yearly_sales = (
            df.groupby("Year")["Automobile_Sales"]
            .mean()
            .reset_index()
        )

        fig1 = px.line(
            yearly_sales,
            x="Year",
            y="Automobile_Sales",
            title="Yearly Automobile Sales"
        )

        # ----------------------------------------------------
        # Plot 2:
        # Total monthly sales for selected year
        # ----------------------------------------------------

        monthly_sales = (
            yearly_data.groupby("Month")["Automobile_Sales"]
            .sum()
            .reset_index()
        )

        fig2 = px.line(
            monthly_sales,
            x="Month",
            y="Automobile_Sales",
            title=f"Total Monthly Automobile Sales in {input_year}"
        )

        # ----------------------------------------------------
        # Plot 3:
        # Average vehicles sold by vehicle type
        # ----------------------------------------------------

        vehicle_sales = (
            yearly_data.groupby("Vehicle_Type")["Automobile_Sales"]
            .mean()
            .reset_index()
        )

        fig3 = px.bar(
            vehicle_sales,
            x="Vehicle_Type",
            y="Automobile_Sales",
            title=f"Average Vehicles Sold by Vehicle Type in {input_year}"
        )

        # ----------------------------------------------------
        # Plot 4:
        # Advertisement expenditure by vehicle type
        # ----------------------------------------------------

        ad_expenditure = (
            yearly_data.groupby("Vehicle_Type")["Advertising_Expenditure"]
            .sum()
            .reset_index()
        )

        fig4 = px.pie(
            ad_expenditure,
            values="Advertising_Expenditure",
            names="Vehicle_Type",
            title=f"Total Advertisement Expenditure by Vehicle Type in {input_year}"
        )

        return [
            html.Div([
                dcc.Graph(figure=fig1),
                dcc.Graph(figure=fig2)
            ], style={
                "display": "flex",
                "width": "100%"
            }),

            html.Div([
                dcc.Graph(figure=fig3),
                dcc.Graph(figure=fig4)
            ], style={
                "display": "flex",
                "width": "100%"
            })
        ]


    # ========================================================
    # RECESSION PERIOD STATISTICS
    # ========================================================

    elif selected_statistics == "Recession Period Statistics":

        recession_data = df[df["Recession"] == 1]

        # ----------------------------------------------------
        # Plot 1:
        # Average automobile sales during recession by year
        # ----------------------------------------------------

        recession_yearly_sales = (
            recession_data.groupby("Year")["Automobile_Sales"]
            .mean()
            .reset_index()
        )

        fig1 = px.line(
            recession_yearly_sales,
            x="Year",
            y="Automobile_Sales",
            title="Average Automobile Sales During Recession Periods"
        )

        # ----------------------------------------------------
        # Plot 2:
        # Average vehicles sold by vehicle type
        # ----------------------------------------------------

        recession_vehicle_sales = (
            recession_data.groupby("Vehicle_Type")["Automobile_Sales"]
            .mean()
            .reset_index()
        )

        fig2 = px.bar(
            recession_vehicle_sales,
            x="Vehicle_Type",
            y="Automobile_Sales",
            title="Average Vehicles Sold by Vehicle Type During Recessions"
        )

        # ----------------------------------------------------
        # Plot 3:
        # Advertising expenditure share
        # ----------------------------------------------------

        recession_ad = (
            recession_data.groupby("Vehicle_Type")["Advertising_Expenditure"]
            .sum()
            .reset_index()
        )

        fig3 = px.pie(
            recession_ad,
            values="Advertising_Expenditure",
            names="Vehicle_Type",
            title="Total Expenditure Share by Vehicle Type During Recessions"
        )

        # ----------------------------------------------------
        # Plot 4:
        # Unemployment rate effect on sales
        # ----------------------------------------------------

        unemployment_data = (
            recession_data
            .groupby(["unemployment_rate", "Vehicle_Type"])["Automobile_Sales"]
            .mean()
            .reset_index()
        )

        fig4 = px.bar(
            unemployment_data,
            x="unemployment_rate",
            y="Automobile_Sales",
            color="Vehicle_Type",
            title="Effect of Unemployment Rate on Vehicle Type and Sales"
        )

        return [
            html.Div([
                dcc.Graph(figure=fig1),
                dcc.Graph(figure=fig2)
            ], style={
                "display": "flex",
                "width": "100%"
            }),

            html.Div([
                dcc.Graph(figure=fig3),
                dcc.Graph(figure=fig4)
            ], style={
                "display": "flex",
                "width": "100%"
            })
        ]


# ============================================================
# Run application
# ============================================================

if __name__ == "__main__":
    if __name__ == "__main__":
        app.run(debug=True, port=8051)