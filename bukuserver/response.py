from typing import Any, Dict
from enum import Enum
from http import HTTPStatus
from flask import jsonify

OK, FAIL = 0, 1


class Response(Enum):
    SUCCESS = (HTTPStatus.OK, "Success.")                                # 200
    FAILURE = (HTTPStatus.BAD_REQUEST, "Failure.")                       # 400
    REMOVED = (HTTPStatus.GONE, "Functionality no longer available.")    # 410
    INPUT_NOT_VALID = (HTTPStatus.BAD_REQUEST, "Input data not valid.")  # 400
    BOOKMARK_NOT_FOUND = (HTTPStatus.NOT_FOUND, "Bookmark not found.")   # 404
    TAG_NOT_FOUND = (HTTPStatus.NOT_FOUND, "Tag not found.")             # 404
    RANGE_NOT_VALID = (HTTPStatus.BAD_REQUEST, "Range not valid.")       # 400
    TAG_NOT_VALID = (HTTPStatus.BAD_REQUEST, "Invalid tag.")             # 400

    @staticmethod
    def bad_request(message: str):
        json = {'status': Response.FAILURE.status, 'message': message}
        return (jsonify(json), Response.FAILURE.status_code, {'ContentType': 'application/json'})

    @staticmethod
    def from_flag(flag: bool):
        return Response.SUCCESS() if flag else Response.FAILURE()

    @property
    def status_code(self) -> int:
        return self.value[0].value

    @property
    def message(self) -> str:
        return self.value[1]

    @property
    def status(self) -> int:
        return OK if self.status_code == HTTPStatus.OK.value else FAIL

    def json(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        return dict(status=self.status, message=self.message, **data or {})  # pylint: disable=R1735

    def __call__(self, *, data: Dict[str, Any] = None):
        """Generates a tuple in the form (response, status, headers)

        If passed, data is added to the response's JSON.
        """

        return (jsonify(self.json(data)), self.status_code, {'ContentType': 'application/json'})
