import asyncio

class DBController:
     def __init__(self, path) -> None:
          self.path = path
          self.lock = asyncio.Lock()
     
     async def process_text_check(self,message,reply):
          async with self.lock:
               a = 2
               # here you should do db writing
          return

     def get_link_info(self, url):
          return "Here will be your link info. Url is: {}".format(url)