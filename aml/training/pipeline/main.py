from azureml.core import Workspace, Dataset, Datastore, Experiment, Environment
from azureml.core.compute import AmlCompute
from azureml.pipeline.steps import PythonScriptStep
from azureml.core.runconfig import RunConfiguration
from azureml.pipeline.steps import PythonScriptStep
from azureml.pipeline.core import PipelineParameter, StepSequence, Pipeline

import os

subscription_id = 'dac8073e-1c2d-4a7d-a53b-c3655e291d58'
resource_group = 'Learning'
workspace_name = 'learningmain'

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
                            source_directory='./program',
                            runconfig = run_config,
                            allow_reuse = False)

steps = StepSequence(steps = [run_step])
pipeline = Pipeline(workspace=ws, steps=steps)
pipeline.validate()

Experiment(ws, "PIPELINE_MAIN_Run").submit(pipeline, regenerate_outputs=True)
