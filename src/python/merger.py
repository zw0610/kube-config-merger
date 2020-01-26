import os
from copy import deepcopy
from functools import reduce

import yaml

import cli.app


class Config:
    _keys_str = {
        "apiVersion",
        "current-context",
        "kind"
    }

    _keys_list = {
        "clusters",
        "contexts",
        "users"
    }

    @staticmethod
    def verify(config):
        return False not in [k in config.get_content().keys() for k in Config._keys_str.union(Config._keys_list)]

    def __init__(self, config=None):
        self._content = {}
        if config is not None:
            self._content = deepcopy(config)

    def is_empty(self):
        return self._content == {}

    def get_content(self):
        return self._content

    def __add__(self, config):
        if self.is_empty():
            return deepcopy(config.get_content())

        if config.is_empty():
            return self.get_content()

        assert Config.verify(self) == True
        assert Config.verify(config) == True

        assert self._content['kind'] == 'Config'
        assert config.get_content()['kind'] == 'Config'

        assert self._content['apiVersion'] == config.get_content()['apiVersion']

        merged = {k: self._content[k] + config.get_content()[k] for k in Config._keys_list}

        merged['kind'] = 'Config'
        merged['apiVersion'] = self._content['apiVersion']
        merged['current-context'] = self._content['current-context']

        return Config(deepcopy(merged))

    def __iadd__(self, config):
        if self._content == {}:
            self._content = deepcopy(config.get_content())
        else:
            self._content = self.__add__(config)


class KubeConfigMerger(cli.app.CommandLineApp):

    def _parse_files(self):
        self._input_files = []
        print(f"KubeConfigMerger is merging {len(self.params.inputs)} files: {' '.join(self.params.inputs)}")
        assert len(self.params.inputs) >= 2
        self._input_files = self.params.inputs

    def _convert_to_yaml(self, filename):
        try:
            with open(filename) as f:
                yaml_obj = yaml.load(f, Loader=yaml.FullLoader)
        except Exception as e:
            raise e
        else:
            return yaml_obj

    def _write_config(self, config):
        output_file = os.path.join(self.params.output, "config")

        with open(output_file, 'w') as f:
            print(f"KubeConfigMerger is writing new config file to {output_file}")
            f.write(
                yaml.dump(config.get_content())
            )

    def main(self):
        self._parse_files()

        yaml_obj_list = [self._convert_to_yaml(filename) for filename in self._input_files]
        configs = [Config(y) for y in yaml_obj_list]
        merged_config = reduce(lambda x, y: x + y, configs)

        self._write_config(config=merged_config)


app = KubeConfigMerger()

app.add_param("-v", "--verbose", default=0, action="count",
              help="increase the verbosity", )

app.add_param("-i", "--inputs", default="", nargs='+', help="path to input config files, separated by space")
app.add_param("-o", "--output", default="/tmp", help="directory where the merged config file will be stored, default "
                                                     "is /tmp")

if __name__ == "__main__":
    app.run()
