"""Tools stubs for agno compatibility"""

class Tool:
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get('name', 'Tool')

class Neo4jTools:
    def __init__(self, *args, **kwargs):
        pass