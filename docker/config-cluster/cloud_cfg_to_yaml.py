#!/usr/bin/env python3

import configparser
import os
import sys


def usage_error():
    print(os.path.basename(__file__), "<k8s cloud_config> <cloud name> <clouds.yaml>", file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        usage_error()

    cloud_cfg_file = sys.argv[1]
    cloud_name = sys.argv[2]
    clouds_yaml_file = sys.argv[3]

    cfg = configparser.ConfigParser()
    cfg.read(cloud_cfg_file)
    global_section = cfg["Global"]

    template = """
clouds:
  {cloud}:
    auth:
      auth_url: {auth_url}
      username: {username}
      password: {password}
      project_id: {project_id}
      user_domain_name: {project_domain_name}
      project_domain_name: {project_domain_name}
    region_name: {region_name}
"""
    yml_string = template.format(
        cloud=cloud_name,
        auth_url=global_section['auth-url'],
        username=global_section['username'],
        password=global_section['password'],
        project_id=global_section.get('tenant-id', ''),
        user_domain_name=global_section.get('domain-name', 'default'),
        project_domain_name=global_section.get('domain-name', 'default'),
        region_name=global_section.get('region', ''))

    with open(clouds_yaml_file, 'w') as f:
        f.write(yml_string)
