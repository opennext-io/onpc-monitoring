#!/usr/bin/env bash
# Copyright 2018, OpenNext SAS.
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


set -xe
PATH=/sbin:/usr/sbin:/bin:/usr/bin
TICKSCRIPTS_DIR="/usr/local/etc/kapacitor/tick/script"
TASKS=$(kapacitor list tasks | sed 's/\|/ /'|awk '{print $1}')

case "$1" in
  create)
    for i in $(find $TICKSCRIPTS_DIR -type f -name "*.tick"); do
      echo $i
      IFS='.' read -ra NAMES <<< "$i"
      IFS='/' read -ra NAMES <<< "${NAMES[-2]}"
      if [[ $i == *"batch"* ]]; then
          kapacitor define ${NAMES[-1]} -type batch -tick $i
      else
          kapacitor define ${NAMES[-1]} -type stream -tick $i
      fi
    done
    ;;
  enable | disable | reload)
    for var in "${TASKS[@]}"; do
      kapacitor $1 ${var}
    done
    ;;
  delete)
    for var in "${TASKS[@]}"; do
      kapacitor delete task ${var}
    done
    ;;
  *)
    echo "Usage: $SCRIPTNAME {create|delete|enable|disable|reload}" >&2
    exit 1
    ;;
esac


