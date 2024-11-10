import dash
from dash import html, dcc, callback, Output, Input, State

# Initialize the Dash app
app = dash.Dash(__name__)

# Function to create the evolution counter component
def evolution_counter(app):
    html_container = html.Div([
        html.Div([
            html.Button("Less", id="down-button", n_clicks=0, style={
                "margin-right": "10px", 
                "width": "80px", 
                "height": "30px",
                "background-color": "black", 
                "color": "white", 
                "border-radius": "5px",  # Rounded corners
                "border": "none"  # Optional: removes border
            }),
            html.Button("More", id="up-button", n_clicks=0, style={
                "margin-right": "20px", 
                "width": "80px", 
                "height": "30px",
                "background-color": "black", 
                "color": "white", 
                "border-radius": "5px",  # Rounded corners
                "border": "none"  # Optional: removes border
            }),    
            html.Div(id="counter-display", children="Evolutions: 1", style={
                "font-size": "20px", 
                "font-weight": "normal"
            }),
        ], style={"display": "flex", "align-items": "center", "margin": "0px"}),
        
        # Hidden store to keep track of the value, initialized to 3
        dcc.Store(id="evolution-store", data=3)
    ], style={"margin-left": "20px"})

    # Callback to update the counter based on button clicks
    @app.callback(
        Output("evolution-store", "data"),
        Input("up-button", "n_clicks"),
        Input("down-button", "n_clicks"),
        State("evolution-store", "data")
    )
    def update_counter(up_clicks, down_clicks, current_value):
        # Ensure the value only goes between 1 and 5
        if dash.callback_context.triggered_id == "up-button":
            if current_value < 5:
                current_value += 1
        elif dash.callback_context.triggered_id == "down-button":
            if current_value > 1:
                current_value -= 1
        return current_value


    # Callback to update the display
    @app.callback(
        Output("counter-display", "children"),
        Input("evolution-store", "data")
    )
    def display_counter(value):
        return f"Evolutions: {value}"
    
    return html_container

# Layout of the app
app.layout = html.Div([
    evolution_counter(app)
])

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)