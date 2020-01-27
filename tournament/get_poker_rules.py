from os.path import join
import yaml


def read_config_file(file_path):

    if type(file_path) is str and '.yaml' not in file_path:
        file_path = join(file_path, 'config.yaml')

    with open(file_path, 'r') as file:
        rule_dict = yaml.safe_load(file)
    return rule_dict


def default_rules():
    rule_dict = {}
    rule_dict['initial stack'] = 1000
    rule_dict['small blind'] = 10
    rule_dict['big blind'] = 20
    rule_dict['minimum raise'] = 10
    rule_dict['timeout'] = 5  # in seconds
    return rule_dict
