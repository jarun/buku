from typing import Any, Dict
from enum import Enum
from http import HTTPStatus
from flask import jsonify

OK, FAIL = 0, 1


class Response(Enum):
    SUCCESS = (HTTPStatus.OK, "Success.")                                         # 200
    FAILURE = (HTTPStatus.CONFLICT, "Failure.")                                   # 409
    REMOVED = (HTTPStatus.GONE, "Functionality no longer available.")             # 410
    INVALID_REQUEST = (HTTPStatus.BAD_REQUEST, "Ill-formed request.")             # 400
    INPUT_NOT_VALID = (HTTPStatus.UNPROCESSABLE_ENTITY, "Input data not valid.")  # 422
    TAG_NOT_VALID = (HTTPStatus.UNPROCESSABLE_ENTITY, "Invalid tag.")             # 422
    BOOKMARK_NOT_FOUND = (HTTPStatus.NOT_FOUND, "Bookmark not found.")            # 404
    RANGE_NOT_VALID = (HTTPStatus.NOT_FOUND, "Range not valid.")                  # 404
    TAG_NOT_FOUND = (HTTPStatus.NOT_FOUND, "Tag not found.")                      # 404

    @staticmethod
    def invalid(errors):
        return Response.INPUT_NOT_VALID(data={'errors': errors})

    @staticmethod
    def from_flag(flag: bool, *, data: Dict[str, Any] = None, errors: Dict[str, Any] = None):
        errors = dict(({'errors': errors} if errors else {}), **(data or {}))
        return Response.SUCCESS(data=data) if flag else Response.FAILURE(data=errors)

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
