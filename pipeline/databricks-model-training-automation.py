import sys
from databricks_api import DatabricksAPI
import time
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', type=str, dest='token')
    parser.add_argument('--build-id', type=str, dest='build_id')
    parser.add_argument('--workspace-name', type=str, dest="workspace_name")
    parser.add_argument('--subscription-id', type=str, dest="subscription_id")
    parser.add_argument('--resource-group', type=str, dest="resource_group")
    parser.add_argument('--service-principal-id', type=str, dest="service_principal_id")
    parser.add_argument('--tenant-id', type=str, dest="tenant_id")
    parser.add_argument('--svc-pr-password', type=str, dest="svc_pr_password")
    parser.add_argument('--repo-id', type=int, dest="repo_id")
    parser.add_argument('--databricks-host', type=int, dest="databricks_host")
    parser.add_argument('--cluster-id', type=int, dest="cluster_id")

    (args, extra_args) = parser.parse_known_args()

    token = args.token
    build_id = args.build_id
    workspace_name = args.workspace_name
    subscription_id = args.subscription_id
    resource_group = args.resource_group
    service_principal_id = args.service_principal_id
    tenant_id = args.tenant_id
    svc_pr_password = args.svc_pr_password
    repo_id = args.repo_id
    databricks_host = args.databricks_host
    cluster_id = args.cluster_id


    db = DatabricksAPI(
        host=databricks_host,
        token=token
    )

    db.repos.update_repo(
        id = repo_id,
        branch='main'
    )


    params = {
        "workspace_name": workspace_name,
        "subscription_id": subscription_id,
        "resource_group": resource_group,
        "service_principal_id": service_principal_id,
        "tenant_id": tenant_id,
        "svc_pr_password": svc_pr_password
    }


    job_id = db.jobs.create_job(
        name="ml-ops-model-training-{}".format(build_id),
        existing_cluster_id=cluster_id,
        notebook_task={
        "notebook_path":"/Repos/hossein.sarshar@microsoft.com/databricks-aml-mlops-workshop/model_training",
        "base_parameters": params
        }
    )['job_id']

    run_id = db.jobs.run_now(
        job_id=job_id
    )['run_id']

    N = 30
    for i in range(N):
        try:
            status = db.jobs.get_run(run_id=run_id)['state']['result_state']
        except:
            status = 'UNKNOWN'
        if status == 'SUCCESS':
            print('Job is successful')
            break
        elif status == 'FAILED':
            raise Exception('Job failed')
        else:
            print('Job is not successful yet, waiting 1 minute')
            time.sleep(60)
    if i == N - 1:
        raise Exception('job timed out after 30 mins. Please check Databricks job')
