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

import factory
from users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    """
    A factory class for creating User instances with predefined attributes using the
    factory_boy library.
    """

    username = factory.Sequence(lambda n: f'user{n}')
    password = factory.Faker('password')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')

    class Meta:
        """
        Meta class to specify the model associated with the UserFactory, which is the
        User model.
        """

        model = User
