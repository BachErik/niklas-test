import sys, re, base64
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
    pattern = r'<([a-z0-9](?:[-a-z0-9]*[a-z0-9])?):(secret|configmap):([a-z0-9](?:[-a-z0-9]*[a-z0-9])?(?:\.[a-z0-9](?:[-a-z0-9]*[a-z0-9])?)*):([-._a-zA-Z0-9]+)>'
    output = re.sub(pattern, replace_pattern, input)
    print(output, end="")
