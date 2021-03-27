#################################
##### Name: YuHua
##### Uniqname: simonhua
#################################

from bs4 import BeautifulSoup
import requests
import json
from secrets import API_KEY
import secrets # file that contains your API key

base_url = 'https://www.nps.gov'

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = ''.join(list(filter(lambda ch: ch in '0123456789-', zipcode)))
        self.phone = ''.join(list(filter(lambda ch: ch in '0123456789() -', phone)))

    def info(self):
        return self.name + ' (' + self.category + '): ' + self.address + ' ' + self.zipcode
    

def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    data = {}
    try:
        with open('build_state_url_dict.json', 'r') as f:
            data = f.read()
            if len(data) != 3311:
                raise Exception
            print("Using Cache")
            # print(data)
            data = json.loads(data)
            # print(type(data))
            
    except :
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0'}
        url = base_url + '/index.html'
        print("Fetching")
        r = requests.get(url, headers = headers)

        soup = BeautifulSoup(r.text, 'html.parser')
        find_data = soup.find('ul',class_="dropdown-menu SearchBar-keywordSearch").find_all('a')
        data = {i.contents[0].lower() : (base_url + i['href']) for i in find_data}
        with open('build_state_url_dict.json', 'w', encoding='utf-8') as file:
            file.write(json.dumps(data, indent = 4, ensure_ascii = False))
    return data

       

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    text = ''
    try:
        with open(site_url.replace('.','_').replace('/','&') + '.json', 'r') as f:
            text = f.read()
            print("Using Cache")
    except:
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0'}
        print("Fetching")
        r = requests.get(site_url, headers = headers)
        text = r.text
        with open(site_url.replace('.','_').replace('/','&') + '.json', 'w', encoding='utf-8') as file:
            file.write(text)
    soup = BeautifulSoup(text, 'html.parser')
    name = soup.find('a', class_ = 'Hero-title').contents[0]
    category = soup.find('span', class_ = 'Hero-designation').contents[0]
    address = soup.find('span', itemprop = "addressLocality").contents[0] + ', ' + soup.find('span', itemprop="addressRegion").contents[0]
    zipcode = soup.find('span', itemprop = "postalCode").contents[0]
    phone = soup.find('span', itemprop = "telephone").contents[0]
    tmp = NationalSite(category, name, address, zipcode, phone)
    return tmp

def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    list_of_nationsite = []
    text = ''
    try:
        with open(state_url.replace('.','_').replace('/','&') + '.json', 'r') as f:
            text = f.read()
            print("Using Cache")
    except:
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0'}
        print("Fetching")
        r = requests.get(state_url, headers = headers)
        text = r.text
        with open(state_url.replace('.','_').replace('/','&') + '.json', 'w', encoding='utf-8') as file:
            file.write(text)
    soup = BeautifulSoup(text, 'html.parser')
    find_data = soup.find_all('li', class_='clearfix')[0:-1]
    list_of_site_to_discover = []
    for ele in find_data:
        list_of_site_to_discover.append(base_url + ele.find('h3').find('a')['href'])
    for ele in list_of_site_to_discover:
        list_of_nationsite.append(get_site_instance(ele))
    return list_of_nationsite


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    base_url = 'http://www.mapquestapi.com/search/v2/radius?'
    key = API_KEY
    origin = site_object.zipcode
    radius = 10.0
    maxMatches = 10
    ambiguities = 'ignore'
    outFormat = 'json'
    url = base_url + 'key=' + key + '&origin=' + origin + '&radius=' + str(radius) + '&maxMatches=' + str(maxMatches) + '&ambiguities=' + ambiguities + '&outFormat=' + outFormat
    data = json.loads(requests.get(url).content)
    res = data['searchResults']
    for ele in res:
        result = '- '
        result += ele['name'] +' '
        if 'group_sic_code_name' in ele:
            result += '(' + ele['group_sic_code_name'] +'): '
        else:
            result += '(no category): '

        if 'address' in ele['fields'] and len(ele['fields']['address']) > 0:
            result += ele['fields']['address'] +', '
        else:
            result += 'no address, '

        if 'city' in ele['fields'] and len(ele['fields']['city']) > 0:
            result += ele['fields']['city']
        else:
            result += 'no city'
        print(result)

    return data

def find_place():
    state = input('Enter a state name (e.g. Michigan, michigan) or "exit"\n:') 
    while state.lower() not in dic_of_state:
        if state.lower() == 'exit':
            exit()
        print("[Error] Enter proper state name")
        print("\n")
        state = input('Enter a state name (e.g. Michigan, michigan) or "exit"\n:') 
        
    
    list_to_show = get_sites_for_state(dic_of_state[state.lower()])
    i = 0
    print("-" * (26 + len(state)))
    print("List of national sites in " + state)
    print("-" * (26 + len(state)))
    for ele in list_to_show:
        i += 1
        print('[' + str(i) + '] ' + ele.info())
    print("\n")
    return list_to_show

if __name__ == "__main__":
    dic_of_state = build_state_url_dict()
    
    list_to_show = find_place()
    step = input('Choose the number for detail search or "exit" or "back"\n:') 
    while True:
        if step.lower() == 'exit':
            exit()
        elif step.lower() == 'back':
            list_to_show = find_place()
            step = input('Choose the number for detail search or "exit" or "back"\n:') 
        elif step.isdigit() and int(step) <= len(list_to_show) and int(step) >= 1:
            state = list_to_show[int(step) - 1].name
            print("-" * (11 + len(state)))
            print("Place near " + state)
            print("-" * (11 + len(state)))
            get_nearby_places(list_to_show[int(step) - 1])
            print("\n")
        else:
            print("[Error] Invalid input\n")
        step = input('Choose the number for detail search or "exit" or "back"\n:')

    