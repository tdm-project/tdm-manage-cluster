#!/bin/bash
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

set -o errexit
set -o pipefail


ThisDir=$( cd "$( dirname "${0}" )" >/dev/null && pwd )

function usage_error() {
  echo "set DOCKER_USERNAME and DOCKER_PASSWORD to login on DockerHub" >&2
  echo -e "\nUsage: $0" >&2
  exit 2
}

# print help
if [[ $# == 1 ]] && [[ ${1} == "--help" ]]; then
  usage_error
fi

if [[ -z ${DOCKER_USERNAME} || -z ${DOCKER_PASSWORD} ]]; then
  usage_error
fi

cd "${ThisDir}"

# login to the DockerHub
echo -e "\nDockerHub login..." >&2
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

# get manage-cluster version to tag the image
image_tag=$(../k8s-tools/manage-cluster -v)

# tag and push images
for target in manage-cluster-tf manage-cluster-ks; do
  docker_image_name="tdm-project/${target}:${image_tag}"
  tagged_docker_image="${DOCKER_USERNAME}/${target}:${image_tag}"
  docker tag "${docker_image_name}" "${tagged_docker_image}"
  echo -e "\nPushing ${tagged_docker_image}..." >&2
  docker push ${tagged_docker_image}
done