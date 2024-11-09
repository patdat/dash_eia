import plotly.graph_objects as go
import numpy as np
import pandas as pd


def melt_pivot(df):
    df = pd.melt(
        df, id_vars=["id", "release_date"], var_name="period", value_name="value"
    )
    df = df.dropna(subset=["value"])
    df["release_date"] = pd.to_datetime(df["release_date"])
    df["period"] = pd.to_datetime(df["period"])
    df["value"] = pd.to_numeric(df["value"])
    df["value"] = df["value"].round(2)

    return df


def get_data(source, metasource):
    df = pd.read_feather(source)
    df_meta = pd.read_csv(metasource)
    df = df[df["id"].isin(df_meta["id"])]
    df["name"] = df["id"].map(df_meta.set_index("id")["name"])
    df["uom"] = df["id"].map(df_meta.set_index("id")["uom"])
    df.insert(1, "region", df["id"].map(df_meta.set_index("id")["region"]))

    meta_name = df[["id", "name"]].drop_duplicates().set_index("id").to_dict()["name"]
    meta_uom = df[["id", "uom"]].drop_duplicates().set_index("id").to_dict()["uom"]
    meta_region = (
        df[["id", "region"]].drop_duplicates().set_index("id").to_dict()["region"]
    )

    df = df.drop(columns=["name", "uom", "region"])

    df = melt_pivot(df)

    return df, meta_name, meta_region, meta_uom


def make_data_dicts(source, metasource, region_lookup=None):
    df, meta_name, meta_region, meta_uom = get_data(source, metasource)

    dct = {}
    for id in df["id"].unique():
        dff = df[df["id"] == id].drop(columns=["id"]).set_index("period")
        dff["release_date"] = dff["release_date"].dt.to_period("M")
        dff = dff.pivot(columns="release_date", values="value")
        dff = dff[dff.columns[::-1]]
        name = meta_name[id]
        region = meta_region[id]
        uom = meta_uom[id]

        if region_lookup is not None and region_lookup in region.lower():
            dct[id] = {"name": name, "region": region, "uom": uom, "data": dff}
    return dct


def chart_dpr(
    id,
    dct,
    btn_2020=True,
    btn_2021=False,
    btn_2022=False,
    btn_2023=False,
    btn_2024=False,
    btn_2025=False,
):
    df = dct[id]["data"]
    graph_region = dct[id]["region"]
    graph_name = dct[id]["name"]
    graph_uom = dct[id]["uom"]

    cols = df.columns.astype(str)

    if btn_2020:
        df = df[df.index >= "2020"]
    if btn_2021:
        df = df[df.index >= "2021"]
    if btn_2022:
        df = df[df.index >= "2022"]
    if btn_2023:
        df = df[df.index >= "2023"]
    if btn_2024:
        df = df[df.index >= "2024"]
    if btn_2025:
        df = df[df.index >= "2025"]

    period_as_array = df.index.to_numpy()

    traces = []

    # first trace
    traces.append(
        go.Scatter(
            x=period_as_array,
            y=df.iloc[:, 0],
            mode="lines",
            name=cols[0],
            line=dict(color="#c00000"),
            line_width=2,
        )
    )

    # second trace
    traces.append(
        go.Scatter(
            x=period_as_array,
            y=df.iloc[:, 1],
            mode="lines",
            name=cols[1],
            line=dict(color="#e97132"),
        )
    )

    # third trace
    traces.append(
        go.Scatter(
            x=period_as_array,
            y=df.iloc[:, 2],
            mode="lines",
            name=cols[2],
            line=dict(color="#bfbec4"),
        )
    )

    # fourth trace
    traces.append(
        go.Scatter(
            x=period_as_array,
            y=df.iloc[:, 3],
            mode="lines",
            name=cols[3],
            line=dict(color="#0073c0"),
        )
    )

    # fifth trace
    traces.append(
        go.Scatter(
            x=period_as_array,
            y=df.iloc[:, 4],
            mode="lines",
            name=cols[4],
            line=dict(color="#4CAF50"),
        )
    )

    layout = go.Layout(
        title=f"{graph_region}: {graph_name} ({graph_uom})",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", x=0, y=1.1),
        xaxis=dict(
            showline=True,
            showgrid=False,
            linecolor="black",
            linewidth=0.5,
            zeroline=False,
        ),
        yaxis=dict(
            tickformat=",.0fK",
            showgrid=False,
            showline=True,
            linecolor="black",
            linewidth=0.5,
            zeroline=False,
        ),
    )

    return go.Figure(data=traces, layout=layout)


### PARAMETERS ##########################################################


def get_regional_dict_data(region_lookup):
    source = "./data/steo/steo_pivot_dpr.feather"
    meta = "./lookup/steo/mapping_dpr.csv"
    dct_to_search = make_data_dicts(source, meta, region_lookup)
    return dct_to_search
