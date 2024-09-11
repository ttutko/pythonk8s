import subprocess
import sys
import logging
from datetime import datetime
from jinja2 import FileSystemLoader, Environment, Template, select_autoescape


logger = logging.getLogger("pluginhost")

KUBECTL="kubectl"

def create_or_update_deployment(
    platform_name: str,
    platform_id: str,
    deploy_message):

    replicas = deploy_message['replicas']
    env_vars = deploy_message['environmentVars']
    # container_env_vars: List[client.V1EnvVar] = []
    container_env_vars = []

    for ev in env_vars or []:
        k,v = ev.split("=", 1)
        logger.info(f"Key: {k}, Value: {v}")
        # new_var = client.V1EnvVar(
        #     name=k,
        #     value=v
        # )
        new_var = { "name": k, "value": v }
        container_env_vars.append(new_var)

    loader = FileSystemLoader("src/templates")
    env = Environment(
        loader=loader,
        autoescape=select_autoescape()
    )

    data= {
        "platformName": deploy_message['name'],
        "env_vars": container_env_vars,
        "replicas": deploy_message['replicas']
    }

    template=env.get_template("plugin-deployment.yml")
    if template is None:
        logger.info("Template not found!")
    else:
        # data={"platformName": "myplatform"}
        rendered_template = template.render(data)
        logger.info(f"Rendered template: {rendered_template}")

        ymlfilename=f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{data['platformName']}-deployment.yml"
        with open(ymlfilename, 'wt') as ymlf:
            ymlf.write(rendered_template)

        try:
            command_line = f"kubectl apply -f {ymlfilename}"
            logger.info(f"Running: {command_line}") 
            process = subprocess.run(command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=120)
            output = process.stdout
            return_code = process.returncode
            logger.info(f"Return Code: {return_code}\nOutput:\n{output}")
        except subprocess.TimeoutExpired as ex:
            logger.error("The process timed out!")
            return False

    return True
