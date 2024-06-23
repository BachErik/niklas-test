from kubernetes import config

def load_config():
    try:
        config.load_incluster_config()
    except config.config_exception.ConfigException:
        config.load_kube_config()