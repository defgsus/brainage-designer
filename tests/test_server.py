from tests.base import BadTestCase
from tests.testserver import TestServer

# register these plugins
import bad.plugins.essential


class TestServerCase(BadTestCase):

    @BadTestCase.tag_server()
    def test_server(self):
        with TestServer() as server:
            data = server.GET("api/status/").json()
            self.assertEqual("bad-test-server", data["server"]["title"])
