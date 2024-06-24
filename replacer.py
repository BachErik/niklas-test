import helper, argparse, sys, yaml, re, base64, os
from kubernetes import client

def is_valid_manifest(manifest) -> bool:
    return manifest.get("apiVersion") and manifest.get("kind") and manifest.get("metadata")

def is_secret_manifest(manifest) -> bool:
    return is_valid_manifest(manifest) and manifest["apiVersion"].startswith("v") and manifest["kind"] == "Secret" and manifest.get("data")

def process_data(match: re.Match):
    namespace, type, name, key = match.groups()
    secret_value = get_data(namespace, type, name, key)
    if args.argocd_mode:
        application_namespace = os.getenv("ARGOCD_APP_NAMESPACE")
        application = os.getenv("ARGOCD_APP_NAME")
        application_source_path = os.getenv("ARGOCD_APP_SOURCE_PATH")
        add_resource_reference(application_namespace, application, application_source_path, namespace, type, name)
    return secret_value

def get_data(namespace: str, type: str, name: str, key: str) -> str:
    if type == "configmap":
        config_map = api_instance.read_namespaced_config_map(name, namespace)
        return config_map.data.get(key)
    secret = api_instance.read_namespaced_secret(name, namespace)
    return base64.b64decode(secret.data.get(key)).decode()

def add_resource_reference(application_namespace: str, application: str, application_source_path: str, namespace: str, type: str, name: str):
    config_map = api_instance.read_namespaced_config_map("kph", args.argocd_namespace)
    patch = {
        "data": {}
    }
    if config_map.data is not None:
        if config_map.data.get(f"{application_namespace}.{application}/{application_source_path}") is not None:
            if f"{namespace}.{type}.{name}" not in config_map.data[f"{application_namespace}.{application}/{application_source_path}"].split("/"):
                patch["data"][f"{application_namespace}.{application}/{application_source_path}"] = config_map.data[f"{application_namespace}.{application}/{application_source_path}"]
            else:
                return
        else:
            patch["data"][f"{application_namespace}.{application}/{application_source_path}"] = ""
    else:
        patch["data"][f"{application_namespace}.{application}/{application_source_path}"] = ""
    resources = patch["data"][f"{application_namespace}.{application}/{application_source_path}"].split("/")
    resources.append(f"{namespace}.{type}.{name}")
    resources = "/".join(resources)
    if resources.startswith("/"):
        resources = resources[1:]
    patch["data"][f"{application_namespace}.{application}/{application_source_path}"] = resources
    api_instance.patch_namespaced_config_map("kph", args.argocd_namespace, patch)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--argocd-namespace", "-an", help="Argocd Namespace", type=str, default="argocd")
    parser.add_argument("--argocd-mode", "-am", action="store_true")
    args = parser.parse_args()
    helper.load_config()

    input = sys.stdin.read()
    manifest_files = list(yaml.safe_load_all(input))
    manifest_files = [x for x in manifest_files if x is not None]
    invalid_manifest_files = []

    namespace_pattern = r'[a-z0-9](?:[-a-z0-9]*[a-z0-9])?'
    type_pattern = r'secret|configmap'
    name_pattern = r'[a-z0-9](?:[-a-z0-9]*[a-z0-9])?(?:\.[a-z0-9](?:[-a-z0-9]*[a-z0-9])?)*'
    key_pattern = r'[-._a-zA-Z0-9]+'
    pattern = rf'<({namespace_pattern}):({type_pattern}):({name_pattern}):({key_pattern})>'

    api_instance = client.CoreV1Api()
    for index, manifest in enumerate(manifest_files):
        if is_valid_manifest(manifest):
            if is_secret_manifest(manifest):
                for key in manifest["data"]:
                    secret = base64.b64decode(manifest["data"][key]).decode()
                    encoded_secret = base64.b64encode(re.sub(pattern, process_data, secret).encode("ascii")).decode()
                    manifest["data"][key] = encoded_secret
        else:
            invalid_manifest_files.append(index)
    for invalid_manifest in invalid_manifest_files:
        del manifest_files[invalid_manifest]
    
    output = yaml.safe_dump_all(manifest_files, default_flow_style=False, sort_keys=False)
    output = re.sub(pattern, process_data, output)
    print(output, end="")
