import json
from datetime import datetime
from pathlib import Path

class ConversationLog:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conversations = self.load()
    
    def load(self):
        if self.path.exists():
            with open(self.path, 'r') as f:
                return json.load(f)
        return []
    
    def append(self, query, response):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response': response
        }
        self.conversations.append(entry)
        self.save()
    
    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self.conversations, f, indent=2)