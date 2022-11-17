import re, json, time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from parsel import Selector
import urlparse

def video_id(url):
    """
    Examples:
    - http://youtu.be/SA2iWivDJiE
    - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
    - http://www.youtube.com/embed/SA2iWivDJiE
    - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
    """
    query = urlparse.urlparse(url)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch':
            p = urlparse.parse_qs(query.query)
            return p['v'][0]
        if query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]
    # fail?
    return None

def scroll_page(url):
	service = Service(executable_path="chromedriver")
	
	options = webdriver.ChromeOptions()
	options.headless = True
	options.add_argument("--lang=en")
	options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36")
	options.add_argument("--no-sandbox")
	options.add_argument("--disable-dev-shm-usage")
	
	driver = webdriver.Chrome(service=service, options=options)
	driver.get(url)
	
	old_height = driver.execute_script("""
		function getHeight() {
			return document.querySelector('ytd-app').scrollHeight;
		}
		return getHeight();
	""")
	
	while True:
		driver.execute_script("window.scrollTo(0, document.querySelector('ytd-app').scrollHeight)")
	
		time.sleep(2)
	
		new_height = driver.execute_script("""
			function getHeight() {
				return document.querySelector('ytd-app').scrollHeight;
			}
			return getHeight();
		""")
	
		if new_height == old_height:
			break
	
		old_height = new_height
	id = video_id(url)
	selector = Selector(driver.page_source)
	driver.quit()
    
	return selector, id



def scrape_all_data(selector,id):
   
	output = []
	
	all_script_tags = selector.css("script").getall()
	
	title = selector.css(".title .ytd-video-primary-info-renderer::text").get()
	
	
	# https://regex101.com/r/9OGwJp/1
	likes = int(re.search(r"(.*)\s", selector.css("#top-level-buttons-computed > ytd-toggle-button-renderer:first-child #text::attr(aria-label)").get()).group().replace(",", ""))
	
	date = selector.css("#info-strings yt-formatted-string::text").get()
	
	duration = selector.css(".ytp-time-duration::text").get()
	
	# https://regex101.com/r/0JNma3/1
	keywords = "".join(re.findall(r'"keywords":\[(.*)\],"channelId":".*"', str(all_script_tags))).replace('\"', '').split(",")
	
	# https://regex101.com/r/9VhH1s/1
	thumbnail = re.findall(r'\[{"url":"(\S+)","width":\d*,"height":\d*},', str(all_script_tags))[0].split('",')[0]
	
	authorName =  selector.css("#channel-name a::text").get(),

	description = selector.css(".ytd-expandable-video-description-body-renderer span:nth-child(1)::text").get()
	
	hashtags = [
		{
			"name": hash_tag.css("::text").get(),
			"link": f'https://www.youtube.com{hash_tag.css("::attr(href)").get()}'
		}
		for hash_tag in selector.css(".ytd-expandable-video-description-body-renderer a")
		if hash_tag.css("::text").get()[0] == '#'
	]
	comments_amount = 5 
	
	comments = []

	
	for comment in selector.css("#contents > ytd-comment-thread-renderer"):
		comments.append({
			"author": comment.css("#author-text span::text").get().strip(),
			"link": f'https://www.youtube.com{comment.css("#author-text::attr(href)").get()}',
			"date": comment.css(".published-time-text a::text").get(),
			"likes": comment.css("#vote-count-middle::text").get().strip(),
			"comment": comment.css("#content-text::text").get(),
			"avatar": comment.css("#author-thumbnail #img::attr(src)").get(),
		})
	
   
	
	output.append({
		"title": title,
		"likes": likes,
		"date": date,
		"duration": duration,
		"author Name": authorName,
		"keywords": keywords,
		"description": description,
		"hashtags": hashtags,
		"comments": comments,
        "Id": id,
	})
	
	print(json.dumps(output, indent=2, ensure_ascii=False))


def main():
    f = open ('data.json', "r")
  
    # Reading from file
    listId = json.loads(f.read())
  
    # Iterating through the json
    # list
    for i in listId['videos_id']:
        id= listId(i)
        url="https://www.youtube.com/watch?v="+id
        result,id = scroll_page(url)
        scrape_all_data(result,id)
        # Closing file
    f.close()


if __name__ == "__main__":
    main()