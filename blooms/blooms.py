"""
Lightweight Bloom filter data structure derived from the
built-in ``bytearray`` type.
"""

from __future__ import annotations
from typing import Union, Callable
import doctest
from collections.abc import Iterable
import base64

class blooms(bytearray):
    """
    Bloom filter data structure.
    """
    def __imatmul__(self: blooms, argument: Union[bytes, bytearray, Iterable]) -> blooms:
        """
        Insert a bytes-like object (or an iterable of bytes-like objects)
        into this instance.

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
            raise TypeError(
                'supplied argument is not a bytes-like object and not iterable'
            )

        bss = [argument] if isinstance(argument, (bytes, bytearray)) else iter(argument)
        for bs in bss:
            bs = getattr(type(self), '_encode')(bs) if hasattr(self, '_encode') else bs
            for i in range(0, len(bs), 4):
                index = int.from_bytes(bs[i:i + 4], 'little')
                (index_byte, index_bit) = (index // 8, index % 8)
                self[index_byte % len(self)] |= 2**index_bit

        return self

    def __rmatmul__(self: blooms, argument: Union[bytes, bytearray, Iterable]) -> bool:
        """
        Check whether a bytes-like object appears in this instance.

        >>> b = blooms(100)
        >>> b @= bytes([1, 2, 3])
        >>> bytes([1, 2, 3]) @ b
        True
        >>> bytes([4, 5, 6]) @ b
        False
        """
        argument = (
            getattr(type(self), '_encode')(argument) \
            if hasattr(self, '_encode') else \
            argument
        )
        for i in range(0, len(argument), 4):
            index = int.from_bytes(argument[i:i + 4], 'little')
            (index_byte, index_bit) = (index // 8, index % 8)
            if ((self[index_byte % len(self)] >> index_bit) % 2) != 1:
                return False
        return True

    def __or__(self: blooms, other: blooms) -> blooms:
        """
        Return the union of this instance and another instance.

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

    def issubset(self: blooms, other: blooms) -> bool:
        """
        Determine whether this instance represents a subset of
        another instance. Note that the subset relationship being
        checked is between the sets of all bytes-like objects that
        are accepted by each instance, regardless of whether they
        were explicitly inserted into an instance or not (*i.e.*,
        all bytes-like objects that are false positives are
        considered to be members).

        >>> b0 = blooms([0, 0, 1])
        >>> b1 = blooms([0, 0, 3])
        >>> b0.issubset(b1)
        True
        >>> b1.issubset(b0)
        False
        >>> b0 = blooms(100)
        >>> b1 = blooms(200)
        >>> b0.issubset(b1)
        Traceback (most recent call last):
          ...
        ValueError: instances do not have equivalent lengths
        """
        if len(self) != len(other):
            raise ValueError('instances do not have equivalent lengths')

        return all(x <= y for (x, y) in zip(self, other))

    @classmethod
    def from_base64(cls, s: str) -> blooms:
        """
        Convert a Base64 UTF-8 string representation into an instance.

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
        Convert this instance to a Base64 UTF-8 string representation.

        >>> b = blooms(100)
        >>> isinstance(b.to_base64(), str)
        True
        """
        return base64.standard_b64encode(self).decode('utf-8')

    @staticmethod
    def specialize(name: str, encode: Callable) -> type:
        """
        Return a class derived from :obj:`blooms` that uses
        the supplied encoding for members.

        >>> from hashlib import sha256
        >>> encode = lambda x: sha256(x).digest()[:2]
        >>> blooms_custom = blooms.specialize(name='blooms_custom', encode=encode)
        >>> b = blooms_custom(4)
        >>> b @= bytes([1, 2, 3])
        >>> bytes([1, 2, 3]) @ b
        True
        """
        return type(name, (blooms,), {'_encode': encode})

if __name__ == "__main__":
    doctest.testmod() # pragma: no cover
