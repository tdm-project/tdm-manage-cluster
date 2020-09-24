
# manage-cluster

A simple utility to help deploy Kubernetes clusters with Terraform and KubeSpray.

## Helm version

Starting from version 1.8, `manage-cluster` supports only **Helm version 3**. In order to work with Helm version 2 please refer to branch *helm-2* of this repository.

## Requirements

* Docker
* Bash version >= 4.3
* ssh
* Access to an OpenStack cloud

## Installation
Copy the `manage-cluster` script to your system.

`manage-cluster` uses some Docker containers, but these will be automatically
fetched from Dockerhub. If you want to build your own copies of the containers,
then clone the repository and run `docker/build.sh`.


## Usage

First, source the RC file for your OpenStack installation.  If you don't have
one yet,

1. Go to your OpenStack Dashboard
2. Navigate to ‚Project > API Access‘
3. Click the button ‚Download OpenStack RC file‘

`manage-cluster` doesn't yet support `clouds.yaml`.


Then,

    manage-cluster template mycluster-dir
    cd mycluster-dir # the '.' in the next commands refers to this directory

Edit `tf/cluster.tf` to set the terraform parameters you need.  After that

    manage-cluster deploy .           # This runs terraform to provision the infrastructure
    manage-cluster deploy-k8s .       # This runs kubespray to deploy Kubernetes
    manage-cluster config-cluster .   # This runs the ansible playbook ./config-cluster-playbook.yml
    manage-cluster config-client .    # This generates the kubeconfig file

At the end of the deployment procedure, follow the instructions on screen to
access you Kubernetes cluster.


To destroy the cluster:

    manage-cluster destroy .


## Other instructions

For additional functionality see the output from `manage-cluster -h`:
```
  Usage of 'manage-cluster'

  manage-cluster <COMMAND> <CLUSTER_DIR>
  manage-cluster -h        prints this help message
  manage-cluster -v        prints the 'manage-cluster' version

  COMMAND:
    template    [ks version]   creates a template cluster configuration directory
    deploy                     creates virtual machines
    deploy-k8s  [ks version]   deploys kubernetes
    config-cluster             run ansible playbook to configure the kubernetes cluster. The default
                               playbook contains CRS4-specific customizations.
    upgrade-k8s [ks version]   upgrade the version of Kubernetes installed on a cluster.
    destroy                    destroys virtual machines
    config-client              configures kubectl
    get-master-ips             prints out master IPs for the cluster, one per line (cluster must be deployed)
    shell       [ks version]   opens a shell for the current cluster in the manage-cluster container
    list-ks-versions           lists KubeSpray versions supported by this program.


  CLUSTER_DIR:
    Path to the directory containing the cluster's configuration
    (i.e., terraform files and artifacts)
```


For details about what manage-cluster does, check out
https://github.com/kubernetes-incubator/kubespray/tree/master/contrib/terraform/openstack


## Copyright and License

Copyright 2018-2020 CRS4 (http://www.crs4.it/)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Authors and contributors

* Marco Enrico Piras (`marcoenrico.piras <at> crs4.it`)
* Mauro del Rio (`mauro.delrio <at> crs4.it`)
* Luca Pireddu (`luca.pireddu <at> crs4.it`)
* Massimo Gaggero (`massimo.gaggero <at> crs4.it`)

