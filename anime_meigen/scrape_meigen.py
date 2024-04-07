from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import pandas as pd
import re
import os



#スクレイピング関数
def scrape_url_page(urls):
    #Chromeドライバーの設定
    options = Options()
    options.add_argument('--headless')
    service = webdriver.ChromeService(executable_path="./chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    #スクレイピング実行と名言の保存
    all_meigen_data = pd.DataFrame()
    for url in urls:
        #名言の取得
        driver.get(url)
        meigen_container = driver.find_element(By.TAG_NAME, "article")
        body = meigen_container.find_element(By.CSS_SELECTOR, "[itemprop='mainEntityOfPage']")
        anime_title = body.find_element(By.TAG_NAME, "h3")
        meigen_list = body.find_elements(By.XPATH, "//p[strong]")

        #名言の保存
        meigen_data = pd.DataFrame({
            "anime":[anime_title.text] * len(meigen_list),
            "meigen":[meigen.text for meigen in meigen_list]
        })
        all_meigen_data = pd.concat([all_meigen_data, meigen_data])

    all_meigen_data = all_meigen_data.reset_index().drop("index", axis=1)

    #ドライバーの終了
    driver.quit()

    return all_meigen_data.reset_index()


#データ前処理関数
def preprocess_meigen_data(meigen_data):
    #データの加工
    meigen_data["character"] = meigen_data["meigen"].apply(lambda x:re.findall(r"\((.*?)\)", x) or None)
    exploded_meigen_data = meigen_data.explode("character").reset_index(drop=True)
    exploded_meigen_data = exploded_meigen_data[~exploded_meigen_data["character"].isin(["仮","白衣に","会話を","紅莉栖の…"])].reset_index()
    exploded_meigen_data.drop("index", axis=1, inplace=True)

    #セリフの結合
    concat_meigen = ""
    for idx in range(len(exploded_meigen_data)):
        if exploded_meigen_data["character"].iloc[idx] is None:
            if not concat_meigen:
                concat_meigen += exploded_meigen_data["meigen"].loc[idx]
        else:
            if concat_meigen:
                exploded_meigen_data.loc[idx, "meigen"] = concat_meigen + exploded_meigen_data.loc[idx, "meigen"]
                concat_meigen = ""

    exploded_meigen_data = exploded_meigen_data[pd.notnull(exploded_meigen_data["character"])]
    groupby_meigen_data = exploded_meigen_data.groupby(["meigen","anime"]).agg(list).reset_index()
    groupby_meigen_data.drop("level_0", axis=1, inplace=True)

    return groupby_meigen_data


#データ出力関数
def output_data(meigen_data):
    #データの出力
    os.makedirs("data", exist_ok=True)
    meigen_data.to_pickle("data/meigen.pkl")



if __name__ == "__main__":
    #スクレイピングするWEBページのURLたち
    urls = [
        "https://animemanga33.com/archives/9553",
        "https://animemanga33.com/archives/1268"
        ]

    meigen_data = scrape_url_page(urls)
    meigen_data = preprocess_meigen_data(meigen_data)
    output_data(meigen_data)

