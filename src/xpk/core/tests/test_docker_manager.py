"""
Copyright 2024 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import docker.errors
from ..docker_manager import CtkDockerManager
import docker
import pytest
import os

dockerfile_path = 'data/Dockerfile'
test_cfg_path = '/tmp/xpk_gcloud_cfg'
test_deployment_dir = '/tmp/xpk_deployment'
test_gcluster_cmd = 'gcluster --version'
test_ctk_xpk_img = 'gcluster-xpk-test'
test_ctk_xpk_container = 'gcluster-xpk-test-container'


def remove_img():
  dc = docker.from_env()
  try:
    dc.images.remove(test_ctk_xpk_img, force=True)
  except docker.errors.APIError as _:
    pass


def remove_container():
  dc = docker.from_env()
  try:
    container = dc.containers.get(test_ctk_xpk_container)
    container.remove(force=True)
  except docker.errors.APIError as _:
    pass


def create_tmp_dirs():
  os.mkdir(test_cfg_path)
  os.mkdir(test_deployment_dir)


def remove_tmp_dirs():
  os.removedirs(test_cfg_path)
  os.removedirs(test_deployment_dir)


@pytest.fixture(name='setup_img_name')
def remove_test_ctk_img():
  create_tmp_dirs()
  remove_container()
  remove_img()
  yield test_ctk_xpk_img
  remove_container()
  remove_img()
  remove_tmp_dirs()


def test_docker_build_image(setup_img_name):
  dm = CtkDockerManager(
      dockerfile_path=dockerfile_path,
      gcloud_cfg_path=test_cfg_path,
      deployment_dir=test_deployment_dir,
  )
  dc = docker.from_env()
  containers_before = dc.containers.list(all=True)
  dm.build_image(setup_img_name)
  dc.images.get(setup_img_name)
  containers_after = dc.containers.list(all=True)
  assert len(containers_before) == len(containers_after)


def test_run_command(setup_img_name):

  dm = CtkDockerManager(
      dockerfile_path=dockerfile_path,
      gcloud_cfg_path=test_cfg_path,
      deployment_dir=test_deployment_dir,
  )
  dc = docker.from_env()

  containers_before = dc.containers.list(all=True)

  dm.build_image(setup_img_name)
  output = dm.run_command(
      setup_img_name,
      test_gcluster_cmd,
      rm_container_after=False,
      container_name=test_ctk_xpk_container,
  )

  containers_after = dc.containers.list(all=True)

  assert len(containers_after) - len(containers_before) == 1

  assert len(output) != 0
  assert "Built from 'main' branch" in str(output)
