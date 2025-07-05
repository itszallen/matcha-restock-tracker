import requests
from bs4 import BeautifulSoup

PRODUCTS = {
    "Unkaku": "https://www.marukyu-koyamaen.co.jp/english/shop/products/detail/1141020c1",
    "Kiwami Choan": "https://www.marukyu-koyamaen.co.jp/english/shop/products/detail/1g36020c1",
    "POOP": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1bcf040b5"
}

def check_stock(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        return bool(soup.select_one("button.add-to-cart"))
    except Exception as e:
        print(f"Error checking {url}: {e}")
        return False

def notify(name, url):
    # Placeholder: Extend this to send Telegram or email notifications
    print(f"Notification: {name} is back in stock! Check {url}")

def main():
    for name, url in PRODUCTS.items():
        if check_stock(url):
            notify(name, url)
        else:
            print(f"{name}: Sold Out")

if __name__ == "__main__":
    main()
