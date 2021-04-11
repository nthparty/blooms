"""Bloom filter data structure.

Lightweight Bloom filter data structure derived from the
built-in bytearray type.
"""

from __future__ import annotations
import doctest

class blooms(bytearray):
    """
    Bloom filter data structure.
    """
    def __imatmul__(self: blooms, bs: bytes) -> blooms:
        """
        Insert a bytes-like object into this instance.

        >>> b = blooms(100)
        >>> b @= bytes([1, 2, 3])
        """
        for i in range(0, len(bs), 4):
            index = int.from_bytes(bs[i:i + 4], 'little')
            (index_byte, index_bit) = (index // 8, index % 8)
            self[index_byte % len(self)] |= 2**index_bit
        return self

    def __rmatmul__(self: blooms, bs: bytes) -> bool:
        """
        Check whether a bytes-like object appears in this instance.

        >>> b = blooms(100)
        >>> b @= bytes([1, 2, 3])
        >>> bytes([1, 2, 3]) @ b
        True
        >>> bytes([4, 5, 6]) @ b
        False
        """
        for i in range(0, len(bs), 4):
            index = int.from_bytes(bs[i:i + 4], 'little')
            (index_byte, index_bit) = (index // 8, index % 8)
            if ((self[index_byte % len(self)] >> index_bit) % 2) != 1:
                return False
        return True


    def __or__(self: blooms, other: blooms) -> blooms:
        """
        Take the union of two instances.

        >>> b0 = blooms(100)
        >>> b0 @= bytes([1, 2, 3])
        >>> b1 = blooms(100)
        >>> b1 @= bytes([4, 5, 6])
        >>> bytes([1, 2, 3]) @ (b0 | b1)
        True
        >>> bytes([4, 5, 6]) @ (b0 | b1)
        True
        >>> b0 = blooms(100)
        >>> b1 = blooms(200)
        >>> b0 | b1
        Traceback (most recent call last):
          ...
        ValueError: instances do not have equivalent lengths
        """
        if len(self) != len(other):
            raise ValueError('instances do not have equivalent lengths')

        return blooms([s | o for (s, o) in zip(self, other)])

if __name__ == "__main__":
    doctest.testmod()
