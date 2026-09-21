"""HTTP client for MagangHub Monev API."""

import requests

TIMEOUT = 30


class ApiError(Exception):
    """API error with HTTP status code."""

    def __init__(self, status_code: int, message: str):
        """Initialize with a status code and message.

        Args:
            status_code: HTTP status code.
            message: Error message.
        """
        self.status_code = status_code
        super().__init__(f"API {status_code}: {message}")


class ApiClient:
    """HTTP client with Bearer token authentication."""

    def __init__(self, token: str, base_url: str = ""):
        """Initialize client with an access token.

        Args:
            token: Bearer access token.
            base_url: API base URL. Defaults to settings value.
        """
        from app.config import settings
        self.base_url = base_url or settings.api_base
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        })

    def get(self, path: str, params: dict | None = None) -> dict:
        """Send a GET request.

        Args:
            path: Endpoint path.
            params: Query parameters.

        Returns:
            JSON response body.
        """
        r = self.session.get(f"{self.base_url}{path}", params=params, timeout=TIMEOUT)
        return self._handle(r)

    def post(self, path: str, data: dict) -> dict:
        """Send a POST request.

        Args:
            path: Endpoint path.
            data: JSON payload.

        Returns:
            JSON response body.
        """
        r = self.session.post(f"{self.base_url}{path}", json=data, timeout=TIMEOUT)
        return self._handle(r)

    def _handle(self, r: requests.Response) -> dict:
        """Process an HTTP response.

        Args:
            r: Response from requests.

        Returns:
            JSON body.

        Raises:
            Exception: If status code is not 2xx.
        """
        try:
            body = r.json()
        except ValueError:
            body = {"raw": r.text}

        if not r.ok:
            raise ApiError(r.status_code, body.get("message", r.text[:200]))

        return body
