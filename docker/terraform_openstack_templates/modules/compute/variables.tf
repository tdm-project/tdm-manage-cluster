variable "cluster_name" {}

variable "az_list" {
  type = "list"
}

variable "number_of_k8s_masters" {}

variable "number_of_k8s_masters_ext_net" {}

variable "number_of_k8s_masters_no_etcd" {}

variable "number_of_etcd" {}

variable "number_of_k8s_nodes_ext_net" {}

variable "number_of_k8s_data_nodes_ext_net" {}

variable "number_of_k8s_masters_no_floating_ip" {}

variable "number_of_k8s_masters_no_floating_ip_no_etcd" {}

variable "number_of_k8s_nodes" {}

variable "number_of_k8s_nodes_no_floating_ip" {}

variable "number_of_bastions" {}

variable "number_of_gfs_nodes_no_floating_ip" {}

variable "gfs_volume_size_in_gb" {}

variable "public_key_path" {}

variable "image" {}

variable "image_gfs" {}

variable "ssh_user" {}

variable "ssh_user_gfs" {}

variable "flavor_k8s_master" {}

variable "flavor_k8s_node" {}

variable "flavor_k8s_data_node" {}

variable "flavor_etcd" {}

variable "flavor_gfs_node" {}

variable "network_name" {}

variable "external_net" {}

variable "flavor_bastion" {}

variable "network_id" {
  default = ""
}

variable "k8s_master_fips" {
  type = "list"
}

variable "k8s_node_fips" {
  type = "list"
}

variable "bastion_fips" {
  type = "list"
}

variable "bastion_allowed_remote_ips" {
  type = "list"
}

variable "supplementary_master_groups" {
  default = ""
}

variable "supplementary_node_groups" {
  default = ""
}

variable "worker_allowed_ports" {
  type = "list"
}

variable "master_vm_scheduler_policy" {
  default = "soft-anti-affinity"
}

variable "node_vm_scheduler_policy" {
  default = "soft-anti-affinity"
}