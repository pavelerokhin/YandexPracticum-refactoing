#!/usr/bin/env python3
"""
Weather forecast script that predicts temperature, humidity, and pressure
for a given geographical region using historical weather data.
"""

import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
import joblib
from pathlib import Path


def load_data(path_to_csv: str) -> pd.DataFrame:
    """
    Load and preprocess the weather history data.
    
    Args:
        path_to_csv: Path to the CSV file with weather history
        
    Returns:
        Preprocessed DataFrame with datetime index
    """
    df = pd.read_csv(path_to_csv)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    df.sort_index(inplace=True)
    
    # Check for missing values
    if df.isnull().any().any():
        raise ValueError("Input data contains missing values")
        
    return df


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create time-based and climate features from the input data.
    
    Args:
        df: Input DataFrame with weather data
        
    Returns:
        DataFrame with additional features
    """
    # Create a copy to avoid modifying the original
    features = df.copy()
    
    # Time-based features
    features['month'] = features.index.month
    features['day_of_year'] = features.index.dayofyear
    features['hour'] = features.index.hour
    
    # Seasonal features using sine/cosine
    features['sin_month'] = np.sin(2 * np.pi * features['month'] / 12)
    features['cos_month'] = np.cos(2 * np.pi * features['month'] / 12)
    features['sin_day'] = np.sin(2 * np.pi * features['day_of_year'] / 365)
    features['cos_day'] = np.cos(2 * np.pi * features['day_of_year'] / 365)
    
    # Rolling means for the last 24 hours
    for col in ['temperature', 'humidity', 'pressure']:
        features[f'{col}_rolling_mean_24h'] = features[col].rolling(window=24, min_periods=1).mean()
    
    # Drop the original timestamp-based columns as they're now in the index
    features = features.drop(['month', 'day_of_year', 'hour'], axis=1)
    
    return features


def train_model(path_to_csv: str) -> dict:
    """
    Train the weather forecasting model.
    
    Args:
        path_to_csv: Path to the CSV file with weather history
        
    Returns:
        Dictionary containing trained models for each target variable
    """
    # Load and preprocess data
    df = load_data(path_to_csv)
    features = make_features(df)
    
    # Prepare target variables
    targets = ['temperature', 'humidity', 'pressure']
    X = features.drop(targets, axis=1)
    
    models = {}
    for target in targets:
        y = features[target]
        
        # Train models for different quantiles
        models[target] = {
            'lower': GradientBoostingRegressor(
                loss='quantile',
                alpha=0.1,
                n_estimators=100,
                random_state=42
            ),
            'pred': GradientBoostingRegressor(
                loss='squared_error',
                n_estimators=100,
                random_state=42
            ),
            'upper': GradientBoostingRegressor(
                loss='quantile',
                alpha=0.9,
                n_estimators=100,
                random_state=42
            )
        }
        
        # Train each model
        for model_type, model in models[target].items():
            model.fit(X, y)
    
    return models


def predict_one_day(model: dict, latest_rows_df: pd.DataFrame, alpha: float = 0.9) -> pd.DataFrame:
    """
    Make predictions for the next 24 hours.
    
    Args:
        model: Dictionary of trained models
        latest_rows_df: DataFrame with the latest weather data
        alpha: Confidence level for prediction intervals
        
    Returns:
        DataFrame with predictions and confidence intervals
    """
    # Create features for prediction
    features = make_features(latest_rows_df)
    
    # Get the last row for prediction
    X_pred = features.iloc[[-1]]
    
    # Make predictions
    predictions = {}
    for target in ['temperature', 'humidity', 'pressure']:
        predictions[f'{target}_pred'] = model[target]['pred'].predict(X_pred)[0]
        predictions[f'{target}_low'] = model[target]['lower'].predict(X_pred)[0]
        predictions[f'{target}_high'] = model[target]['upper'].predict(X_pred)[0]
    
    # Create result DataFrame
    target_date = latest_rows_df.index[-1] + timedelta(days=1)
    result = pd.DataFrame({
        'target_date': [target_date],
        **predictions
    })
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Weather forecast script')
    parser.add_argument('--data', required=True, help='Path to weather history CSV file')
    parser.add_argument('--alpha', type=float, default=0.9, help='Confidence level for prediction intervals')
    args = parser.parse_args()
    
    # Train model
    model = train_model(args.data)
    
    # Load latest data for prediction
    latest_data = load_data(args.data)
    
    # Make prediction
    forecast = predict_one_day(model, latest_data, args.alpha)
    
    # Save forecast
    output_path = 'forecast.csv'
    forecast.to_csv(output_path, index=False)
    print(f"Forecast saved to: {output_path}")


if __name__ == "__main__":
    main() 