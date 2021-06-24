import pytest
# from sheets import SheetsApi


# TODO - This needs tests!
@pytest.fixture(scope='module')
def client():
    return None
    # return SheetsApi(credentials_json)


@pytest.mark.usefixtures('client')
class TestClient(object):

    def test(self, client):
        # TODO!
        assert True
