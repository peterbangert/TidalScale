import yaml
from config import config
import os


import logging
logger = logging.getLogger(__name__)


def load_config(args):

    if not os.path.exists(args.config_path):
        print("No VolumeMount config path or given config path, using local config.")
    else:
        print("VolumeMount of input config directory found, loading configuration files")
        config_filenames = next(os.walk(args.config_path), (None, None, []))[2]
        for config_file in config_filenames:
            with open(os.path.join(args.config_path, config_file), "r") as f:
                configmap = yaml.safe_load(f)
                config_headers = [x for x in configmap]
                for header in config_headers:
                    # Right-Merge two Attributes if they are Dict objects, VolumeMount config overrides local
                    # If Attribute is List, String, or Int; override local value with VolumeMount value
                    attribute = None
                    if type(configmap[header]) is dict:
                        try:
                            attr_dict = getattr(config, header)
                        except AttributeError as e:
                            print(f"No Attribute: {header} in config, using default empty dict")
                            attr_dict = {}
                        attribute = {**attr_dict, **configmap[header]}
                    else:
                        attribute = configmap[header]

                    setattr(config, header, attribute)
                    