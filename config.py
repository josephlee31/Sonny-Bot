# Initialize player class
class Player:
    def __init__(self, link):
        self.link = link

# BeautifulSoup helper variables
headers = {'User-Agent': 
           'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}

# Transfermarkt links
transermarkt_mainpage = 'https://www.transfermarkt.us'
transermarkt_query = 'https://www.transfermarkt.us/schnellsuche/ergebnis/schnellsuche?query='