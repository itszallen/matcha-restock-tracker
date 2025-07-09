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
    "Ippodo Matcha To Go": "https://ippodotea.com/collections/matcha/products/matcha-to-go-packets"
}

LOGIN_URL = "https://www.marukyu-koyamaen.co.jp/english/shop/account"


# ====== LOGIN TO MARUKYU ======
def login_to_marukyu():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    }
    response = session.get(LOGIN_URL, headers=headers)
    
    print("=== LOGIN PAGE HTML START ===")
    print(response.text[:2000])  # Print first 2000 chars for debugging
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


# ====== STOCK CHECKING ======
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

    add_to_cart_btn = soup.select_one("button.single_add_to_cart_button")
    if add_to_cart_btn and not add_to_cart_btn.has_attr("disabled"):
        return True
    return False


def check_stock_ippodo(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Look for the add to bag button by CSS class
    add_to_bag_btn = soup.select_one("button.product-form__submit")

    if add_to_bag_btn:
        # Check if button is disabled
        if add_to_bag_btn.has_attr("disabled"):
            return False
        # Also check if button text contains "add to bag" to be sure
        if "add to bag" in add_to_bag_btn.get_text(strip=True).lower():
            return True

    # If button not found or disabled, also check for sold out text
    sold_out_text = soup.find(string=lambda t: t and "sold out" in t.lower())
    if sold_out_text:
        return False

    # Default fallback
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
