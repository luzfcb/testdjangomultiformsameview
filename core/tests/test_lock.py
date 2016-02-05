from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory

from ..models import Pessoa, DocumentoLock
from ..views import PessoaCreate

class LockTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user1_data = {
            'username': 'admin',
            'email': 'admin@admin.com',
            'password': 'admin',
            'first_name': 'Admin',
            'last_name': 'Root'
        }
        self.user2_data = {
            'username': 'maria',
            'email': 'maria@maria.com',
            'password': 'maria',
            'first_name': 'Maria',
            'last_name': 'Neo Matrix'
        }

        self.user1 = User.objects.create_superuser(**self.user1_data)
        self.user2 = User.objects.create_superuser(**self.user2_data)



    def test_lock(self):
        """
        Test lock logic
        """
        assert True
