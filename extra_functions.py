import requests

url = 'https://www.instagram.com/api/graphql'

def get_play_count(reel_short_code=None):

    # reel_short_code = 'C8Ka1fzvTyn'

    headers= {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/x-www-form-urlencoded",
        "priority": "u=1, i",
        "sec-ch-prefers-color-scheme": "dark",
        "sec-ch-ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
        "sec-ch-ua-full-version-list": "\"Google Chrome\";v=\"125.0.6422.114\", \"Chromium\";v=\"125.0.6422.114\", \"Not.A/Brand\";v=\"24.0.0.0\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": "\"\"",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-ch-ua-platform-version": "\"15.0.0\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-asbd-id": "129477",
        "x-csrftoken": "FeZkR5km8wFdAI-vHANv0K",
        "x-fb-friendly-name": "PolarisPostActionLoadPostQueryLegacyQuery",
        "x-fb-lsd": "AVo8j1qOP2g",
        "x-ig-app-id": "936619743392459",
        "cookie": "csrftoken=FeZkR5km8wFdAI-vHANv0K; ps_n=1; ps_l=1; dpr=2; mid=ZmyzqwALAAHic7lcHhGXNs665LS8; ig_did=EF2112DD-AC1B-4630-9FA0-0305F5FABB9A; ig_nrcb=1; datr=qrNsZjTtnuU2G2L5HaxBZnHp; wd=1030x827",
        "Referer": f"https://www.instagram.com/reel/{reel_short_code}/?hl=en",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }
    post_data = f"av=0&hl=en&__d=www&__user=0&__a=1&__req=i&__hs=19888.HYP%3Ainstagram_web_pkg.2.1..0.0&dpr=1&__ccg=UNKNOWN&__rev=1014227545&__s=n6vsas%3A42oj3l%3Ax4zlaf&__hsi=7380471438416309875&__dyn=7xeUjG1mxu1syUbFp40NonwgU7SbzEdF8aUco2qwJw5ux609vCwjE1xoswaq0yE6ucw5Mx62G5UswoEcE7O2l0Fwqo31w9O1TwQzXwae4UaEW2G0AEcobEaU2eUlwhEe87q7U1bobpEbUGdwtUeo9UaQ0Lo6-3u2WE5B08-269wr86C1mwPwUQp1yUb8jxKi2qi7ErwYCz8KfwHw&__csr=n2Yfg_5hcQkxlITjW8QBieB_FSrHhuQjj9Rp4mXy7SFpaDHFHjFAzk-nyAtenh68aiAKta8hoShogKkF5yaUBqCpF9XHmmhoBXyBKbQWgaWK2tdFz8VDAzudhK4XLGiGDvByoNaEGp1-HxTDzVQ5Fp801nrEkO0rC58xwf2440euw1XdEAzwKwnNWg9Ef8887W582bxjc0epwjo3kw4pyP02h81Ie0oq00BoU&__comet_req=7&lsd=AVo8j1qOP2g&jazoest=2898&__spin_r=1014227545&__spin_b=trunk&__spin_t=1718399914&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=PolarisPostActionLoadPostQueryLegacyQuery&variables=%7B%22shortcode%22%3A%22{reel_short_code}%22%2C%22fetch_comment_count%22%3A40%2C%22fetch_related_profile_media_count%22%3A3%2C%22parent_comment_count%22%3A24%2C%22child_comment_count%22%3A3%2C%22fetch_like_count%22%3A10%2C%22fetch_tagged_user_count%22%3Anull%2C%22fetch_preview_comment_count%22%3A2%2C%22has_threaded_comments%22%3Atrue%2C%22hoisted_comment_id%22%3Anull%2C%22hoisted_reply_id%22%3Anull%7D&server_timestamps=true&doc_id=7341532402634560"

    r = requests.post(url=url,headers=headers,data=post_data)

    # print(r.json())
    try:
        r_json = r.json()
        play_count = r_json['data']['xdt_shortcode_media']['video_play_count']
        print(reel_short_code,"  -  ",play_count)
        return play_count
    except:
        return None

# with open("output.txt","w",encoding="utf-8") as w:
#     w.writelines(r.text)


# get_play_count()