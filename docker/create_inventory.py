#!/usr/bin/env python2

# Copyright 2018-2019 CRS4 (http://www.crs4.it/)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import argparse
import random
import ConfigParser

VERSION = '0.1.0alpha'


class KubeSprayGroupName(object):
    # Legal group names
    ALL = "all"
    BASTION = 'bastion'
    ETCD = 'etcd'
    CLUSTER = 'k8s-cluster'
    MASTER = 'kube-master'
    NODE = 'kube-node'
    # cache list
    __list__ = None

    @staticmethod
    def list():
        if KubeSprayGroupName.__list__ is None:
            KubeSprayGroupName.__list__ = [KubeSprayGroupName.__dict__[x] for x in KubeSprayGroupName.__dict__ if
                                           not x.startswith('_') and x != 'list']
            KubeSprayGroupName.__list__.sort()
        return KubeSprayGroupName.__list__


class Instance(object):

    def __init__(self, raw_data):
        super(Instance, self).__init__()
        self._raw_data = raw_data

    @property
    def id(self):
        return self._raw_data['primary']['attributes']['id']

    @property
    def name(self):
        return self._raw_data['primary']['attributes']['name']

    @property
    def kubespray_groups(self):
        return self._raw_data['primary']['attributes']['all_metadata.kubespray_groups'].split(',')

    def is_bastion_node(self):
        return 'bastion' in self.kubespray_groups

    @property
    def private_ip(self):
        return self._raw_data['primary']['attributes']['access_ip_v4']

    @property
    def floating_ip(self):
        return self._raw_data['primary']['attributes']['network.0.floating_ip']

    @floating_ip.setter
    def floating_ip(self, fip):
        self._raw_data['primary']['attributes']['network.0.floating_ip'] = fip

    @property
    def ssh_user(self):
        return self._raw_data['primary']['attributes']['metadata.ssh_user']


class TerraformState(object):

    def __init__(self, json_data):
        super(TerraformState, self).__init__()
        self._json_data = json_data
        self._instances, self._fip_associations, self._groups = TerraformState.parse_json_data(json_data)

    @property
    def instances(self):
        return self._instances

    def get_instance_by_id(self, id):
        return self.instances[id]

    @property
    def kubespray_groups(self):
        return self._groups

    def has_private_instances(self):
        for i in self._instances.values():
            if not i.floating_ip:
                return True
        return False

    def get_bastion_instance(self):
        for i in self._instances.values():
            if i.is_bastion_node():
                return i
        return None

    def choose_random_fip_instance(self):
        if len(self._fip_associations) == 0:
            raise Exception("No public IP available!!!")
        return random.choice(self._fip_associations.values())

    @staticmethod
    def parse_json_data(json_data):        
        fips = {}
        public_ips = {}
        instances = {}
        groups = {x: [] for x in KubeSprayGroupName.list()}

        for m in json_data['modules']:
            for r in m['resources']:
                resource = m['resources'][r]                
                rtype = resource['type']
                if rtype == 'openstack_compute_instance_v2':
                    instance = Instance(resource)
                    instances[instance.id] = instance
                    if not instance.is_bastion_node():
                        groups['all'].append(instance.id)
                        for g in instance.kubespray_groups:
                            if g in KubeSprayGroupName.list():
                                groups[g].append(instance.id)
                    if "k8s_master_ext_net" in r: # check master subtype by name
                        instance.floating_ip = resource['primary']['attributes']['network.0.fixed_ip_v4']
                        public_ips[instance.floating_ip] = instance
                elif rtype == 'openstack_compute_floatingip_associate_v2':
                    fips[resource['primary']['attributes']['instance_id']] = resource

        # associate floating ip to instances
        for i_id, instance in instances.items():
            if i_id in fips:
                instance.floating_ip = fips[i_id]['primary']['attributes']['floating_ip']
                public_ips[instance.floating_ip] = instance

        return instances, public_ips, groups

    @staticmethod
    def load(filename):
        with open(filename) as f:
            return TerraformState(json.load(f))


class Inventory(object):

    @staticmethod
    def __format_node_name(instance):
        return 'bastion' if instance.is_bastion_node() else instance.name

    @staticmethod
    def generate(terraform_state, output_stream):
        """

        :param terraform_state:
        :type terraform_state: TerraformState
        :param output_stream:
        :return:
        """
        config = ConfigParser.RawConfigParser(allow_no_value=True)

        # get map group_name -> instance_id list
        groups = terraform_state.kubespray_groups

        # search for a bastion node
        bastion = terraform_state.get_bastion_instance()

        # fill the 'all' section
        config.add_section("all")
        for i in groups['all']:
            instance = terraform_state.instances[i]
            if not instance.is_bastion_node():
                node_name = Inventory.__format_node_name(instance)
                config.set('all', "{} ansible_host={} ip={} ansible_ssh_user={}"
                           .format(node_name,
                                   instance.floating_ip or instance.private_ip,
                                   instance.private_ip,
                                   instance.ssh_user))

        if bastion or terraform_state.has_private_instances():
            bastion = bastion or terraform_state.choose_random_fip_instance()
            config.set('all', "{} ansible_host={} ansible_user={}"
                       .format(KubeSprayGroupName.BASTION, bastion.floating_ip, bastion.ssh_user))
            config.add_section(KubeSprayGroupName.BASTION)
            config.set(KubeSprayGroupName.BASTION, KubeSprayGroupName.BASTION)

        # fill remaining sections
        for group in KubeSprayGroupName.list()[2:]:
            instance_id_list = groups[group]
            config.add_section(group)
            for instance_id in instance_id_list:
                instance = terraform_state.instances[instance_id]
                config.set(group, Inventory.__format_node_name(instance))

        # write the output file
        if output_stream:
            config.write(output_stream)


def run(terraform_state_filepath, inventory_filepath):
    # load the terraform state
    terraform_state = TerraformState.load(terraform_state_filepath)
    # ensure the path exists
    filepath = os.path.dirname(inventory_filepath)
    if filepath and not os.path.exists(filepath):
        os.makedirs(filepath)
    # write the inventory file
    with open(inventory_filepath, 'w') as inventory_file:
        Inventory.generate(terraform_state, inventory_file)


def _build_parse_args():
    parser = argparse.ArgumentParser(__file__, __doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--version', action='store_true', help='print version and exit')
    parser.add_argument('-s', '--terraform-state', default='terraform.tfstate',
                        help='path of the terraform state file')
    parser.add_argument('-o', '--output', default='hosts.ini', help='path of the output file')
    return parser


def main():
    parser = _build_parse_args()
    args = parser.parse_args()
    if args.version:
        print('%s %s' % (__file__, VERSION))
        parser.exit()
    run(args.terraform_state, args.output)
    parser.exit()


if __name__ == '__main__':
    main()
