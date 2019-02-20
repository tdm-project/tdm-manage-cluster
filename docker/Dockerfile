
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

FROM hashicorp/terraform:0.11.11 AS manage-cluster-base

# KubeSpray repo and version
ARG git_repo=kubernetes-sigs/kubespray.git
ARG kubespray_version="v2.8.2"

LABEL kubespray_version="${kubespray_version}"

COPY ssh_config /etc/ssh/
COPY requirements.txt /root/manage-cluster-py-requirements.txt

RUN apk update && \
  apk add --no-cache --virtual .build-deps python2-dev gcc libc-dev libffi-dev openssl-dev make && \
  apk add --no-cache jq git python2 py2-pip bash && \
  pip install --no-cache-dir --upgrade pip && \
  pip install -r /root/manage-cluster-py-requirements.txt  && \
  apk del --purge .build-deps && \
  rm -rf /var/lib/{cache,log}/ /tmp/* /var/tmp/* /root/.[^.]* /root/*

WORKDIR /tmp
ENV KUBESPRAY_DIR=/kubespray

RUN git clone --depth 1 --single-branch --branch "${kubespray_version}" https://github.com/${git_repo} ${KUBESPRAY_DIR} \
 && cd ${KUBESPRAY_DIR} \
 && sed -i \
        -e 's|\<contrib/terraform/openstack/ansible_bastion_template.txt\>|../../contrib/terraform/openstack/ansible_bastion_template.txt|g' \
        -e "s|\<contrib/terraform/group_vars/no-floating.yml\>|${KUBESPRAY_DIR}/inventory/cluster/group_vars/no-floating.yml|g" \
        contrib/terraform/openstack/modules/compute/main.tf \
 && rm -rf .git \
 && find . -type d -print0 | xargs -0 chmod a+rwx \
 && find . -type f -print0 | xargs -0 chmod a+rw

COPY playbooks /home/manageks/playbooks
COPY create_inventory.py /usr/local/bin/
RUN chmod a+rx /usr/local/bin/create_inventory.py \
    && chmod a+rx /home /home/manageks /home/manageks/playbooks \
    && chmod a+r  /home/manageks/playbooks/*

#####################################
FROM manage-cluster-base AS manage-cluster-tf

# USER -> this image is run as the local system user by the manage-cluster script

WORKDIR ${KUBESPRAY_DIR}/inventory/cluster
ENTRYPOINT []


#####################################
FROM manage-cluster-base AS manage-cluster-ks

ENV ANSIBLE_LOCAL_TEMP=/tmp

# must run as root...haven't been able to make it work otherwise
USER root
WORKDIR /root/

ENTRYPOINT []
