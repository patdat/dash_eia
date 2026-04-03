import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from scripts.generate_report import (
    TABLE_DEFS,
    CHART_SERIES,
    load_data,
    build_table_data,
    compute_seasonality,
)


class TestTableDefs:
    def test_table_defs_has_16_tables(self):
        assert len(TABLE_DEFS) == 16

    def test_headline_series_ids(self):
        assert "WCESTUS1" in TABLE_DEFS["Headline"]
        assert "W_EPC0_SAX_YCUOK_MBBL" in TABLE_DEFS["Headline"]
        assert "WGTSTUS1" in TABLE_DEFS["Headline"]
        assert "WDISTUS1" in TABLE_DEFS["Headline"]

    def test_chart_series_has_4_ids(self):
        assert len(CHART_SERIES) == 4
        assert "WCESTUS1" in CHART_SERIES
        assert "W_EPC0_SAX_YCUOK_MBBL" in CHART_SERIES


class TestBuildTableData:
    @pytest.fixture
    def sample_df(self):
        rows = []
        dates = pd.to_datetime(["2026-03-14", "2026-03-21", "2026-03-28"])
        for d in dates:
            rows.append({"date": d, "series_id": "WCESTUS1", "value": 430.0 + (d.day - 14)})
            rows.append({"date": d, "series_id": "WGTSTUS1", "value": 230.0 + (d.day - 14)})
        return pd.DataFrame(rows)

    def test_returns_dict_keyed_by_table_name(self, sample_df):
        result = build_table_data(sample_df)
        assert isinstance(result, dict)
        assert "Headline" in result

    def test_table_has_correct_columns(self, sample_df):
        result = build_table_data(sample_df)
        headline = result["Headline"]
        assert "name" in headline.columns
        assert "change" in headline.columns
        assert len(headline.columns) == 4

    def test_change_is_week_over_week(self, sample_df):
        result = build_table_data(sample_df)
        headline = result["Headline"]
        row = headline[headline["name"] == "US Commercial Stocks (kb)"]
        assert len(row) == 1
        change = row["change"].iloc[0]
        assert change == pytest.approx(7.0)

    def test_missing_series_excluded(self, sample_df):
        result = build_table_data(sample_df)
        if "CDU Utilization" in result:
            assert result["CDU Utilization"]["change"].isna().all()

    def test_week_ending_date(self, sample_df):
        result = build_table_data(sample_df)
        headline = result["Headline"]
        date_cols = [c for c in headline.columns if c not in ("name", "change")]
        assert len(date_cols) == 2
        assert date_cols[1] == "03/28"
        assert date_cols[0] == "03/21"


class TestComputeSeasonality:
    @pytest.fixture
    def seasonality_df(self):
        rows = []
        for year in range(2015, 2027):
            base = 400 + (year - 2015) * 5
            for week in range(52):
                date = pd.Timestamp(f"{year}-01-01") + pd.Timedelta(weeks=week)
                value = base + 20 * np.sin(2 * np.pi * week / 52)
                rows.append({
                    "date": date,
                    "series_id": "WCESTUS1",
                    "value": value,
                })
        return pd.DataFrame(rows)

    def test_returns_dict_with_required_keys(self, seasonality_df):
        result = compute_seasonality(seasonality_df, "WCESTUS1")
        assert "week_of_year" in result
        assert "min" in result
        assert "max" in result
        assert "mean" in result
        assert "years" in result

    def test_range_band_computed_from_historical_years(self, seasonality_df):
        result = compute_seasonality(seasonality_df, "WCESTUS1")
        for i in range(len(result["min"])):
            assert result["min"][i] <= result["max"][i]

    def test_year_lines_has_display_years(self, seasonality_df):
        result = compute_seasonality(seasonality_df, "WCESTUS1")
        year_keys = list(result["years"].keys())
        assert 2026 in year_keys
        assert 2025 in year_keys
        assert 2024 in year_keys

    def test_week_of_year_is_sequential(self, seasonality_df):
        result = compute_seasonality(seasonality_df, "WCESTUS1")
        weeks = result["week_of_year"]
        assert weeks[0] == 0
        assert weeks[-1] <= 52
        assert all(weeks[i] <= weeks[i + 1] for i in range(len(weeks) - 1))
