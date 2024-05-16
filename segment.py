from configs import CFG, Config
config = Config.from_json(CFG)

class TCPSegment:
    def __init__(self, src_port: int, dest_port: int, data: bytes):

        assert len(data) <= config.constants.MAX_TCP_SEGMENT_DATA_SIZE, print(
            f"MAXIMUM DATA SIZE OF A TCP SEGMENT IS {config.constants.MAX_TCP_SEGMENT_DATA_SIZE}"
        )

        self.src_port = src_port
        self.dest_port = dest_port
        self.length = len(data)
        self.data = data


