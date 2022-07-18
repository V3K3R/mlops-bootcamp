


import pickle
import sys
import pandas as pd

BASE_DIR = './04-deployment'

year = int(sys.argv[1]) #2021
month = int(sys.argv[2]) #2
input_file= f'{BASE_DIR}/../01-into/data/fhv_tripdata_{year:04d}-{month:02d}.parquet'
output_file= f'{BASE_DIR}/data/fhv_tripdata_{year:04d}-{month:02d}_pred.parquet'


with open(f'{BASE_DIR}/models/model.bin', 'rb') as f_in:
    dv, lr = pickle.load(f_in)


categorical = ['PUlocationID', 'DOlocationID']

def read_data(filename):
    df = pd.read_parquet(filename)
    
    df['duration'] = df.dropOff_datetime - df.pickup_datetime
    df['duration'] = df.duration.dt.total_seconds() / 60

    df = df[(df.duration >= 1) & (df.duration <= 60)].copy()

    df[categorical] = df[categorical].fillna(-1).astype('int').astype('str')
    
    return df

# broken url
# df = read_data('https://nyc-tlc.s3.amazonaws.com/trip+data/fhv_tripdata_????-??.parquet')
df = read_data(input_file)


df['ride_id'] = f'{year:04d}/{month:02d}_' + df.index.astype('str')


dicts = df[categorical].to_dict(orient='records')
X_val = dv.transform(dicts)
y_pred = lr.predict(X_val)


y_pred.mean()


df['ride_id'] = f'{year:04d}/{month:02d}_' + df.index.astype('str')


df_result = pd.DataFrame()
df_result['ride_id'] = df['ride_id']
df_result['predicted_result'] = y_pred


df_result.head()


df_result.to_parquet(
    output_file,
    engine='pyarrow',
    compression=None,
    index=False
)
