class SetModeRequest:
    def __init__(self, nodeId: int, mode: str, filename: str):
        self.node_id = nodeId
        self.mode = mode
        self.filename = filename
    
    def check_missing_fields(self):
        missing_fields = []
        if self.node_id is None:
            missing_fields.append('nodeId')
        if self.mode is None:
            missing_fields.append('mode')
        if self.filename is None:
            missing_fields.append('filename')
        
        return missing_fields
