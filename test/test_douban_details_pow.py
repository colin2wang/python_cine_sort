import re
import time
import hashlib
import requests
from urllib.parse import urljoin


def calculate_nonce(challenge: str, difficulty: int = 4) -> str:
    """
    Calculate nonce that satisfies conditions (Proof of Work)
    Condition: First difficulty characters of SHA-512(cha + nonce) hex result are '0'
    """
    nonce = 1
    target_prefix = '0' * difficulty
    start_time = time.time()

    while True:
        data = f"{challenge}{nonce}"
        hash_hex = hashlib.sha512(data.encode('utf-8')).hexdigest()
        if hash_hex.startswith(target_prefix):
            elapsed = time.time() - start_time
            print(f"[✓] Found nonce={nonce} (Time taken: {elapsed:.2f}s)")
            return str(nonce)
        nonce += 1
        # Optional: Show progress every 100k attempts (prevent hanging)
        if nonce % 100000 == 0:
            print(f"  Attempted {nonce} times...")


def bypass_douban_verification(target_url: str, max_retries: int = 2) -> requests.Response:
    """
    Automatically handle Douban verification process, return response object of target page
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
                # 步骤1: 请求目标URL（自动跟随重定向）
                resp = session.get(target_url, timeout=15)
                resp.encoding = 'utf-8'

                # 步骤2: 检查是否为验证页（关键特征）
                if '<form name="sec" id="sec"' not in resp.text:
                    print(f"[✓] 无需验证，直接返回目标页面 (状态码: {resp.status_code})")
                    return resp

                print(f"[⚠] 检测到验证页 (尝试 {attempt + 1}/{max_retries})")

                # 步骤3: 提取关键参数
                tok = re.search(r'name="tok" value="([^"]+)"', resp.text)
                cha = re.search(r'name="cha" value="([^"]+)"', resp.text)
                red = re.search(r'name="red" value="([^"]+)"', resp.text)
                action_match = re.search(r'<form[^>]+action="([^"]+)"', resp.text)

                if not all([tok, cha, red, action_match]):
                    raise ValueError("Verification page parameter parsing failed")

                tok_val = tok.group(1)
                cha_val = cha.group(1)
                red_val = red.group(1)
                action_url = urljoin(resp.url, action_match.group(1).strip())

                print(f"  Challenge value (first 20 chars): {cha_val[:20]}...")
                print(f"  Target redirect address: {red_val}")

                # Step 4: Calculate nonce (sol)
                sol_val = calculate_nonce(cha_val, difficulty=4)

                # Step 5: Submit verification form (automatically follow redirects)
                payload = {
                    'tok': tok_val,
                    'cha': cha_val,
                    'sol': sol_val,
                    'red': red_val
                }
                verify_resp = session.post(action_url, data=payload, timeout=20)

                # Verify if successfully redirected to target page
                if verify_resp.url.rstrip('/') == red_val.rstrip('/'):
                    print(f"[✓] Verification successful! Redirected to: {verify_resp.url}")
                    return verify_resp
                else:
                    print(f"[!] Redirect abnormal, current URL: {verify_resp.url}")
                    # Continue retrying (may need to re-fetch verification page)

            except Exception as e:
                print(f"[✗] Verification process error (Attempt {attempt + 1}): {str(e)}")
                time.sleep(2)

        raise RuntimeError("Verification process failed: Maximum retry attempts reached")


# ============ Usage Example ============
if __name__ == "__main__":
    TARGET_MOVIE_URL = "https://movie.douban.com/subject/1292052/"

    try:
        response = bypass_douban_verification(TARGET_MOVIE_URL)
        # After success, can process page content
        # print(response.text)  # Caution: Content is lengthy
        print(f"Final page title fragment: {response.text}")

        # Optional: Save as HTML file for viewing
        # with open("douban_movie.html", "w", encoding="utf-8") as f:
        #     f.write(response.text)

    except Exception as e:
        print(f"Process terminated: {e}")