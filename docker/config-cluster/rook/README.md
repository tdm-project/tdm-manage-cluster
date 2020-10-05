
# Deploying Rook with Ceph

These deployment declarations deploy the Rook Ceph operator on your Kubernetes
cluster.  Everything is based on the Rook Ceph documentation:

  https://rook.io/docs/rook/v1.4/ceph-storage.html

The deployment enables the Ceph block storage and the CephFS shared file system
(along with the relevent k8s storage provisioner).

It also partially configures Ceph object storage, but that part isn't complete
and we don't have a working configuration.

The dashboard is also enabled (https access) and accessible through a NodePort
service.  Check the service created in the `rook-ceph` namespace.

The specifics of the deployment are not documented here in the interest of
avoiding having to worry about keeping this document in sync with any possible
changes

## Requirements

  * Kubernetes version >= 1.14

