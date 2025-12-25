import json

import pytest

from app.api.dependencies import get_optional_current_user
from app.api.error_handler import internal_error_response


@pytest.mark.asyncio
async def test_get_optional_current_user_returns_none_without_credentials():
    result = await get_optional_current_user(None, None)
    assert result is None


def test_internal_error_response_masks_detail_in_production():
    response = internal_error_response("sensitive detail", production_mode=True)
    payload = response.body.decode("utf-8")
    data = json.loads(payload)
    assert data["status"] == 500
    assert data["detail"] == "An internal error occurred. Please try again later."
