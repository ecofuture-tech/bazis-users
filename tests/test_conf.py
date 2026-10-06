# Copyright 2026 EcoFuture Technology Services LLC and contributors
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

import os
import subprocess
import sys

from bazis.contrib.users.conf import Settings


BARE_SETTINGS = """\
import bazis.core.configure  # noqa: F401

INSTALLED_APPS = []
"""

BARE_PROJECT_CHECK = """\
import django
django.setup()

from django.conf import settings

# the conf module of bazis-users is loaded (its own settings are present) ...
assert settings.BAZIS_AUTH_COOKIE_NAME == 'bazis_auth'
# ... but it does not bind the project to the users app
assert settings.AUTH_USER_MODEL == 'auth.User', settings.AUTH_USER_MODEL
"""


def test_conf_does_not_declare_django_model_settings():
    """
    The conf modules of all installed Bazis packages are loaded in every project, so
    bazis-users must not declare AUTH_USER_MODEL (the core does, with Django's default).
    """
    assert 'AUTH_USER_MODEL' not in Settings.model_fields
    assert 'AUTH_ANONYMOUS_USER_MODEL' in Settings.model_fields


def test_project_without_users_app_keeps_django_user_model(tmp_path):
    """
    A project that has bazis-users installed but does not use the users app must set up
    Django with the default user model (AUTH_USER_MODEL='users.User' made Django fail).
    """
    (tmp_path / 'bare_settings.py').write_text(BARE_SETTINGS)
    env = {
        key: value
        for key, value in os.environ.items()
        if key
        not in {
            'BS_INSTALLED_APPS',
            'BS_BAZIS_APPS',
            'BS_BAZIS_CONFIG_APPS',
            'BS_AUTH_USER_MODEL',
            'BS_AUTH_ANONYMOUS_USER_MODEL',
        }
    }
    env['DJANGO_SETTINGS_MODULE'] = 'bare_settings'
    env['PYTHONPATH'] = os.pathsep.join([str(tmp_path), *filter(None, [env.get('PYTHONPATH')])])
    # the working directory without project.env and .env: nothing but the environment is read
    result = subprocess.run(
        [sys.executable, '-c', BARE_PROJECT_CHECK],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
