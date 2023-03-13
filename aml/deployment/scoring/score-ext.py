import json
import random
import pickle
import numpy
import os
import joblib
import pandas as pd

def init():
    global model, columns
    model_path = os.path.join(
        os.getenv("AZUREML_MODEL_DIR"), "model/model_data"
    )
    pf = pd.read_csv(os.getenv("AZUREML_MODEL_DIR"), "model/sample_data.csv")
    columns = pf.columns
    # deserialize the model file back into a sklearn model
    # model = pickle.load(open(model_path,'rb'))
    model = joblib.load(model_path)

def run(raw_data):
    data = json.loads(raw_data)["data"]
    df = pd.DataFrame.from_records(data)
    df.columns = columns
    
    result = model.predict(df)
    return result.tolist()
