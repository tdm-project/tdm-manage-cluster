
# manage-cluster

A simple utility to help deploy Kubernetes clusters with Terraform and KubeSpray.

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

    manage-cluster deploy .  # This runs terraform to provision the infrastructure
    manage-cluster deploy-k8s .  # This runs kubespray to deploy Kubernetes

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
    template     creates a template cluster configuration directory
    deploy       creates virtual machines
    deploy-k8s   deploys kubernetes
    destroy      destroys virtual machines
    config       configures kubectl
    shell        opens a shell in the manage-cluster container

  CLUSTER_DIR:
    Path to the directory containing the cluster's configuration
    (i.e., terraform files and artifacts)
```


For details about what manage-cluster does, check out
https://github.com/kubernetes-incubator/kubespray/tree/master/contrib/terraform/openstack


## Troubleshooting

### Helm

When using Helm for the first time, the following error can occur:
```
Error: configmaps is forbidden: User "system:serviceaccount:kube-system:default" cannot list configmaps in the namespace "kube-system"
```

In order to fix it type:

```
kubectl create serviceaccount --namespace kube-system tiller
kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller
kubectl patch deploy --namespace kube-system tiller-deploy -p '{"spec":{"template":{"spec":{"serviceAccount":"tiller"}}}}'
helm init --service-account tiller --upgrade
```
(ref: https://stackoverflow.com/questions/46672523/helm-list-cannot-list-configmaps-in-the-namespace-kube-system)

### Pods stuck in pending state

Pods whose definition includes volumes might get stuck in pending state if a (specific or, at least, default) StorageClass has not been defined on the Kubernetes cluster. To define a StorageClass which relies on Cinder (the OpenStack Block Storage service) type:

```
kubectl create -f storageclass.yaml
```


Another solution is to enable persistent volumes by default, editing the <CLUSTER-CONFIG-DIR>/tf/group_vars/k8s-cluster/k8s-cluster.yml KubeSpray config file:

```

# Add Persistent Volumes Storage Class for corresponding cloud provider ( OpenStack is only supported now )
 persistent_volumes_enabled: true

```

## Copyright and License

Copyright 2018-2019 CRS4 (http://www.crs4.it/)

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

* Marco Enrico Piras (marcoenrico.piras <at> crs4)
* Mauro del Rio (mauro.delrio <at> crs4)
* Luca Pireddu (luca.pireddu <at> crs4)
* Massimo Gaggero (massimo.gaggero <at> crs4)

