import datetime
import pickle

import pandas as pd
from dateutil.relativedelta import relativedelta
from prefect import flow, task
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

from prefect.deployments import DeploymentSpec
from prefect.flow_runners import SubprocessFlowRunner
from prefect.orion.schemas.schedules import CronSchedule

DATA_DIR = './01-into/data'
MODEL_DIR = './03-orchestration'

@task
def read_data(path):
    df = pd.read_parquet(path)
    return df

@task
def prepare_features(df, categorical, train=True):
    df['duration'] = df.dropOff_datetime - df.pickup_datetime
    df['duration'] = df.duration.dt.total_seconds() / 60
    df = df[(df.duration >= 1) & (df.duration <= 60)].copy()

    mean_duration = df.duration.mean()
    if train:
        print(f"The mean duration of training is {mean_duration}")
    else:
        print(f"The mean duration of validation is {mean_duration}")
    
    df[categorical] = df[categorical].fillna(-1).astype('int').astype('str')
    return df

@task
def train_model(df, categorical):

    train_dicts = df[categorical].to_dict(orient='records')
    dv = DictVectorizer()
    X_train = dv.fit_transform(train_dicts) 
    y_train = df.duration.values

    print(f"The shape of X_train is {X_train.shape}")
    print(f"The DictVectorizer has {len(dv.feature_names_)} features")

    lr = LinearRegression()
    lr.fit(X_train, y_train)
    y_pred = lr.predict(X_train)
    mse = mean_squared_error(y_train, y_pred, squared=False)
    print(f"The MSE of training is: {mse}")
    return lr, dv

@task
def run_model(df, categorical, dv, lr):
    val_dicts = df[categorical].to_dict(orient='records')
    X_val = dv.transform(val_dicts) 
    y_pred = lr.predict(X_val)
    y_val = df.duration.values

    mse = mean_squared_error(y_val, y_pred, squared=False)
    print(f"The MSE of validation is: {mse}")
    return

@task
def get_paths(date):
    
    train_date = date - relativedelta(months=2)
    val_date = date - relativedelta(months=1)
    train_path = f'{DATA_DIR}/fhv_tripdata_{train_date.year}-{str(train_date.month).zfill(2)}.parquet'
    val_path = f'{DATA_DIR}/fhv_tripdata_{val_date.year}-{str(val_date.month).zfill(2)}.parquet'
    
    return train_path, val_path

@task
def get_date(date):
    if not date:
        processed_date= datetime.date.today()
    else:
        processed_date = datetime.datetime.strptime(date, "%Y-%m-%d")
    
    return processed_date

@flow
def main(date):
    
    processed_date = get_date(date).result()
    
    train_path, val_path = get_paths(processed_date).result()

    categorical = ['PUlocationID', 'DOlocationID']

    df_train = read_data(train_path)
    df_train_processed = prepare_features(df_train, categorical)

    df_val = read_data(val_path)
    df_val_processed = prepare_features(df_val, categorical, False)

    # train the model
    lr, dv = train_model(df_train_processed, categorical).result()
    run_model(df_val_processed, categorical, dv, lr)
    
    with open(f'{MODEL_DIR}/models/dv-{processed_date}.b', 'wb') as f_out:
        pickle.dump(dv, f_out)

# main("2021-03-15")

DeploymentSpec(
    flow=main,
    name="model_training",
    schedule=CronSchedule(cron="0 9 15 * *"),
    flow_runner=SubprocessFlowRunner(),
)
