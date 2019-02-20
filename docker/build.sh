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


set -o nounset
set -o errexit
set -o pipefail

ThisDir=$( cd "$( dirname "${0}" )" >/dev/null && pwd )

function usage_error() {
  echo "Usage: $0 [tag]" >&2
  exit 2
}

#### main ####
cd "${ThisDir}"
if [[ $# == 0 ]]; then
  Tag=":$(../k8s-tools/manage-cluster -v)"
elif [[ $# == 1 ]]; then
  Tag=":${1}"
else
  usage_error
fi

for target in manage-cluster-tf manage-cluster-ks; do
  docker build --target=${target} -t tdm-project/${target}${Tag} .
done

