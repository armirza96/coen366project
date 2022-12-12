import bitarray

class packet:
        
    def __init__(self, max_bits : int, fill : bool = False, *args) -> None:
      
        self.body = bitarray.bitarray(max_bits)
        self.size = max_bits
        self.body.setall(0)
        if fill:
            self.body.fill()
            self.size = len(self.body)


    def __call__(self, val : str) -> 'packet':
      
        if len(val) != self.size:
            raise ValueError("Incorrect size provided")

        self.body = bitarray.bitarray(val)
        return self

    def value(self) -> bitarray.bitarray:
    
        return self.body

    def to_bytes(self) -> bytes:
       
        return self.body.tobytes()

    def set_size(self, val: int) -> None:
        
        self.body = bitarray.bitarray(val)
        self.body.clear()
        self.size = val

    def __str__(self) -> str:
        return self.body.to01()

    def __repr__(self) -> str:
        return self.body.to01()

    