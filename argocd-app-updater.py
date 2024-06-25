import helper, argparse, threading, socket
from queue import Queue
from kubernetes import client, watch

def watch_config_maps():
    watcher = watch.Watch()
    while True:
        try:
            for event in watcher.stream(api_instance.list_namespaced_config_map, namespace=""):
                update_helper("configmap", event)
        except client.exceptions.ApiException as exception:
            if exception.status == 410:
                continue
            raise

def watch_secrets():
    watcher = watch.Watch()
    while True:
        try:
            for event in watcher.stream(api_instance.list_namespaced_secret, namespace=""):
                update_helper("secret", event)
        except client.exceptions.ApiException as exception:
            if exception.status == 410:
                continue
            raise

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

def process_queue():
    while True:
        application_namespace, application, resource_namespace, resource_type, resource = reference_queue.get()
        config_map = api_instance.read_namespaced_config_map("kph", args.argocd_namespace)
        patch = {
            "data": {}
        }
        if config_map.data is not None:
            if config_map.data.get(f"{application_namespace}.{application}") is not None:
                if f"{resource_namespace}.{resource_type}.{resource}" not in config_map.data[f"{application_namespace}.{application}"].split("/"):
                    patch["data"][f"{application_namespace}.{application}"] = config_map.data[f"{application_namespace}.{application}"]
                else:
                    return
            else:
                patch["data"][f"{application_namespace}.{application}"] = ""
        else:
            patch["data"][f"{application_namespace}.{application}"] = ""
        resources = patch["data"][f"{application_namespace}.{application}"].split("/")
        resources.append(f"{resource_namespace}.{resource_type}.{resource}")
        resources = "/".join(resources)
        if resources.startswith("/"):
            resources = resources[1:]
        patch["data"][f"{application_namespace}.{application}"] = resources
        api_instance.patch_namespaced_config_map("kph", args.argocd_namespace, patch)

def client_acceptor():
    while True:
        client_socket, address = server.accept()
        client_handler_thread = threading.Thread(target=client_handler, args=(client_socket, address))
        client_handler_thread.start()

def client_handler(client_socket: socket.socket, address):
    while True:
        try:
            message = client_socket.recv(1024).decode("utf-8")
            if message:
                application_namespace = message.split(" ")[0]
                application = message.split(" ")[1]
                resource_namespace = message.split(" ")[2]
                resource_type = message.split(" ")[3]
                resource = message.split(" ")[4]
                reference_queue.put((application_namespace, application, resource_namespace, resource_type, resource))
            break
        except:
            break
    client_socket.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--argocd-namespace", "-an", help="Argocd Namespace", type=str, default="argocd")
    parser.add_argument("--host", help="Host", type=str, default="127.0.0.1")
    parser.add_argument("--port", "-p", type=int, default=1234)
    args = parser.parse_args()
    helper.load_config()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((args.host, args.port))
    server.listen()

    api_instance = client.CoreV1Api()
    custom_api_instance = client.CustomObjectsApi()
    reference_queue = Queue()
    process_queue_thread = threading.Thread(target=process_queue)
    client_acceptor_thread = threading.Thread(target=client_acceptor)
    watch_config_map_thread = threading.Thread(target=watch_config_maps)
    watch_secret_thread = threading.Thread(target=watch_secrets)
    watch_application_thread = threading.Thread(target=watch_applications)
    process_queue_thread.start()
    client_acceptor_thread.start()
    watch_config_map_thread.start()
    watch_secret_thread.start()
    watch_application_thread.start()
    process_queue_thread.join()
    client_acceptor_thread.join()
    watch_config_map_thread.join()
    watch_secret_thread.join()
    watch_application_thread.join()