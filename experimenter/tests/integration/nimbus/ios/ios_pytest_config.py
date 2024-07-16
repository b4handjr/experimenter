# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import os
import subprocess

from pathlib import Path

import pytest
from SyncIntegrationTests.xcodebuild import XCodeBuild
from SyncIntegrationTests.xcrun import XCRun

here = Path(__file__)


@pytest.fixture(name="nimbus_cli_args")
def fixture_nimbus_cli_args():
    return "FIREFOX_SKIP_INTRO FIREFOX_TEST DISABLE_ANIMATIONS 'GCDWEBSERVER_PORT:7777'"


@pytest.fixture()
def xcodebuild_log(request, tmp_path_factory):
    xcodebuild_log = tmp_path_factory.mktemp("logs") / "xcodebuild.log"
    logging.info(f"Logs stored at: {xcodebuild_log}")
    request.config._xcodebuild_log = xcodebuild_log
    yield xcodebuild_log


@pytest.fixture()
def xcodebuild(xcodebuild_log):
    yield XCodeBuild(
        xcodebuild_log, scheme="Fennec", test_plan="ExperimentIntegrationTests"
    )


@pytest.fixture(scope="session")
def xcrun():
    return XCRun()


@pytest.fixture(name="start_app")
def fixture_start_app(nimbus_cli_args):
    def _start_app():
        command = (
            f"nimbus-cli --app firefox_ios --channel developer open -- {nimbus_cli_args}"
        )
        out = subprocess.check_output(
            command,
            cwd=here.parent,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            shell=True,
        )
        logging.debug(out)

    return _start_app


@pytest.fixture
def experiment_slug():
    return "firefox-ios-integration-test"


@pytest.fixture(name="set_env_variables", autouse=True)
def fixture_set_env_variables(experiment_slug):
    """Set any env variables XCUITests might need"""
    os.environ["EXPERIMENT_NAME"] = experiment_slug


@pytest.fixture(name="setup_experiment")
def setup_experiment(experiment_slug, nimbus_cli_args):
    def _setup_experiment():
        logging.info(f"Testing experiment {experiment_slug}")
        command = [
            "nimbus-cli",
            "--app",
            "firefox_ios",
            "--channel",
            "developer",
            "enroll",
            f"{experiment_slug}",
            "--branch",
            "control",
            "--file",
            "/tmp/experimenter/tests/integration/ios_recipe.json",
            "--reset-app",
            "--",
            f"{nimbus_cli_args}",
        ]
        logging.info(f"Nimbus CLI Command: {' '.join(command)}")
        out = subprocess.check_output(
            " ".join(command),
            cwd=here.parent,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            shell=True,
        )
        logging.info(out)

    return _setup_experiment
