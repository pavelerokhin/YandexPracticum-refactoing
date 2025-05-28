# Weather Forecast

A Python script for predicting temperature, humidity, and pressure for a given geographical region using historical weather data.

## Features

- Predicts temperature (°C), relative humidity (%), and atmospheric pressure (hPa)
- Uses Gradient Boosting with quantile regression for confidence intervals
- Includes time-based and climate features
- Generates 24-hour ahead forecasts

## Requirements

- Python 3.7+
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the script with your weather history data:

```bash
python forecast.py --data weather_history.csv
```

Optional arguments:
- `--alpha`: Confidence level for prediction intervals (default: 0.9)

## Input Data Format

The input CSV file should contain the following columns:
- `timestamp` (UTC, ISO 8601)
- `lat` (latitude)
- `lon` (longitude)
- `elevation_m` (elevation in meters)
- `temperature` (in °C)
- `humidity` (in %)
- `pressure` (in hPa)

## Output

The script generates a `forecast.csv` file with the following columns:
- `target_date`: Date of the forecast
- `temperature_pred`, `temperature_low`, `temperature_high`
- `humidity_pred`, `humidity_low`, `humidity_high`
- `pressure_pred`, `pressure_low`, `pressure_high`

## Example

```bash
python forecast.py --data weather_history.csv --alpha 0.9
```

This will generate a forecast for the next 24 hours with 90% confidence intervals. 