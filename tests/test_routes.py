"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    def test_get_account_list(self):
        """It should Get a list of Accounts"""
        self._create_accounts(3)
        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 3)

    def test_read_an_account(self):
        """It should Read a single Account"""
        account = self._create_accounts(1)[0]
        # make a call to self.client.get() to read the account
        resp = self.client.get(
            f"{BASE_URL}/{account.id}", content_type="application/json"
        )
        # assert that the resp.status_code is status.HTTP_200_OK
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # get the data from resp.get_json()
        data = resp.get_json()
        # assert that data["name"] equals the account.name
        self.assertEqual(data["name"], account.name)
        self.assertEqual(data["email"], account.email)
        self.assertEqual(data["address"], account.address)
        self.assertEqual(data["phone_number"], account.phone_number)
        self.assertEqual(data["date_joined"], str(account.date_joined))

    def test_account_not_found(self):
        """It should not Read an Account that is not found"""
        account = self._create_accounts(1)[0]
        # make a call to self.client.get() to read the account
        resp = self.client.get(
            f"{BASE_URL}/{account.id}", content_type="application/json"
        )
        # sad path: wrong id
        resp = self.client.get(
            f"{BASE_URL}/{account.id+1}", content_type="application/json"
        )
        # assert that the resp.status_code is status.HTTP_404_NOT_FOUND
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


    def test_delete_account(self):
        """It should Delete an Account"""
        account = self._create_accounts(1)[0]
        # send a self.client.delete() request to the BASE_URL with an id of an account
        resp = self.client.delete(f"{BASE_URL}/{account.id}")
        # assert that the resp.status_code is status.HTTP_204_NO_CONTENT
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        
        # sad path: wrong id
        resp = self.client.delete(f"{BASE_URL}/{account.id+1}")
        # assert that the resp.status_code is status.HTTP_404_NOT_FOUND
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

 
    def test_update_account(self):
        """It should Update an existing Account"""
        # create an Account to update
        test_account = AccountFactory()
        # send a self.client.post() request to the BASE_URL with a json payload of test_account.serialize()
        response = self.client.post(
            BASE_URL,
            json=test_account.serialize(),
        )
        # assert that the resp.status_code is status.HTTP_201_CREATED
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update the account
        
        # get the data from resp.get_json() as new_account
        new_account = response.get_json()
        # change new_account["name"] to something known
        new_account["email"] = "foo@email.it"

        # send a self.client.put() request to the BASE_URL with a json payload of new_account
        response = self.client.put(
            f"{BASE_URL}/{new_account['id']}",
            json=new_account
        )
        # assert that the resp.status_code is status.HTTP_200_OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # get the data from resp.get_json() as updated_account
        updated_account = response.get_json()
        # assert that the updated_account["name"] is whatever you changed it to
        self.assertEqual(updated_account["email"], "foo@email.it")


    def test_method_not_allowed(self):
        """It should not allow an illegal method call"""
        # call self.client.delete() on the BASE_URL
        response = self.client.delete(BASE_URL)
        # assert that the resp.status_code is status.HTTP_405_METHOD_NOT_ALLOWED
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        