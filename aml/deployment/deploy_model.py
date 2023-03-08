import argparse
import os
# import required libraries
from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    ManagedOnlineEndpoint,
    ManagedOnlineDeployment,
    Model,
    Environment,
    CodeConfiguration,
)
from azure.identity import DefaultAzureCredential
import datetime

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace-name', type=str, dest="workspace_name")
    parser.add_argument('--subscription-id', type=str, dest="subscription_id")
    parser.add_argument('--resource-group', type=str, dest="resource_group")
    parser.add_argument('--model-name', type=str, dest="model_name")
    
    (args, extra_args) = parser.parse_known_args()

    # enter details of your AML workspace
    workspace_name = args.workspace_name
    subscription_id = args.subscription_id
    resource_group = args.resource_group
    model_name = args.model_name

    # get a handle to the workspace
    ml_client = MLClient(
        DefaultAzureCredential(), subscription_id, resource_group, workspace_name
    )

    online_endpoint_name = "endpoint-" + datetime.datetime.now().strftime("%m%d%H%M%f")

    # create an online endpoint
    endpoint = ManagedOnlineEndpoint(
        name=online_endpoint_name,
        description="endpoint for mlops workshop",
        auth_mode="key",
        tags={"foo": "bar"},
    )

    ml_client.online_endpoints.begin_create_or_update(endpoint).result()


    model = Model(path=model_name)
    env = Environment(
        conda_file="model-1/environment/conda.yml",
        image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest",
    )

    blue_deployment = ManagedOnlineDeployment(
        name="blue",
        endpoint_name=online_endpoint_name,
        model=model,
        environment=env,
        code_configuration=CodeConfiguration(
            code="model-1/onlinescoring", scoring_script="score.py"
        ),
        instance_type="Standard_DS3_v2",
        instance_count=1,
    )