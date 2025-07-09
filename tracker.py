import os
import requests
from bs4 import BeautifulSoup

# ====== CONFIGURATION ======
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

PRODUCTS = {
    # Marukyu Koyamaen products
    "Unkaku Matcha": "https://www.marukyu-koyamaen.co.jp/english/shop/products/detail/1141020c1",
    "Kiwami Choan Matcha": "https://www.marukyu-koyamaen.co.jp/english/shop/products/detail/1g36020c1",
    "Cold Brew Gyokuro": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1bcf040b5",
    "Asahi Matcha": "https://www.marukyu-koyamaen.co.jp/english/shop/products/11a1040c1",
    "Sayaka Matcha": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1181040c1",
    "Momoyuki Matcha": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1171020c1",
    "Shirakawa Matcha": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1151020c1",
    "Fumiko Matcha": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1131020c1",
    "Gokujo Matcha": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1121020c1",
    "Tokujou Matcha": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1111020c1",
    "Omatcha Matcha": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1161020c1",

    # Amazon test product
    "AMAZON TEST": "https://www.amazon.com/dp/B094FMCST9",

    # Ippodo Tea products
    "Ippodo Matcha To-Go Packets": "https://ippodotea.com/collections/matcha/products/matcha-to-go-packets",
    "Ippodo Sayaka 100g": "https://ippodotea.com/collections/matcha/products/sayaka-100g",
    "Ippodo Sayaka no Mukashi": "https://ippodotea.com/collections/matcha/products/sayaka-no-mukashi",
    "Ippodo Kan Matcha": "https://ippodotea.com/collections/matcha/products/kan",
    "Ippodo Ikuyo 100g": "https://ippodotea.com/collections/matcha/products/ikuyo-100",
    "Ippodo Ikuyo": "https://ippodotea.com/collections/matcha/products/ikuyo",
    "Ippodo Wakaki Shiro": "https://ippodotea.com/collections/matcha/products/wakaki-shiro"
}

LOGIN_URL = "https://www.marukyu-koyamaen.co.jp/english/shop/account/"

# ====== LOGIN TO MARUKYU ======
def login_to_marukyu():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    }
    response = session.get(LOGIN_URL, headers=headers)
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

    if soup.select_one("#add-to-cart-button") or soup.select_one("#buy-now-button"):
        return True

    availability = soup.select_one("#availability")
    if availability:
        text = availability.get_text(strip=True).lower()
        if "in stock" in text:
            return True
        if "currently unavailable" in text or "temporarily out of stock" in text:
            return False

    text = soup.get_text().lower()
    if "only" in text and "left in stock" in text:
        return True
    if "currently unavailable" in text or "temporarily out of stock" in text:
        return False
    if "in stock" in text:
        return True

    return False

def check_stock_marukyu(url, session):
    response = session.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    stock_notice = soup.find("p", class_="stock out-of-stock")
    if stock_notice and "out of stock" in stock_notice.get_text(strip=True).lower():
        return False

    button = soup.select_one("button.single_add_to_cart_button")
    if button and not button.has_attr("disabled"):
        return True

    if "out of stock" in soup.get_text().lower():
        return False

    return False

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
