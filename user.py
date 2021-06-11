import util, json

class User:
    users = {}
    def __init__(self, id, ip, websocket) -> None:
        self.name = "anon_" + util.generate_uid(ip)[10:]
        self.id = id
        self.raw_ip = ip
        self.uid = util.generate_uid(ip)
        self.websocket = websocket
        self.room = None
        self.logged_in = False
        self.mod = False
        self.owner = False
    
    def setMod(self, boolean: bool):
        self.mod = boolean
    
    def setOwner(self, boolean: bool):
        self.owner = boolean
    
    def setRoom(self, name: str):
        self.room = name
    
    def setName(self, name: str):
        self.name = name
    
    def setLoggedIn(self, boolean: bool):
        self.logged_in = boolean
    
    def set(self):
        self.users[self.id] = self
    
    def get(self, id: str):
        if id in self.users:
            return self.users[id]

    def remove(self, id: str = None):
        if id:
            if id in self.users:
                del self.users[id]
        else:
            del self.users[self.id]

    def write(self, **commands):
        data = json.dumps(commands).encode()
        self.websocket.sendMessage(data)