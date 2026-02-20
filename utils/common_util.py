import hashlib
import random
import re
import time
from functools import lru_cache
from urllib.parse import urljoin

import requests

from .logging_util import get_default_logger

logger = get_default_logger()


def sleep_for_random_time():
    sleep_time = random.uniform(0.5, 1.5)
    logger.info(f"Sleeping for {sleep_time:.2f} seconds...")
    time.sleep(sleep_time)


def calculate_nonce(challenge: str, difficulty: int = 4) -> str:
    """
    Calculate nonce that satisfies conditions (Proof of Work)
    Condition: First difficulty characters of SHA-512(cha + nonce) hex result are '0'

    Args:
        challenge (str): Challenge string from verification page
        difficulty (int): Number of leading zeros required (default: 4)

    Returns:
        str: Valid nonce value
    """
    nonce = 1
    target_prefix = '0' * difficulty
    start_time = time.time()

    while True:
        data = f"{challenge}{nonce}"
        hash_hex = hashlib.sha512(data.encode('utf-8')).hexdigest()
        if hash_hex.startswith(target_prefix):
            elapsed = time.time() - start_time
            logger.info(f"Found valid nonce={nonce} (Time taken: {elapsed:.2f}s)")
            return str(nonce)
        nonce += 1
        # Show progress every 100k attempts to prevent hanging
        if nonce % 100000 == 0:
            logger.debug(f"POW calculation attempted {nonce} times...")


@lru_cache(maxsize=128)
def bypass_douban_verification(target_url: str, max_retries: int = 2) -> requests.Response:
    """
    Automatically handle Douban verification process, return response object of target page

    Args:
        target_url (str): Target movie URL to access
        max_retries (int): Maximum number of retry attempts

    Returns:
        requests.Response: Response object of the target page

    Raises:
        RuntimeError: When verification fails after maximum retries
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.douban.com/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }

    with requests.Session() as session:
        session.headers.update(headers)

        for attempt in range(max_retries):
            try:
                sleep_for_random_time()

                # Step 1: Request target URL (follow redirects automatically)
                logger.info(f"Accessing target URL: {target_url}")
                resp = session.get(target_url, timeout=15)
                resp.encoding = 'utf-8'

                # Step 2: Check if it's a verification page (key characteristic)
                if '<form name="sec" id="sec"' not in resp.text:
                    logger.info(f"No verification required, returning target page (Status: {resp.status_code})")
                    return resp

                logger.warning(f"Verification page detected (Attempt {attempt + 1}/{max_retries})")

                # Step 3: Extract key parameters
                tok = re.search(r'name="tok" value="([^"]+)"', resp.text)
                cha = re.search(r'name="cha" value="([^"]+)"', resp.text)
                red = re.search(r'name="red" value="([^"]+)"', resp.text)
                action_match = re.search(r'<form[^>]+action="([^"]+)"', resp.text)

                if not all([tok, cha, red, action_match]):
                    raise ValueError("Failed to parse verification page parameters")

                tok_val = tok.group(1)
                cha_val = cha.group(1)
                red_val = red.group(1)
                action_url = urljoin(resp.url, action_match.group(1).strip())

                logger.info(f"Challenge value (first 20 chars): {cha_val[:20]}...")
                logger.info(f"Target redirect URL: {red_val}")

                # Step 4: Calculate nonce (solution)
                sol_val = calculate_nonce(cha_val, difficulty=4)

                # Step 5: Submit verification form (automatically follow redirects)
                payload = {
                    'tok': tok_val,
                    'cha': cha_val,
                    'sol': sol_val,
                    'red': red_val
                }

                sleep_for_random_time()
                logger.info("Submitting verification form...")
                verify_resp = session.post(action_url, data=payload, timeout=20)

                # Verify if successfully redirected to target page
                if verify_resp.url.rstrip('/') == red_val.rstrip('/'):
                    logger.info(f"Verification successful! Redirected to: {verify_resp.url}")
                    return verify_resp
                else:
                    logger.warning(f"Redirect abnormal, current URL: {verify_resp.url}")
                    # Continue retrying (may need to re-fetch verification page)

            except Exception as e:
                logger.error(f"Verification process error (Attempt {attempt + 1}): {str(e)}")
                time.sleep(2)

        raise RuntimeError("Verification process failed: Maximum retry attempts reached")