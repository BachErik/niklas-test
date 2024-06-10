import sys, re, base64
from kubernetes import client, config

def read_data(namespace, type, name, key):
    if type == "secret":
        secret = api_instance.read_namespaced_secret(name, namespace)
        if secret.data:
            return base64.b64decode(secret.data.get(key)).decode()
    if type == "configmap":
        config_map = api_instance.read_namespaced_config_map(name, namespace)
        if config_map.data:
            return config_map.data.get(key)
    return ""

def replace_pattern(match):
    namespace, type, name, key = match.groups()
    secret_value = read_data(namespace, type, name, key)
    return secret_value

if __name__ == "__main__":
    input = sys.stdin.read()
    #config.load_kube_config()
    config.load_incluster_config()
    api_instance = client.CoreV1Api()
    pattern = r'<([^:]+):([^:]+):([^:]+):([^>]+)>'
    output = re.sub(pattern, replace_pattern, input)
    print(output, end="")
