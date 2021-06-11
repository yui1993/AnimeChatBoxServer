import hashlib, random, config, re, bleach
from cryptography.fernet import Fernet
from usernames import is_safe_username

def isAllowed(text, max_len=10, min_len=3):
    if len(text) <=max_len:
        if len(text) < min_len:
            return False
    
    if text.find(".") > -1:
        return False
    
    return is_safe_username(text)

def _get_key(path):
    try:
        f = open(path, "rb")
        key  = f.read()
        f.close()
        return key
    except:
        key = Fernet.generate_key()
        f = open(path, "wb")
        f.write(key)
        f.close()
        return key

def generate_uid(string: str, hash=hashlib.sha3_512) -> str:
    string = f"^%$#!#$^&*({string})$&^hjvghfttf_".encode() 
    return hash(string).hexdigest() + "==hash"

def generate_id() -> str:
    string = "abcdefghijklmnopqrstuvwxyz1234567890!@#$%^&**(())(*&^$$$"
    upper_string = string.upper()
    string = string + upper_string
    l=[]
    b=[]
    for x in string:
        l.append(x)
        random.shuffle(l)
        h =  hashlib.sha512("".join(l).encode())
        b.append(h.hexdigest())
    return hashlib.sha3_512("".join(l).encode()).hexdigest() + '==id'

class FCipher:
    def __init__(self, path_to_key):
        self._data = Fernet(_get_key(path_to_key))
    
    def encrypt(self, data):
        return self._data.encrypt(data)
    
    def decrypt(self, data):
        return self._data.decrypt(data)

def filter(text):
    return bleach.clean(text, tags=config.allowed_tags, attributes=config.allowed_attrs, strip=False)


if __name__=="__main__":
    print(isAllowed(username))