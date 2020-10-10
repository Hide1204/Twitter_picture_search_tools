# coding: utf-8

import json
import os
import argparse
import time

from requests_oauthlib import OAuth1Session

# 設定ファイル
from data import API_config
from data import Search_words

# コマンドライン引数の設定
parser = argparse.ArgumentParser()
parser.add_argument("--maxid", type=int, default=1314950588266766338000, help="max idを指定する")
args = parser.parse_args()

# APIトークンの読み込み
try:
    CK      = API_config.CONSUMER_KEY
    CS      = API_config.CONSUMER_SECRET
    AT      = API_config.ACCESS_TOKEN
    ATS     = API_config.ACCESS_TOKEN_SECRET
except Exception:
    raise

try:
    search_list = Search_words.search_list
except Exception:
    raise

class TwitterAPI:
    def __init__(self, search_word):
        print('Collect "{}"'.format(search_word))

        # 変数の用意
        self._tweet_cnt = 0
        self._max_id = args.maxid

        # DBの接続


        # apiのためのセットアップ
        self._twitter_api = OAuth1Session(CK, CS, AT, ATS)
        self._SEARCH_URL = "https://api.twitter.com/1.1/search/tweets.json"
        self._RATE_LIMIT_STATUS_URL = "https://api.twitter.com/1.1/application/rate_limit_status.json"
        self._params = {
            'q'               : search_word,
            'count'           : 100,          # 取得するtweet数
            'result_type'     : 'recent',
            'max_id'        : self._max_id
        }

        # rate limitのstatusの取得
        status = self._get_rate_limit_status()
        self._LIMIT = status["limit"]
        self._remaining = status["remaining"]


    def _get_response(self):
        return self._twitter_api.get(self._SEARCH_URL, params=self._params)


    def _get_rate_limit_status(self):
        params = {
            "resources_famiily": "family"
        }
        response = self._twitter_api.get(self._RATE_LIMIT_STATUS_URL, params=params, timeout=1)
        return json.loads(response.text)["resources"]["users"]["/users/search"]


    def get_tweet(self):
        while True:
            if self._remaining > 0:
                response = self._get_response()
                self._remaining -= 1

                # 正常終了時
                if response.status_code == 200:
                    print(self._params['max_id'])
                    resp_body = json.loads(response.text)
                    resp_cnt = len(resp_body['statuses'])

                    # 収集結果が0件だったら終了
                    if resp_cnt == 0:
                        break

                    self._tweet_cnt += resp_cnt
                    print("count:{0}, total:{1} ".format(resp_cnt, self._tweet_cnt))

                    #print(resp_body)
                    # 収集したうちで最も小さいid-1を、次の収集のmax_idにする
                    self._params['max_id'] = resp_body['statuses'][-1]["id"] - 1

                    # 収集したツイートをDBに追加
                    #print("*******************")
                    #print(response)
                    #TODO

                # 異常終了
                else:
                    print(response)
                    print(json.loads(response.text))
                    break

            # rate limitに達したとき
            else:
                # resetまでの時間を取得して待つ（一応1秒長く待つ）
                status = self._get_rate_limit_status()
                wait_time = int(status["reset"] - time.time() + 1)

                for i in range(1, wait_time+1):
                    print("\rWaiting for rate limit reset: {0} / {1}[sec]".format(i, wait_time), end="")
                    time.sleep(1)

                print("")

                status = self._get_rate_limit_status()
                self._remaining = status["remaining"]

        print("--FINISH--")

def main():
    for search in search_list:
        twitter_api = TwitterAPI(
            search_word=search["search_word"]
        )
        twitter_api.get_tweet()

def test():
    ta = TwitterAPI(search_word="#未来へ飛び出せリトルエンジェルス")
    ta.get_tweet()

if __name__ == "__main__":
    #main()
    test()
