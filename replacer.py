import sys, re, base64, yaml
from kubernetes import client, config

def read_data(namespace, type, name, key):
    if type == "secret":
        secret = api_instance.read_namespaced_secret(name, namespace)
        return base64.b64decode(secret.data.get(key)).decode()
    else:
        config_map = api_instance.read_namespaced_config_map(name, namespace)
        return config_map.data.get(key)

def replace_pattern(match):
    namespace, type, name, key = match.groups()
    secret_value = read_data(namespace, type, name, key)
    return secret_value

if __name__ == "__main__":
    input = sys.stdin.read()
    config.load_incluster_config()
    api_instance = client.CoreV1Api()
    manifest_files = list(yaml.safe_load_all(input))
    manifest_files = [x for x in manifest_files if x is not None]
    invalid_manifest_files = []
    namespace_pattern = r'[a-z0-9](?:[-a-z0-9]*[a-z0-9])?'
    type_pattern = r'secret|configmap'
    name_pattern = r'[a-z0-9](?:[-a-z0-9]*[a-z0-9])?(?:\.[a-z0-9](?:[-a-z0-9]*[a-z0-9])?)*'
    key_pattern = r'[-._a-zA-Z0-9]+'
    pattern = rf'<({namespace_pattern}):({type_pattern}):({name_pattern}):({key_pattern})>'
    for index, manifest in enumerate(manifest_files):
        if manifest.get("apiVersion") and manifest.get("kind") and manifest.get("metadata"):
            if manifest["apiVersion"].startswith("v") and manifest["kind"] == "Secret" and manifest.get("data"):
                for key in manifest["data"]:
                    secret = base64.b64decode(manifest["data"][key]).decode()
                    encoded_secret = base64.b64encode(re.sub(pattern, replace_pattern, secret).encode("ascii")).decode()
                    manifest["data"][key] = encoded_secret
        else:
            invalid_manifest_files.append(index)
    for invalid_manifest in invalid_manifest_files:
        del manifest_files[invalid_manifest]
    input = yaml.safe_dump_all(manifest_files, default_flow_style=False, sort_keys=False)
    output = re.sub(pattern, replace_pattern, input)
    #print(output, end="")
    print(manifest_files)
