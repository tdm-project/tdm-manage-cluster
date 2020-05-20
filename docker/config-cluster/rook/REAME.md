
# Deploying Rook with Ceph

These deployment declarations deploy the Rook Ceph operator on your Kubernetes
cluster.  Everything is based on the Rook Ceph documentation:

  https://rook.io/docs/rook/v1.3/ceph-storage.html

The deployment enables the Ceph block storage, Ceph bucket storage and the
CephFS shared file system (along with the relevent k8s storage provisioner).

The user authentication for the bucket storage isn't configured correctly and
needs to be fixed.

The dashboard is also enabled (https access) and accessible through a NodePort
service.  Check the service created in the `rook-ceph` namespace.

The specifics of the deployment are not documented here in the interest of
avoiding having to worry about keeping this document in sync with any possible
changes

## Requirements

  * Kubernetes version >= 1.14

