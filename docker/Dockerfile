
# Copyright 2018-2020 CRS4 (http://www.crs4.it/)
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
ARG base_kubespray_version="2.12.5"

COPY ssh_config /etc/ssh/
WORKDIR /tmp
ENV DEFAULT_KUBESPRAY_VERSION=${base_kubespray_version}
ENV KUBESPRAY_DIR=/kubespray
ENV INVENTORY_DIR=/inventory-dir

RUN apk update \
  && apk add --no-cache \
        bash \
        git \
        jq \
        py3-pip \
        python3 \
  && pip3 install --no-cache-dir --upgrade pip \
  && pip3 install --no-cache-dir 'GitPython==3.1' \
  && rm -rf /var/lib/{cache,log}/ /tmp/* /var/tmp/* /root/.[^.]* /root/*

RUN git clone --depth 1 --single-branch --branch "v${DEFAULT_KUBESPRAY_VERSION}" https://github.com/${git_repo} ${KUBESPRAY_DIR} \
 && cd ${KUBESPRAY_DIR} \
 && git fetch --tags \
 && git checkout "v${DEFAULT_KUBESPRAY_VERSION}"

COPY kubespray_patches /home/manageks/kubespray_patches
# Apply a patch to kubespray if we have one.  The operation is rather
# contrived because we want any error in `git apply` to rise to the RUN
RUN \
  set -x && \
  cd "${KUBESPRAY_DIR}" \
  && if [[ -f /home/manageks/kubespray_patches/v${DEFAULT_KUBESPRAY_VERSION}.patch ]]; then \
        git apply /home/manageks/kubespray_patches/v${DEFAULT_KUBESPRAY_VERSION}.patch ; \
     fi \
  && find "${KUBESPRAY_DIR}" -print0 | xargs -0 chmod a+w
# We make the repository world writable so that all users can change the checked out
# kubespray version

RUN cat "${KUBESPRAY_DIR}/requirements.txt"

RUN apk update \
  && apk add --no-cache --virtual .build-deps \
         gcc \
         libc-dev \
         libffi-dev \
         make \
         openssl-dev \
         python3-dev \
  && pip3 install --no-cache-dir -r "${KUBESPRAY_DIR}/requirements.txt" \
  && apk del --purge .build-deps \
  && rm -rf /var/lib/{cache,log}/ /tmp/* /var/tmp/* /root/.[^.]* /root/*


COPY terraform_openstack_templates /home/manageks/terraform_openstack_templates
COPY config-cluster /home/manageks/config-cluster
RUN mkdir ${INVENTORY_DIR} \
 && find /home "${KUBESPRAY_DIR}" -type d -print0 | xargs -0 chmod a+rx \
 && find /home "${KUBESPRAY_DIR}" -type f -print0 | xargs -0 chmod a+r

COPY create_inventory.py manage-cluster.py /usr/local/bin/
RUN chmod a+rx /usr/local/bin/create_inventory.py /usr/local/bin/manage-cluster.py

#####################################
FROM manage-cluster-base AS manage-cluster-tf

# USER -> this image is run as the local system user by the manage-cluster script

WORKDIR ${INVENTORY_DIR}/cluster
ENTRYPOINT []


#####################################
FROM manage-cluster-base AS manage-cluster-ks

ENV ANSIBLE_LOCAL_TEMP=/tmp
RUN mkdir -p /etc/ansible && ln -s ${KUBESPRAY_DIR}/roles /etc/ansible/roles

# must run as root...haven't been able to make it work otherwise
USER root
WORKDIR /root/

ENTRYPOINT []

