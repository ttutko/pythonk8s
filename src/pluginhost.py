import subprocess
import sys
import logging
from jinja2 import FileSystemLoader, Environment, Template


logger = logging.getLogger("pluginhost")

def create_or_update_deployment(
    platform_name: str,
    platform_id: str,
    deploy_message):

    replicas = deploy_message['replicas']
    env_vars = deploy_message['environmentVars']
    container_env_vars: List[client.V1EnvVar] = []

    for ev in env_vars or []:
        k,v = ev.split("=", 1)
        logger.info(f"Key: {k}, Value: {v}")
        new_var = client.V1EnvVar(
            name=k,
            value=v
        )
        container_env_vars.append(new_var)

    loader = FileSystemLoader("templates")
    env = Environment(
        loader=loader,
        autoescape=select_autoescape()
    )

    template=env.get_template("plugintest.yml")
    if template is None:
        logger.info("Template not found!")
    else:
        logger.info("Template FOUND!")
        data={"platformName": "myplatform"}
        rendered_template = template.render(data)
        logger.info(f"Rendered template: {rendered_template}")

    return True
