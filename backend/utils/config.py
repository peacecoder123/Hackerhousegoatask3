"""
utils/config.py
---------------
Load and validate required environment variables.
"""

from __future__ import annotations
import os
from dataclasses import dataclass


@dataclass
class Config:
    serpapi_key: str
    web3_provider_url: str
    wallet_private_key: str
    contract_address: str


def get_config() -> Config:
    """
    Read environment variables and return a validated Config object.

    Raises:
        EnvironmentError: If any required variable is missing.
    """
    missing = []
    keys = ["SERPAPI_KEY", "WEB3_PROVIDER_URL", "WALLET_PRIVATE_KEY", "CONTRACT_ADDRESS"]
    values = {}

    for key in keys:
        val = os.getenv(key)
        if not val:
            missing.append(key)
        else:
            values[key] = val

    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Create a .env file with these keys (see README.md)."
        )

    return Config(
        serpapi_key=values["SERPAPI_KEY"],
        web3_provider_url=values["WEB3_PROVIDER_URL"],
        wallet_private_key=values["WALLET_PRIVATE_KEY"],
        contract_address=values["CONTRACT_ADDRESS"],
    )
