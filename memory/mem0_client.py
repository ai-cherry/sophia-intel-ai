from mem0 import Memory

class Mem:
    def __init__(self, namespace: str):
        self.ns = namespace
        self.client = Memory()

    def remember(self, text: str, **meta):
        return self.client.add({"text": text, "meta": {"ns": self.ns, **meta}})

    def recall(self, query: str, k: int = 5):
        return self.client.search(query, limit=k, filters={"meta.ns": self.ns})