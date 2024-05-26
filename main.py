from serpapi import GoogleSearch

search = GoogleSearch({
    "q": "coffee",
    "location": "Austin,Texas",
    "api_key": "<your secret api key>"
  })
if __name__ == "__main__":
    result = search.get_dict()
    print(result)