import requests

class wow():

  async def getRandomWow():
    url = "https://owen-wilson-wow-api.herokuapp.com/wows/random"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)
    return(response.text)

  async def getWowVideo():
    