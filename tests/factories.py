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
