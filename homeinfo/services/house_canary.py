"""
Author: Edwin S. Cowart
Created: 4/17/22
"""
import logging
import requests  # Import has to be structured this way for unittest.mock.patch
from typing import Tuple, Optional, Literal, Union, TypedDict
from django.conf import settings

HTTPMethod = Literal["get", "options", "head", "post", "put", "patch", "delete"]


def _make_house_canary_api_request(
    method: HTTPMethod, route: str, params: Optional[dict]
) -> Tuple[requests.Response, Optional[requests.exceptions.RequestException]]:
    """
    :param method: HTTP method
    :param route: House Canary route
    :param params: Query params
    :return: Success: (Response, None)
             Error:   (Response, Exception)
    """
    try:
        response = requests.request(
            method=method,
            url=f"{settings.HOUSE_CANARY_API_URL}/{route}",
            params=params,
            timeout=settings.HOUSE_CANARY_TIMEOUT_S,
        )
        response.raise_for_status()
        return response, None
    except requests.exceptions.RequestException as e:
        return e.response, e


# NOTE API doc is inconsistent about capitalization. Be sure to casefold when doing comparisons.
Sewer = Literal["Municipal", "None", "Storm", "Septic", "Yes"]


class PropertyDetails(TypedDict):
    sewer: Sewer


def is_septic(property_details: PropertyDetails) -> bool:
    return property_details["sewer"].casefold() == "Septic".casefold()


def get_property_details(
    address: str, zipcode: str
) -> Union[Tuple[PropertyDetails, None], Tuple[None, requests.RequestException]]:
    """Get property details
    :param address: Single line address
    :param zipcode: Zip code
    :return: Success: (Response, Property, None)
             Error:   (Response, None, Exception)
    """
    # https://api-docs.housecanary.com/#property-details
    response, exception = _make_house_canary_api_request(
        method="get",
        route="property/details",
        params={"address": address, "zipcode": zipcode},
    )
    if exception:
        # TODO Next Step log exception to exception monitoring service
        logging.exception(exception, stack_info=True)
        return None, exception

    # TODO Next Step consider capturing contract violations here instead of allowing the exception to
    #  propagate down the call stack
    property_details = response.json()["property/details"]["result"]["property"]
    return property_details, None