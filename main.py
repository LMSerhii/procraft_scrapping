import json
import os

import requests
from bs4 import BeautifulSoup


def get_data():
    """  """
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/107.0.0.0 Safari/537.36"

    }

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

    all_data = []

    with requests.Session() as session:

        # выполняем request по разновидностям товаров
        for url in category_links:

            category_name = url.split('/')[-2]

            if not os.path.exists(f"data/{category_name}"):
                os.mkdir(f"data/{category_name}")

            response = session.get(url=url, headers=headers)

            soup = BeautifulSoup(response.text, "lxml")

            try:
                subdirectories = soup.find('div', class_="categories-wrapp").find_all("div", class_="category-wrapp")

                # ссылки на подкаталоги товаров
                subdirectory_links = [subdirectory.find('a').get("href") for subdirectory in subdirectories]
                # ссылки на фото подкаталогов товаров
                subdirectory_imgs = [subdirectory.find('img').get("data-src") for subdirectory in subdirectories]
                # html разметка описания разновидности товаров
                subdirectory_text = soup.find('div', class_="tb_category_description tb_text_wrap")

                # Записываем в файл описание разновидностей товаров
                with open(f"data/{category_name}/{category_name}_text.txt", "w", encoding="utf-8") as file:
                    file.write(str(subdirectory_text))
            except Exception as ex:
                continue

            # Выполняем request по разновидностям товаров
            subcategory = []
            for subdirectory_link in subdirectory_links:

                subcategory_name = subdirectory_link.split('/')[-1]
                response = session.get(url=subdirectory_link, headers=headers)

                if not os.path.exists(f"data/{category_name}/{subcategory_name}"):
                    os.mkdir(f"data/{category_name}/{subcategory_name}")

                soup = BeautifulSoup(response.text, "lxml")

                try:
                    products_group_text = soup.find("div", class_="tb_category_description tb_text_wrap")
                except Exception as ex:
                    products_group_text = None

                # Записываем в файл описание подкаталогов
                with open(f"data/{category_name}/{subcategory_name}/{subcategory_name}_text.txt", "w", encoding='utf-8') as file:
                    file.write(str(products_group_text))

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
                        product_title = product_link.split("/")[-1]

                        product_name = soup.find("div",
                                                 class_="tb_wt tb_wt_page_title_system tb_mb_20 display-block tb_system_page_title").find(
                            "h1").text.strip()

                        text = soup.find("div", class_="panel-body tb_product_description tb_text_wrap")

                        attributes = soup.find("div", class_="attributes").find_all("div", class_="single-attr")
                        product_attributes = {}
                        for attribute in attributes:
                            attr_key = attribute.find("span").text.strip()
                            attr_value = attribute.find("span").next_element.next_element.text.strip()
                            product_attributes[attr_key] = attr_value

                        if not os.path.exists(f"data/{category_name}/{subcategory_name}/cards/"):
                            os.mkdir(f"data/{category_name}/{subcategory_name}/cards/")

                        with open(f"data/{category_name}/{subcategory_name}/cards/{product_title}_text.txt", "w", encoding='utf-8') as file:
                            file.write(str(text))

                        cards.append(
                            {
                                "product_name": product_name,
                                "product_link": product_link,
                                "product_attributes": product_attributes


                            }
                        )

                subcategory.append(
                    {
                        "subcategory_name": subcategory_name,
                        "subdirectory_link": subdirectory_link,
                        "cards": cards,
                    }
                )

            all_data.append(
                {
                    "category_name": category_name,
                    "category_url": url,
                    "subcategory": subcategory,
                }
            )
            print(f"[+] Scrap {category_name} is completed")

    with open("all_data.json", "w", encoding="utf-8") as file:
        json.dump(all_data, file, indent=4, ensure_ascii=False)

    return "[INFO] Work is done!!"


def download_imgs():
    """"""


def main():
    print(get_data())


if __name__ == '__main__':
    main()
