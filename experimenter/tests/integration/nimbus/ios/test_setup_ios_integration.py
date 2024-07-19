import json
import logging
import subprocess
import time
from pathlib import Path

import pytest
import requests
from nimbus.models.base_dataclass import BaseExperimentApplications
from nimbus.pages.experimenter.summary import SummaryPage
from nimbus.utils import helpers

here = Path(__file__)


@pytest.fixture
def experiment_slug():
    return "firefox-ios-integration-test2"


@pytest.fixture
def default_data_api(default_data_api):
    feature_config_id = helpers.get_feature_id_as_string(
        "messaging", BaseExperimentApplications.FIREFOX_IOS.value
    )
    test_data = {
        "featureConfigIds": [int(feature_config_id)],
        "referenceBranch": {
            "description": "reference branch",
            "name": "Branch 1",
            "ratio": 50,
            "featureValues": [
                {
                    "featureConfig": str(feature_config_id),
                    "value": "{}",
                },
            ],
        },
    }
    default_data_api.update(test_data)
    return default_data_api


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
def test_create_ios_experiment_for_integration_test(
    selenium, experiment_url, kinto_client, default_data_api, experiment_slug
):
    """Create an ios experiment for device integration tests"""
    helpers.create_experiment(
        experiment_slug, BaseExperimentApplications.FIREFOX_IOS.value, default_data_api
    )

    summary = SummaryPage(selenium, experiment_url).open()
    summary.launch_and_approve()

    kinto_client.approve()

    SummaryPage(selenium, experiment_url).open().wait_for_live_status()
    
    path = Path.cwd()
    timeout = time.time() + 30
    while time.time() < timeout:
        try:
            recipe = requests.get(
                f"https://nginx/api/v6/experiments/{experiment_slug}/", verify=False
            ).json()
        except Exception:
            continue
        else:
            json_file = (
                path / "experimenter" / "tests" / "integration" / "ios_recipe.json"
            )
            json_file.write_text(json.dumps(recipe))
            logging.info(f"ios recipe created at {json_file}")
            break


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
