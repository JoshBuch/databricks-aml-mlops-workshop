from databricks_api import DatabricksAPI
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', type=str, dest='token')
    parser.add_argument('--databricks-host', type=str, dest='databricks_host')
    parser.add_argument('--sp-secret-val', type=str, dest='sp_secret_val')
    
    (args, extra_args) = parser.parse_known_args()
    print('args', args)

    token = args.token
    databricks_host = args.databricks_host

    db = DatabricksAPI(
        host=databricks_host,
        token=token
    )

    scope_name= 'adb-secrets'
    db.secret.create_scope(
        scope_name,
        initial_manage_principal='users',
    )

    secret_valu = args.sp_secret_val
    db.secret.put_secret(
        scope_name,
        'svc_pr_password',
        string_value=secret_valu
    )

    print(db.repos.list_repos())
