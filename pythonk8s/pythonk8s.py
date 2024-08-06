from kubernetes import client, config

SVC_ACCOUNT = "my_service_account"
NAMESPACE = "mynamespace"
NUM_REPLICAS = 3

# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()

v1 = client.CoreV1Api()
print("Listing pods with their IPs:")
ret = v1.list_pod_for_all_namespaces(watch=False)
for i in ret.items:
    print(f"{i.status.pod_ip}\t{i.metadata.namespace}\t{i.metadata.name}")

dep_container = client.V1Container(
    name="nginx",
    image="nginx:1.15.4",
    ports=[client.V1ContainerPort(container_port=80)],
    resources=client.V1ResourceRequirements(
        requests={"cpu": "100m", "memory": "200Mi"},
        limits={"cpu": "500m", "memory": "500Mi"},
    ),
)

template = client.V1PodTemplateSpec(
    metadata=client.V1ObjectMeta(labels={"app": "myclient"}),
    spec = client.V1PodSpec(containers=[dep_container]),
)


dep_spec = client.V1DeploymentSpec(
    replicas=NUM_REPLICAS,
    template=template,
    selector={
        "matchLabels": {"app": "myclient"}
    }
)



# dep_metadata = client.V1ObjectMeta()
# dep_metadata.name = "my_deployment"
# dep_metadata.namespace = NAMESPACE
# dep_selector = client.V1LabelSelector()
# dep_selector.match_labels = { "app": "myclient" }
# dep_spec.selector = dep_selector

deployment = client.V1Deployment(
    api_version="apps/v1",
    kind="Deployment",
    metadata=client.V1ObjectMeta(name="my-deployment", namespace=NAMESPACE),
    spec=dep_spec
)

namespace=client.V1Namespace()
namespace.metadata = client.V1ObjectMeta(name=NAMESPACE)

v1.replace_namespace(name=NAMESPACE, body=namespace)
# v1.create_namespace(body=namespace)
apps_v1 = client.AppsV1Api()
resp = apps_v1.create_namespaced_deployment(
    body=deployment,
    namespace=NAMESPACE
)

print(f"{type(resp)}")

print(f"\n[INFO] deployment: `{deployment.metadata.name}` created.\n" )
print("NAMESPACE\tNAME\tREVISION\tIMAGE")
print(f"{resp.metadata.namespace}\t{resp.metadata.name}\t{resp.metadata.generation}\t{resp.spec.template.spec.containers[0].image}")
