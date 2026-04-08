# Extreme Poverty Dashboard

A Streamlit dashboard that recreates the two poverty charts and adds a year-by-year playback view.

## What is included

- **Country trends**: line chart for selected countries
- **Regional totals**: stacked area chart by world region
- **Year playback**: bubble chart + top-country table that updates year by year
- **Play / Pause / Reset** controls in the sidebar

## Project structure

```text
poverty_dashboard_repo/
├── app.py
├── requirements.txt
└── data/
    ├── share-of-population-in-extreme-poverty.csv
    └── projections-extreme-poverty-wb.csv
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on GitHub + Streamlit Community Cloud

1. Create a new GitHub repository.
2. Upload all files in this folder.
3. Push the repository to GitHub.
4. In Streamlit Community Cloud, create a new app and connect the GitHub repository.
5. Set the main file path to `app.py`.
6. Deploy.

## Notes

- The playback feature is built with `streamlit-autorefresh`.
- The bubble chart uses **population** as both the x-axis base and the bubble size, with a log-scaled x-axis for readability.
- The regional stacked area chart includes a dotted vertical line at 2023 to separate the projection period.
