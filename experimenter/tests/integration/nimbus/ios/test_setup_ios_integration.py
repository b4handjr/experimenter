import json
import logging
import time
from pathlib import Path

import pytest
import requests
from nimbus.models.base_dataclass import BaseExperimentApplications
from nimbus.pages.experimenter.summary import SummaryPage
from nimbus.utils import helpers


@pytest.fixture
def experiment_slug():
    return "firefox-ios-integration-test"


@pytest.fixture
def default_data_api(application):
    feature_config_id = helpers.get_feature_id_as_string(
        "messaging", BaseExperimentApplications.FIREFOX_IOS.value
    )
    return {
        "hypothesis": "Test Hypothesis",
        "application": application,
        "changelogMessage": "test updates",
        "targetingConfigSlug": "no_targeting",
        "publicDescription": "Some sort of Fancy Words",
        "riskRevenue": False,
        "riskPartnerRelated": False,
        "riskBrand": False,
        "riskMessage": False,
        "featureConfigIds": [int(feature_config_id)],
        "referenceBranch": {
            "description": "reference branch",
            "name": "control",
            "ratio": 50,
            "featureValues": [
                {
                    "featureConfig": str(feature_config_id),
                    "value": "{}",
                },
            ],
        },
        "treatmentBranches": [],
        "populationPercent": "100",
        "totalEnrolledClients": 55,
        "firefoxMinVersion": "FIREFOX_120",
    }


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
    time.sleep(10)
    recipe = requests.get(
        f"https://nginx/api/v6/experiments/{experiment_slug}/", verify=False
    ).json()
    path = Path.cwd()
    json_file = path / "experimenter" / "tests" / "integration" / "ios_recipe.json"
    json_file.write_text(json.dumps(recipe))
    logging.info(f"ios recipe created at {json_file}")
