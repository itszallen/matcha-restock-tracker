import os
import requests
from bs4 import BeautifulSoup

# ====== CONFIGURATION ======
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

PRODUCTS = {
    "Unkaku": "https://www.marukyu-koyamaen.co.jp/english/shop/products/detail/1141020c1",
    "Kiwami Choan": "https://www.marukyu-koyamaen.co.jp/english/shop/products/detail/1g36020c1",
    "Cold brew Gyokuro": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1bcf040b5",
    "AMAZON TEST": "https://www.amazon.com/dp/B094FMCST9",
    "Ippodo Matcha To-Go": "https://ippodotea.com/collections/matcha/products/matcha-to-go-packets"
}

LOGIN_URL = "https://www.marukyu-koyamaen.co.jp/english/shop/my-account/"

# ====== LOGIN TO MARUKYU ======
def login_to_marukyu():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    }
    response = session.get(LOGIN_URL, headers=headers)

    print("=== LOGIN PAGE HTML START ===")
    print(response.text[:2000])  # Debug first 2000 chars
    print("=== LOGIN PAGE HTML END ===")

    soup = BeautifulSoup(response.text, "html.parser")

    try:
        token = soup.find("input", {"name": "woocommerce-login-nonce"})["value"]
        referer = soup.find("input", {"name": "_wp_http_referer"})["value"]
    except Exception as e:
        print(f"❌ Failed to extract login tokens: {e}")
        return None

    payload = {
        "username": os.environ["MARUKYU_USER"],
        "password": os.environ["MARUKYU_PASS"],
        "woocommerce-login-nonce": token,
        "_wp_http_referer": referer,
        "rememberme": "forever",
        "login": "Log in"
    }

    res = session.post(LOGIN_URL, data=payload, headers=headers)
    if "logout" in res.text.lower():
        print("✅ Logged into Marukyu successfully")
        return session
    else:
        print("❌ Marukyu login failed")
        return None

# ====== STOCK CHECK FUNCTIONS ======

def check_stock_amazon(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/103.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.select_one("#add-to-cart-button") is not None

def check_stock_marukyu(url, session):
    response = session.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    return bool(soup.select_one("button.single_add_to_cart_button"))

def check_stock_ippodo(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    button = soup.select_one("button.product-addbtn.btn-primary")
    if button:
        if button.has_attr("disabled"):
            return False
        
        inventory = button.get("data-inventory")
        if inventory and int(inventory) > 0:
            return True
        
        if "add to bag" in button.get_text(strip=True).lower():
            return True

    if soup.find(string=lambda t: t and "sold out" in t.lower()):
        return False

    return False

# ====== DISCORD NOTIFY ======
def notify(name, url):
    if not DISCORD_WEBHOOK_URL:
        print(f"[!] No Discord webhook set. Skipping notification for {name}.")
        return
    message = {
        "content": f"🚨 **{name}** is back in stock!\n{url}"
    }
    try:
        res = requests.post(DISCORD_WEBHOOK_URL, json=message)
        res.raise_for_status()
    except Exception as e:
        print(f"Failed to notify for {name}: {e}")

# ====== MAIN ======
def main():
    session = login_to_marukyu()

    for name, url in PRODUCTS.items():
        try:
            if "amazon.com" in url:
                in_stock = check_stock_amazon(url)
            elif "ippodotea.com" in url:
                in_stock = check_stock_ippodo(url)
            else:
                if not session:
                    print(f"[!] Can't check Marukyu item '{name}' without login.")
                    continue
                in_stock = check_stock_marukyu(url, session)

            if in_stock:
                notify(name, url)
                print(f"{name}: 🟢 In Stock")
            else:
                print(f"{name}: 🔴 Sold Out")

        except Exception as e:
            print(f"Error checking {name}: {e}")

if __name__ == "__main__":
    main()
