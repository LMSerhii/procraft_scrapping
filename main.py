import json
import os
import pprint
import time

import requests
from bs4 import BeautifulSoup


headers = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/107.0.0.0 Safari/537.36"

}


def get_data():
    """  """

    category_links = ['https://procraft.ua/ua/elektroinstrument/',
                      'https://procraft.ua/ua/akkumuljatornyj-instrument/',
                      'https://procraft.ua/ua/derevoobrabatyvajuschij-instrument/',
                      'https://procraft.ua/ua/svarochnoe-oborudovanie/',
                      'https://procraft.ua/ua/sadovo-parkovyj-instrument/',
                      'https://procraft.ua/ua/benzointrumenty/',
                      'https://procraft.ua/ua/shlifovalnoj-instrument/',
                      'https://procraft.ua/ua/kraskopulty-i-compressory/',
                      'https://procraft.ua/ua/kraskopulty-i-compressory/',
                      'https://procraft.ua/ua/zatochki/',
                      'https://procraft.ua/ua/stanki/',
                      'https://procraft.ua/ua/stroitelnye-pylesosy-i-avtomojki/',
                      'https://procraft.ua/ua/nabory-instrumentov/'
                      ]
    all_data = {}
    video_count = 0
    images_count = 0
    items_count = 0
    category_items = []
    with requests.Session() as session:

        # выполняем request по разновидностям товаров
        for url in category_links:

            response = session.get(url=url, headers=headers)
            soup = BeautifulSoup(response.text, "lxml")

            subdirectories = soup.find('div', class_="categories-wrapp").find_all("div", class_="category-wrapp")

            # ссылки на подкаталоги товаров
            subdirectory_links = [subdirectory.find('a').get("href") for subdirectory in subdirectories]

            category_name = url.split("/")[-2]
            try:
                # html разметка описания разновидности товаров
                subdirectory_description = soup.find('div', class_="tb_category_description tb_text_wrap")
            except Exception as ex:
                pass

            subcategory = []
            for subdirectory_link in subdirectory_links:

                subcategory_name = subdirectory_link.split('/')[-1]

                response = session.get(url=subdirectory_link, headers=headers)

                soup = BeautifulSoup(response.text, "lxml")

                try:
                    group_description = soup.find("div", class_="tb_category_description tb_text_wrap")
                except Exception as ex:
                    group_description = None
                try:
                    pagination = \
                    soup.find("div", class_="pagination tb_mt_0 tb_mb_30").find("ul", class_="links").find_all("li")[
                        -3].text.strip()
                except Exception as ex:
                    pagination = 1

                cards = []
                for page in range(1, int(pagination) + 1):

                    response = session.get(url=f"{subdirectory_link}/page-{page}/", headers=headers)
                    soup = BeautifulSoup(response.text, "lxml")

                    try:
                        products_links = soup.find_all("div", class_="image image_slide active")
                        products_links_list = [product_link.find('a').get('href') for product_link in products_links]
                    except Exception as ex:
                        continue

                    # Побегаем по ссылке каждого продукта
                    for product_link in products_links_list:
                        response = session.get(url=product_link, headers=headers)
                        soup = BeautifulSoup(response.text, 'lxml')

                        product_name = soup.find("div",
                                                 class_="tb_wt tb_wt_page_title_system tb_mb_20 display-block tb_system_page_title").find(
                            "h1").text.strip()

                        description = soup.find("div", class_="panel-body tb_product_description tb_text_wrap")
                        attributes_html = soup.find("div", class_="attributes").find_all("div", class_="single-attr")
                        product_attributes = {}
                        for attribute in attributes_html:
                            attr_key = attribute.find("span").text.strip()
                            attr_value = attribute.find("span").next_element.next_element.text.strip()
                            product_attributes[attr_key] = attr_value

                        image_links = soup.find("div", id="additional")
                        try:
                            video_link = image_links.find("div", class_="image-additional swiper-slide three_de_video").find("a").get("href")
                            video_count += 1
                        except Exception:
                            video_link = None

                        image_urls = image_links.find_all("div", class_="image-additional swiper-slide")
                        product_image_links = [image_link.find("a").get('href') for image_link in image_urls]

                        cards.append(
                            {
                                "product_name": product_name,
                                "product_attributes": product_attributes,
                                "product_link": product_link,
                                "video_link": video_link,
                                "product_image_links": product_image_links,
                                "attributes_html": str(attributes_html),
                                "description": str(description),
                            }
                        )
                        items_count += 1
                        images_count += len(product_image_links)

                subcategory.append(
                    {
                        "subcategory_name": subcategory_name,
                        "subdirectory_link": subdirectory_link,
                        "group_description": str(group_description),
                        "cards": cards,
                    }
                )

                print(f" Category {subcategory_name} is completed")

            category_items.append(
                {
                    "category_name": category_name,
                    "category_url": url,
                    "subdirectory_description": str(subdirectory_description),
                    "subcategory": subcategory,
                }
            )
            print(f"[+] Scrap {category_name} is completed")

    all_data['category_items'] = category_items
    all_data['items_count'] = items_count
    all_data['images_count'] = images_count
    all_data['video_count'] = video_count

    with open("all_data.json", "w", encoding="utf-8") as file:
        json.dump(all_data, file, indent=4, ensure_ascii=False)

    return "[INFO] Work is done!!"


