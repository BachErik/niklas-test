import helper, argparse, threading
from kubernetes import client, watch

def watch_config_maps():
    watcher = watch.Watch()
    for event in watcher.stream(api_instance.list_namespaced_config_map, namespace=""):
        update_helper("configmap", event)

def watch_secrets():
    watcher = watch.Watch()
    for event in watcher.stream(api_instance.list_namespaced_secret, namespace=""):
        update_helper("secret", event)

def watch_applications():
    watcher = watch.Watch()
    for event in watcher.stream(custom_api_instance.list_namespaced_custom_object, "argoproj.io", "v1alpha1", "", "applications"):
        if event["type"] == "DELETED":
            application = event["object"]
            patch = {
                "data": {
                    f"{application.metadata.namespace}.{application.metadata.name}": None
                }
            }
            api_instance.patch_namespaced_config_map("kph", args.argocd_namespace, patch)

def update_helper(type: str, event):
    object = event["object"]
    application = get_application(object.metadata.namespace, type, object.metadata.name)
    if application is not None:
        update_application(application[0], application[1])

def get_application(namespace: str, type: str, name: str) -> tuple:
    config_map = api_instance.read_namespaced_config_map("kph", args.argocd_namespace)
    if config_map.data is not None:
        for application in config_map.data:
            resources = config_map.data[application].split("/")
            for resource in resources:
                application_namespace = resource.split(".")[0]
                application_type = resource.split(".")[1]
                application_name = resource.split(".", maxsplit=2)[2]
                if namespace == application_namespace and type == application_type and name == application_name:
                    return (application.split(".")[0], application.split(".", maxsplit=1)[1])
    return None

def update_application(namespace: str, name: str):
    patch = {
        "metadata": {
            "annotations": {
                "argocd.argoproj.io/refresh": "hard"
            }
        }
    }
    custom_api_instance.patch_namespaced_custom_object("argoproj.io", "v1alpha1", namespace, "applications", name, patch)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--argocd-namespace", "-an", help="Argocd Namespace", type=str, default="argocd")
    args = parser.parse_args()
    helper.load_config()

    api_instance = client.CoreV1Api()
    custom_api_instance = client.CustomObjectsApi()
    watch_config_map_thread = threading.Thread(target=watch_config_maps)
    watch_secret_thread = threading.Thread(target=watch_secrets)
    watch_application_thread = threading.Thread(target=watch_applications)
    watch_config_map_thread.start()
    watch_secret_thread.start()
    watch_application_thread.start()
    watch_config_map_thread.join()
    watch_secret_thread.join()
    watch_application_thread.join()
