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
    parser.add_argument('--endpoint-name', type=str, dest="endpoint_name")
    parser.add_argument('--online-endpoint-compute-type', type=str, dest="online_endpoint_compute_type", default='Standard_E2s_v3')
    
    (args, extra_args) = parser.parse_known_args()

    # enter details of your AML workspace
    workspace_name = args.workspace_name
    subscription_id = args.subscription_id
    resource_group = args.resource_group
    model_name = args.model_name
    endpoint_name = args.endpoint_name
    online_endpoint_compute_type = args.online_endpoint_compute_type

    # get a handle to the workspace
    ml_client = MLClient(
        DefaultAzureCredential(), subscription_id, resource_group, workspace_name
    )

    # create an online endpoint
    print("Creating endpoint")
    endpoint = ManagedOnlineEndpoint(
        name=endpoint_name,
        description="endpoint for mlops workshop",
        auth_mode="key",
        tags={"foo": "bar"},
    )

    ml_client.online_endpoints.begin_create_or_update(endpoint).result()
    print("Endpoint created")


    model = Model(path=model_name)
    model = list(ml_client.models.list(model_name))[0]
    env = Environment(
        #image="mcr.microsoft.com/azureml/curated/azureml-automl-dnn-text-gpu:56",
        image="mcr.microsoft.com/azureml/curated/azureml-automl:latest"
    )
    print("Deployment sarted")

    deployment_name = 'deployment-' + datetime.datetime.now().strftime("%m%d%H%M%f")
    blue_deployment = ManagedOnlineDeployment(
        name=deployment_name,
        endpoint_name=endpoint_name,
        model=model,
        environment=env,
        code_configuration=CodeConfiguration(
            code="aml/deployment/scoring", scoring_script="score-ext.py"
        ),
        instance_type=online_endpoint_compute_type,
        instance_count=1,
    )

    ml_client.online_deployments.begin_create_or_update(blue_deployment).result()

    print("Deployment complete")