def download_imgs():
    """ """
    with open("all_data.json", "r", encoding="utf-8") as file:
        src = json.load(file)

    with requests.Session() as session:

        category_items = src['category_items']
        images_count = src['images_count']
        count = 0
        for category_item in category_items:
            subcategory = category_item['subcategory']
            category_name = category_item['category_name']

            if not os.path.exists(f"data/{category_name}"):
                os.mkdir(f"data/{category_name}")

            for cards in subcategory:
                subcategory_name = cards['subcategory_name']
                cards = cards['cards']

                if not os.path.exists(f"data/{category_name}/{subcategory_name}"):
                    os.mkdir(f"data/{category_name}/{subcategory_name}")

                for card in cards:
                    product_name = card['product_link'].split("/")[-1]

                    product_image_links = card['product_image_links']
                    # print(product_image_links)
                    if not os.path.exists(f"data/{category_name}/{subcategory_name}/{product_name}"):
                        os.mkdir(f"data/{category_name}/{subcategory_name}/{product_name}")

                    img_count = 0
                    for product_image_link in product_image_links:

                        response = session.get(url=product_image_link, headers=headers)

                        with open(f"data/{category_name}/{subcategory_name}/{product_name}/img_{img_count}.png", 'wb') as file:
                            file.write(response.content)

                        img_count += 1
                        count += 1

                        print(f"Item: {count}/{images_count} is completed")

                    # if count % 25 == 0:
                    #     time.sleep(7)


def download_txt():
    """ """
    with open("all_data.json", "r", encoding="utf-8") as file:
        src = json.load(file)

    category_items = src['category_items']
    items_count = src['items_count']
    count = 0
    for category_item in category_items:
        subcategory = category_item['subcategory']
        category_name = category_item['category_name']
        subdirectory_description = category_item['subdirectory_description']

        if not os.path.exists(f"data/{category_name}"):
            os.mkdir(f"data/{category_name}")

        with open(f"data/{category_name}/{category_name}.txt", "w", encoding='utf-8') as file:
            file.write(subdirectory_description)

            for cards in subcategory:
                subcategory_name = cards['subcategory_name']
                group_description = cards['group_description']
                cards = cards['cards']

                if not os.path.exists(f"data/{category_name}/{subcategory_name}"):
                    os.mkdir(f"data/{category_name}/{subcategory_name}")

                with open(f"data/{category_name}/{subcategory_name}/{category_name}.txt", "w", encoding='utf-8') as file:
                    file.write(group_description)

                for card in cards:
                    product_name = card['product_link'].split("/")[-1]
                    video_link = card['video_link']
                    description = card['description']
                    attributes_html = card['attributes_html']

                    product_description = f"{description}\n\n\n{attributes_html}\n\n\n{video_link}"

                    if not os.path.exists(f"data/{category_name}/{subcategory_name}/{product_name}"):

                        os.mkdir(f"data/{category_name}/{subcategory_name}/{product_name}")

                    with open(f"data/{category_name}/{subcategory_name}/{product_name}/{count}.txt", "w",
                              encoding='utf-8') as file:
                        file.write(product_description)
                    count += 1

                    print(f"Item: {count}/{items_count} is completed")

                    # new comment
def main():
    print(get_data())
    download_txt()
    download_imgs()


if __name__ == '__main__':
    main()
