from typing import Any, Dict
from enum import Enum
from flask import jsonify
from flask_api.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

OK, FAIL = 0, 1


class Response(Enum):
    SUCCESS = (HTTP_200_OK, "Success.")
    FAILURE = (HTTP_400_BAD_REQUEST, "Failure.")
    INPUT_NOT_VALID = (HTTP_400_BAD_REQUEST, "Input data not valid.")
    BOOKMARK_NOT_FOUND = (HTTP_404_NOT_FOUND, "Bookmark not found.")
    TAG_NOT_FOUND = (HTTP_404_NOT_FOUND, "Tag not found.")
    RANGE_NOT_VALID = (HTTP_400_BAD_REQUEST, "Range not valid.")
    TAG_NOT_VALID = (HTTP_400_BAD_REQUEST, "Invalid tag.")

    @staticmethod
    def bad_request(message: str):
        json = {'status': Response.FAILURE.status, 'message': message}
        return (jsonify(json), Response.FAILURE.status_code, {'ContentType': 'application/json'})

    @staticmethod
    def from_flag(flag: bool):
        return Response.SUCCESS() if flag else Response.FAILURE()

    @property
    def status_code(self) -> int:
        return self.value[0]

    @property
    def message(self) -> str:
        return self.value[1]

    @property
    def status(self) -> int:
        return OK if self.status_code == HTTP_200_OK else FAIL

    def json(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        return dict(status=self.status, message=self.message, **data or {})  # pylint: disable=R1735

    def __call__(self, *, data: Dict[str, Any] = None):
        """Generates a tuple in the form (response, status, headers)

        If passed, data is added to the response's JSON.
        """

        return (jsonify(self.json(data)), self.status_code, {'ContentType': 'application/json'})
