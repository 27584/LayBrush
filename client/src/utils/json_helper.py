
import json
class Json:
    def __init__(self,content = None,path=None,load=False):
        self.path = path
        self.content = content
        if load:
            self.load()
    def save(self,path = None, indent=2):
        if not path:
            path = self.path
        if path and self.content:
            with open(path, 'w',encoding='utf-8') as load_f:
                load_f.write(json.dumps(self.content, ensure_ascii=False, indent=indent))
        else:
            return -1
    def load(self,path = None):
        if not path:
            path = self.path
        if path:
            with open(path, 'r',encoding='utf-8') as load_f:
                self.content = json.load(load_f)
        else:
            return -1
    def __str__(self):
        return json.dumps(self.content)