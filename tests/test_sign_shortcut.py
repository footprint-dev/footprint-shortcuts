import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from sign_shortcut import sign_shortcut


class SigningTests(unittest.TestCase):
    def test_forbidden_response_reports_server_details_and_preserves_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "unsigned.shortcut"
            destination = Path(directory) / "Footprint 提交当前位置.shortcut"
            source.write_bytes(b"unsigned workflow")
            destination.write_bytes(b"existing signed shortcut")
            error = HTTPError(
                "https://sign.shortcuty.app/api/v1/sign",
                403,
                "Forbidden",
                {"Content-Type": "text/html", "CF-Ray": "test-request-id"},
                io.BytesIO(b"Access denied by the signing service"),
            )

            with patch("sign_shortcut.urlopen", side_effect=error):
                with self.assertRaises(RuntimeError) as raised:
                    sign_shortcut(source, destination)

            message = str(raised.exception)
            self.assertIn("HTTP 403", message)
            self.assertIn("text/html", message)
            self.assertIn("test-request-id", message)
            self.assertIn("Access denied by the signing service", message)
            self.assertEqual(destination.read_bytes(), b"existing signed shortcut")
