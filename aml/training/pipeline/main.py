from azureml.core import Workspace, Dataset, Datastore, Experiment, Environment
from azureml.core.compute import AmlCompute
from azureml.pipeline.steps import PythonScriptStep
from azureml.core.runconfig import RunConfiguration
from azureml.pipeline.steps import PythonScriptStep
from azureml.pipeline.core import PipelineParameter, StepSequence, Pipeline
import argparse
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-id', type=str, dest='build_id')
    parser.add_argument('--workspace-name', type=str, dest="workspace_name")
    parser.add_argument('--subscription-id', type=str, dest="subscription_id")
    parser.add_argument('--resource-group', type=str, dest="resource_group")
    
    (args, extra_args) = parser.parse_known_args()
    print('args', args)

    workspace_name = args.workspace_name
    subscription_id = args.subscription_id
    resource_group = args.resource_group

    ws = Workspace(subscription_id, resource_group, workspace_name)

    aml_compute = AmlCompute(ws, "cpu-cluster")

    env = Environment('workshop-env')

    env.docker.base_image = 'mcr.microsoft.com/azureml/curated/sklearn-0.24-ubuntu18.04-py37-cpu:latest'
    env.python.user_managed_dependencies = True

    # create a new runconfig object
    run_config = RunConfiguration()
    run_config.environment = env

    print(os.system('pwd'))
    print(os.system('ls -lah'))

    run_step = PythonScriptStep(script_name="main_script.py",
                                compute_target=aml_compute,
                                source_directory='aml/training/pipeline/program',
                                runconfig = run_config,
                                allow_reuse = False)

    steps = StepSequence(steps = [run_step])
    pipeline = Pipeline(workspace=ws, steps=steps)
    pipeline.validate()

    Experiment(ws, "PIPELINE_MAIN_Run").submit(pipeline)
