from udsoncan import services
from udsoncan.exceptions import *
from udsoncan import Request, Response

from test.ClientServerTest import ClientServerTest
import time

class TestClient(ClientServerTest):
    def __init__(self, *args, **kwargs):
        ClientServerTest.__init__(self, *args, **kwargs)

    def test_timeout_override(self):
        pass

    def _test_timeout_override(self):
        req = Request(service = services.TesterPresent, subfunction=0) 
        timeout = 0.5
        try:
            t1 = time.time()
            response = self.udsclient.send_request(req, timeout=timeout)
            raise Exception('Request did not raise a TimeoutException')
        except TimeoutException as e:
            diff = time.time() - t1
            self.assertGreater(diff, timeout, 'Timeout raised after %.3f seconds when it should be %.3f sec' % (diff, timeout))
            self.assertLess(diff, timeout+0.5, 'Timeout raised after %.3f seconds when it should be %.3f sec' % (diff, timeout))

    # Server does not respond. Overall timeout is set smaller than P2 timeout. Overall timeout should trig
    def test_no_response_overall_timeout(self):
        pass

    def _test_no_response_overall_timeout(self):
        req = Request(service = services.TesterPresent, subfunction=0) 
        timeout = 0.5
        self.udsclient.set_configs({'request_timeout': timeout, 'p2_timeout' : 2, 'p2_star_timeout':2})
        try:
            t1 = time.time()
            response = self.udsclient.send_request(req)
            raise Exception('Request did not raise a TimeoutException')
        except TimeoutException as e:
            diff = time.time() - t1
            self.assertGreater(diff, timeout, 'Timeout raised after %.3f seconds when it should be %.3f sec' % (diff, timeout))
            self.assertLess(diff, timeout+0.5, 'Timeout raised after %.3f seconds when it should be %.3f sec' % (diff, timeout))

    # Server does not respond. P2 timeout is smaller than overall timeout. P2 timeout should trig
    def test_no_response_p2_timeout(self):
        pass

    def _test_no_response_p2_timeout(self):
        req = Request(service = services.TesterPresent, subfunction=0) 
        timeout = 0.5
        self.udsclient.set_configs({'request_timeout': 2, 'p2_timeout' : timeout, 'p2_star_timeout':2})
        try:
            t1 = time.time()
            response = self.udsclient.send_request(req)
            raise Exception('Request did not raise a TimeoutException')
        except TimeoutException as e:
            diff = time.time() - t1
            self.assertGreater(diff, timeout, 'Timeout raised after %.3f seconds when it should be %.3f sec' % (diff, timeout))
            self.assertLess(diff, timeout+0.5, 'Timeout raised after %.3f seconds when it should be %.3f sec' % (diff, timeout))

    #  overall timeout is set to 0.5. Server respond "pendingResponse" for 1 sec. Client should timeout first.
    def test_overall_timeout_pending_response(self):
        if not hasattr(self, 'completed'):
            self.completed = False
        self.conn.touserqueue.get(timeout=0.2)
        response = Response(service=services.TesterPresent, code=Response.Code.RequestCorrectlyReceived_ResponsePending)
        t1 = time.time()
        while time.time() - t1 < 1 and not self.completed:
            self.conn.fromuserqueue.put(response.get_payload())
            time.sleep(0.1)

    def _test_overall_timeout_pending_response(self):
        req = Request(service = services.TesterPresent, subfunction=0) 
        timeout = 0.5
        self.udsclient.set_configs({'request_timeout': timeout, 'p2_timeout' : 2, 'p2_star_timeout':2})
        try:
            t1 = time.time()
            response = self.udsclient.send_request(req)
            raise Exception('Request did not raise a TimeoutException')
        except TimeoutException as e:
            self.assertIsNotNone(self.udsclient.last_response, 'Client never received the PendingResponse message')
            self.completed = True
            diff = time.time() - t1
            self.assertGreater(diff, timeout, 'Timeout raised after %.3f seconds when it should be %.3f sec' % (diff, timeout))
            self.assertLess(diff, timeout+0.5, 'Timeout raised after %.3f seconds when it should be %.3f sec' % (diff, timeout))

    #  Sends 2 "pending response" response to switch to P2* timeout.
    def test_p2_star_timeout(self):
        self.conn.touserqueue.get(timeout=0.2)
        response = Response(service=services.TesterPresent, code=Response.Code.RequestCorrectlyReceived_ResponsePending)
        self.conn.fromuserqueue.put(response.get_payload())
        time.sleep(0.1)
        self.conn.fromuserqueue.put(response.get_payload())

    def _test_p2_star_timeout(self):
        req = Request(service = services.TesterPresent, subfunction=0) 
        timeout = 2
        self.udsclient.set_configs({'request_timeout': 5, 'p2_timeout' : 0.5, 'p2_star_timeout':timeout})
        try:
            t1 = time.time()
            response = self.udsclient.send_request(req)
            raise Exception('Request did not raise a TimeoutException')
        except TimeoutException as e:
            self.assertIsNotNone(self.udsclient.last_response, 'Client never received the PendingResponse message')
            self.completed = True
            diff = time.time() - t1
            self.assertGreater(diff, timeout, 'Timeout raised after %.3f seconds when it should be %.3f sec' % (diff, timeout))
            self.assertLess(diff, timeout+0.5, 'Timeout raised after %.3f seconds when it should be %.3f sec' % (diff, timeout))

    #  Sends 2 "pending response" response to switch to P2* timeout.
    def test_p2_star_timeout_overrided_by_diagnostic_session_control(self):
        self.conn.touserqueue.get(timeout=0.2)
        self.conn.fromuserqueue.put(b"\x50\x01\x03\xE8\x00\xC8")  # Respond to diagnostic session control with timeout of 2 sec
        
        response = Response(service=services.TesterPresent, code=Response.Code.RequestCorrectlyReceived_ResponsePending)
        self.conn.fromuserqueue.put(response.get_payload())
        time.sleep(0.1)
        self.conn.fromuserqueue.put(response.get_payload())

    def _test_p2_star_timeout_overrided_by_diagnostic_session_control(self):
        req = Request(service = services.TesterPresent, subfunction=0) 
        self.udsclient.set_configs({'request_timeout': 5, 'p2_timeout' : 0.5, 'p2_star_timeout':1})
        self.udsclient.change_session(1)
        timeout = 2
        try:
            t1 = time.time()
            response = self.udsclient.send_request(req)
            raise Exception('Request did not raise a TimeoutException')
        except TimeoutException as e:
            self.assertIsNotNone(self.udsclient.last_response, 'Client never received the PendingResponse message')
            self.completed = True
            diff = time.time() - t1
            self.assertGreater(diff, timeout, 'Timeout raised after %.3f seconds when it should be %.3f sec' % (diff, timeout))
            self.assertLess(diff, timeout+0.5, 'Timeout raised after %.3f seconds when it should be %.3f sec' % (diff, timeout))

    def test_payload_override_literal(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b'\x12\x34\x56\x78')
        self.conn.fromuserqueue.put(b"\x7E\x00")

    def _test_payload_override_literal(self):
        req = Request(service = services.TesterPresent, subfunction=0) 
        with self.udsclient.payload_override(b'\x12\x34\x56\x78'):
            response = self.udsclient.send_request(req)
            self.assertEqual(response.original_payload, b'\x7E\x00')


    def test_payload_override_func(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b'\x99\x88\x77\x66')
        self.conn.fromuserqueue.put(b"\x7E\x00")

    def _test_payload_override_func(self):
        def func(payload):
            return b'\x99\x88\x77\x66'

        req = Request(service = services.TesterPresent, subfunction=0) 
        with self.udsclient.payload_override(func):
            response = self.udsclient.send_request(req)
            self.assertEqual(response.original_payload, b'\x7E\x00')