import logging
import subprocess
import time

import pytest


@pytest.fixture
def experiment_slug():
    return "firefox-ios-integration-test"


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


@pytest.mark.ios
def test_experiment_unenrolls_after_studies_toggle(
    xcodebuild, setup_experiment, start_app
):
    xcodebuild.install(boot=False)
    xcodebuild.test(
        "XCUITests/ExperimentIntegrationTests/testAppStartup", build=False, erase=False
    )
    setup_experiment()
    time.sleep(5)
    xcodebuild.test(
        "XCUITests/ExperimentIntegrationTests/testVerifyExperimentEnrolled",
        build=False,
        erase=False,
    )
    start_app()
    xcodebuild.test(
        "XCUITests/ExperimentIntegrationTests/testStudiesToggleDisablesExperiment",
        build=False,
        erase=False,
    )
