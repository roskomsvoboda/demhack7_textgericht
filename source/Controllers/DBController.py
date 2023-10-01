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
     
     async def process_feedback(self,reply):
          async with self.lock:
               a = 2
               # here you should do db writing
          return

     async def process_url_check(self,url,reply):
          async with self.lock:
               a = 2
               # here you should do db writing
          return