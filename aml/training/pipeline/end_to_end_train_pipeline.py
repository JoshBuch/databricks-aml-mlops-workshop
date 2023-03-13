import os
import azureml.core
from azureml.core.runconfig import JarLibrary
from azureml.core.compute import ComputeTarget, DatabricksCompute
from azureml.exceptions import ComputeTargetException
from azureml.core import Workspace, Environment, Experiment, Datastore, Dataset, ScriptRunConfig
from azureml.pipeline.core import Pipeline, PipelineData, TrainingOutput
from azureml.pipeline.steps import DatabricksStep, PythonScriptStep
from azureml.core.datastore import Datastore
from azureml.data.data_reference import DataReference
from azureml.core.conda_dependencies import CondaDependencies
from azureml.train.automl import AutoMLConfig
from azureml.pipeline.core import PipelineData, TrainingOutput
from azureml.pipeline.steps import AutoMLStep
from azureml.core.runconfig import RunConfiguration
from azureml.pipeline.core import PipelineParameter
from azureml.pipeline.core.pipeline_output_dataset import PipelineOutputAbstractDataset
import argparse
import os

# Check core SDK version number
print("SDK version:", azureml.core.VERSION)

def register_dataset(ws, datastore, dataset_name):
    remote_path = f'dataset-demo/{dataset_name}/'
    local_path = 'aml/training/pipeline/data/titanic.csv'
    datastore.upload_files(files = [local_path],
                    target_path = remote_path,
                    overwrite = True,
                    show_progress = False)
    
    dataset = Dataset.Tabular.from_delimited_files(path = [(datastore, remote_path)])
    dataset = dataset.register(ws, name=dataset_name, create_new_version=True)
    return dataset

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace-name', type=str, dest="workspace_name")
    parser.add_argument('--subscription-id', type=str, dest="subscription_id")
    parser.add_argument('--resource-group', type=str, dest="resource_group")
    parser.add_argument('--adb-attached-compute-name', type=str, dest="adb_attached_compute_name")
    parser.add_argument('--cluster-id', type=str, dest="adb_cluster_id")
    parser.add_argument('--aml-train-cluster-id', type=str, dest="aml_train_cluster_id")
    parser.add_argument('--aml-register-cluster-id', type=str, dest="aml_register_cluster_id")
    
    (args, extra_args) = parser.parse_known_args()
    print('args', args)

    workspace_name = args.workspace_name
    subscription_id = args.subscription_id
    resource_group = args.resource_group
    adb_cluster_id = args.adb_cluster_id
    aml_train_cluster_id = args.aml_train_cluster_id
    aml_register_cluster_id = args.aml_register_cluster_id
    adb_attached_compute_name = args.adb_attached_compute_name

    ws = Workspace(subscription_id, resource_group, workspace_name)

    db_compute_name = adb_attached_compute_name # Databricks compute name

    databricks_compute = DatabricksCompute(workspace=ws, name=db_compute_name)
    print('Compute target {} already exists'.format(db_compute_name))
    
    def_blob_store = ws.get_default_datastore()
    print('Datastore {} will be used'.format(def_blob_store.name))

    ds_titanic_1 = register_dataset(ws, def_blob_store, 'titanic_1')
    ds_titanic_2 = register_dataset(ws, def_blob_store, 'titanic_2')
    ds_titanic_3 = register_dataset(ws, def_blob_store, 'titanic_3')

    ds_step_1_train = PipelineData("output_train", datastore=def_blob_store).as_dataset()
    ds_step_1_test = PipelineData("output_test", datastore=def_blob_store).as_dataset()

    source_directory = "aml/training/pipeline/scripts"

    databricks_script_name = "adb_run_automl.py"

    feature_dataset_name_train = "feature_titanic_train"
    feature_dataset_name_test = "feature_titanic_test"

    target_col = 'Survived'

    dbNbStep = DatabricksStep(
        name="ADB_Feature_Eng",
        outputs=[ds_step_1_train, ds_step_1_test],
        compute_target=databricks_compute,
        existing_cluster_id=adb_cluster_id,
        python_script_params=["--feature_set_1", ds_titanic_1.name,
                            "--feature_set_2", ds_titanic_2.name,
                            "--feature_set_3", ds_titanic_3.name,
                            '--target-col', target_col,
                            '--output_datastore_name', def_blob_store.name,
                            "--output_train_feature_set_name", feature_dataset_name_train, 
                            "--output_test_feature_set_name", feature_dataset_name_test],
        permit_cluster_restart=True,
        python_script_name=databricks_script_name,
        source_directory=source_directory,
        run_name='ADB_Feature_Eng',
        allow_reuse=True
    )

    cluster_name = aml_train_cluster_id
    compute_target = ComputeTarget(workspace=ws, name=cluster_name)

    # Change iterations to a reasonable number (50) to get better accuracy
    automl_settings = {
        "iteration_timeout_minutes" : 10,
        "iterations" : 2,
        "primary_metric" : 'AUC_weighted',
        "n_cross_validations": 5
    }

    automl_config = AutoMLConfig(task = 'classification',
                                debug_log = 'automated_ml_errors.log',
                                compute_target = compute_target,
                                featurization = 'auto',
                                training_data = ds_step_1_train.parse_parquet_files(),
                                test_data = ds_step_1_test.parse_parquet_files(),
                                label_column_name = target_col,
                                **automl_settings)
                                
    print("AutoML config created.")

    metrics_output_name = 'metrics_output'
    best_model_output_name = 'best_model_output'

    metrics_data = PipelineData(name='metrics_data',
                            datastore=def_blob_store,
                            pipeline_output_name=metrics_output_name,
                            training_output=TrainingOutput(type='Metrics'))
    model_data = PipelineData(name='model_data',
                            datastore=def_blob_store,
                            pipeline_output_name=best_model_output_name,
                            training_output=TrainingOutput(type='Model'))

    train_automlStep = AutoMLStep(name='AutoML_Classification',
                                 automl_config=automl_config,
                                 outputs=[metrics_data, model_data],
                                 allow_reuse=True)

    print("trainWithAutomlStep created.")

    reg_comp_name = aml_register_cluster_id
    reg_compute_target = ComputeTarget(workspace=ws, name=reg_comp_name)

    conda_dep = CondaDependencies()
    conda_dep.add_pip_package("azureml-sdk[automl]")

    rcfg = RunConfiguration(conda_dependencies=conda_dep)

    register_model_step = PythonScriptStep(script_name='register_model.py',
                                        source_directory=source_directory,
                                        name="Register_Best_Model",
                                        inputs=[model_data],
                                                # ds_step_1_train.parse_parquet_files().as_named_input('input_train'), 
                                                # ds_step_1_test.parse_parquet_files().as_named_input('input_test')],
                                        compute_target=reg_compute_target,
                                        arguments=["--saved-model", model_data,
                                                    '--model-name' , 'titanic_model',
                                                    '--target-col', target_col,
                                                    '--featureset-name-train', feature_dataset_name_train,
                                                    '--featureset-name-test', feature_dataset_name_test],
                                        allow_reuse=True,
                                        runconfig=rcfg)

    steps = [dbNbStep, train_automlStep, register_model_step]
    pipeline = Pipeline(workspace=ws, steps=steps)
    pipeline_run = Experiment(ws, 'DB_FeatureStore_AutoML_Register').submit(pipeline)
