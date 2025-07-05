import requests
from bs4 import BeautifulSoup

PRODUCTS = {
    "Unkaku": "https://www.marukyu-koyamaen.co.jp/english/shop/products/detail/1141020c1",
    "Kiwami Choan": "https://www.marukyu-koyamaen.co.jp/english/shop/products/detail/1g36020c1",
    "Cold brew Gyokuro": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1bcf040b5",
    "AMAZON TEST": "https://www.amazon.com/CNCJ-Hourglass-Sand-Timer-Minute/dp/B094FMCST9/?_encoding=UTF8&pd_rd_w=ZIbQO&content-id=amzn1.sym.255b3518-6e7f-495c-8611-30a58648072e%3Aamzn1.symc.a68f4ca3-28dc-4388-a2cf-24672c480d8f&pf_rd_p=255b3518-6e7f-495c-8611-30a58648072e&pf_rd_r=0G2W7NWYYCNG3TDEK0S3&pd_rd_wg=I5LIN&pd_rd_r=b886bb4c-ac7d-4d1c-83d0-b436400b9a83&ref_=pd_hp_d_atf_ci_mcx_mr_ca_hp_atf_d&th=1"
    
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
