"""Bloom filter data structure.

Lightweight Bloom filter data structure derived from the
built-in bytearray type.
"""

from __future__ import annotations
from typing import Union
import doctest
from collections.abc import Iterable
import base64

class blooms(bytearray):
    """
    Bloom filter data structure.
    """
    @classmethod
    def from_base64(cls, s: str) -> blooms:
        """
        Convert a Base64 UTF-8 string representation into a blooms instance.

        >>> b = blooms(100)
        >>> b @= bytes([1, 2, 3])
        >>> b = blooms.from_base64(b.to_base64())
        >>> bytes([1, 2, 3]) @ b
        True
        >>> bytes([4, 5, 6]) @ b
        False
        """
        ba = bytearray.__new__(cls)
        ba.extend(base64.standard_b64decode(s))
        return ba

    def to_base64(self: blooms) -> str:
        """
        Convert to Base64 UTF-8 string representation.

        >>> b = blooms(100)
        >>> isinstance(b.to_base64(), str)
        True
        """
        return base64.standard_b64encode(self).decode('utf-8')

    def __imatmul__(self: blooms, argument: Union[bytes, Iterable]) -> blooms:
        """
        Insert a bytes-like object into this instance.

        >>> b = blooms(100)
        >>> b @= bytes([1, 2, 3])
        >>> b = blooms(100)
        >>> b @= (bytes([i, i + 1, i + 2]) for i in range(10))
        >>> b = blooms(100)
        >>> b @= 123
        Traceback (most recent call last):
          ...
        TypeError: supplied argument is not a bytes-like object and not iterable
        """
        if not isinstance(argument, (bytes, bytearray, Iterable)):
            raise TypeError('supplied argument is not a bytes-like object and not iterable')

        bss = [argument] if isinstance(argument, (bytes, bytearray)) else iter(argument)
        for bs in bss:
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
    doctest.testmod() # pragma: no cover
