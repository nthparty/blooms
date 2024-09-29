"""
Lightweight Bloom filter data structure derived from the built-in
:obj:`bytearray` type.
"""
from __future__ import annotations
from typing import Union, Callable, Iterable
import doctest
import collections.abc
import base64

class blooms(bytearray):
    """
    Bloom filter data structure with support for common operations such as
    insertion (using :obj:`~blooms.__imatmul__`), membership (using
    :obj:`~blooms.__rmatmul__`), union (using :obj:`~blooms.__or__`), and
    containment (using :obj:`~blooms.issubset`).

    >>> b = blooms(4)

    It is the responsibility of the user of the library to hash and truncate
    the bytes-like object being inserted. Only those bytes that remain after
    truncation contribute to the object's membership within the instance.

    >>> from hashlib import sha256
    >>> x = 'abc' # Value to insert.
    >>> h = sha256(x.encode()).digest() # Hash of value.
    >>> t = h[:2] # Truncated hash.
    >>> b @= t # Insert the value into the Bloom filter.
    >>> b.hex()
    '00000004'

    When testing whether a bytes-like object is a member of an instance,
    the same hashing and truncation operations should be applied.

    >>> sha256('abc'.encode()).digest()[:2] @ b
    True
    >>> sha256('xyz'.encode()).digest()[:2] @ b
    False

    A particular sequence of a hashing operation followed by a truncation operation
    can be encapsulated within a user-defined class derived from the :obj:`blooms`
    class, wherein the default insertion method :obj:`~blooms.__imatmul__` and
    membership method :obj:`~blooms.__rmatmul__` are overloaded. The static method
    :obj:`~blooms.specialize` makes it possible to define such a derived class concisely
    (without resorting to Python's class definition syntax).

    For a given :obj:`blooms` instance, the :obj:`~blooms.saturation` method returns a
    :class:`float <float>` value between ``0.0`` and ``1.0`` that is influenced by the
    number of bytes-like objects that have been inserted so far into that instance.
    This value represents an upper bound on the rate with which false positives will
    occur when testing bytes-like objects (of the specified length) for membership
    within the instance.

    >>> b = blooms(32)
    >>> from secrets import token_bytes
    >>> for _ in range(8):
    ...     b @= token_bytes(4)
    >>> b.saturation(4) < 0.1
    True

    It is also possible to use the :obj:`~blooms.capacity` method to obtain an
    approximate maximum capacity of a :obj:`blooms` instance for a given saturation
    limit. For example, the output below indicates that a saturation of ``0.05`` will
    likely be reached after more than ``28`` insertions of bytes-like objects of length
    ``8``.

    >>> b = blooms(32)
    >>> b.capacity(8, 0.05)
    28
    """
    LENGTH_MAX: int = 256 ** 4
    """Maximum permitted length for an instance."""

    def __init__(self, *args, **kwargs):
        """
        Create and initialize a new :obj:`blooms` instance.

        >>> b = blooms(1)
        >>> b @= bytes([0])
        >>> bytes([0]) @ b
        True
        >>> bytes([1]) @ b
        False

        Any approach for creating an instance of the built-in :obj:`bytearray` class
        can also be used to create an instance of this class.

        >>> b = blooms(range(256))
        >>> bytes([1]) @ b
        False
        >>> b = blooms(b'abc')
        >>> bytes([0]) @ b
        True

        An instance can be of any non-zero length. This method checks that the instance
        has a valid size.

        >>> b = blooms()
        Traceback (most recent call last):
          ...
        ValueError: instance must have an integer length greater than zero
        >>> b = blooms(0)
        Traceback (most recent call last):
          ...
        ValueError: instance must have an integer length greater than zero
        >>> b = blooms(256 ** 4 + 1)
        Traceback (most recent call last):
          ...
        ValueError: instance length cannot exceed 4294967296
        """
        super().__init__(*args, **kwargs)

        if len(self) == 0:
            raise ValueError('instance must have an integer length greater than zero')

        if len(self) >= self.LENGTH_MAX + 1:
            raise ValueError('instance length cannot exceed ' + str(self.LENGTH_MAX))

    def __imatmul__(
            self: blooms,
            argument: Union[bytes, bytearray, Iterable[Union[bytes, bytearray]]]
        ) -> blooms:
        """
        Insert a bytes-like object (or an iterable of bytes-like objects)
        into this instance.

        :param argument: Object or objects to insert into this instance.

        This method provides a concise way to insert objects into an instance.
        This method modifies the instance for which it is invoked.

        >>> b = blooms(100)
        >>> b @= bytes([1, 2, 3])
        >>> b = blooms(100)
        >>> b @= (bytes([i, i + 1, i + 2]) for i in range(10))
        >>> b = blooms(100)

        Any attempt to insert an object that has an unsupported type raises an
        exception.

        >>> b @= 123
        Traceback (most recent call last):
          ...
        TypeError: supplied argument must be a bytes-like object or an iterable
        >>> b @= [bytes([4, 5, 6]), 123]
        Traceback (most recent call last):
          ...
        TypeError: item in supplied iterable must be a bytes-like object

        Note that when an iterable is supplied, the effects of all successful insertions
        (that occurred before the exception) remain.

        >>> bytes([4, 5, 6]) @ b
        True
        """
        if not isinstance(argument, (bytes, bytearray, collections.abc.Iterable)):
            raise TypeError(
                'supplied argument must be a bytes-like object or an iterable'
            )

        bss = [argument] if isinstance(argument, (bytes, bytearray)) else iter(argument)
        for bs in bss:
            if not isinstance(bs, (bytes, bytearray)):
                raise TypeError('item in supplied iterable must be a bytes-like object')

            bs = getattr(type(self), '_encode')(bs) if hasattr(self, '_encode') else bs
            for i in range(0, len(bs), 4):
                index = int.from_bytes(bs[i:i + 4], 'little')
                (index_byte, index_bit) = (index // 8, index % 8)
                self[index_byte % len(self)] |= 2**index_bit

        return self

    def __rmatmul__(
            self: blooms,
            argument: Union[bytes, bytearray]
        ) -> bool:
        """
        Check whether a bytes-like object appears in this instance.

        :param argument: Object to be used in querying this instance.

        A :obj:`blooms` instance never returns a false negative when queried
        using this method, but may return a false positive.

        >>> b = blooms(100)
        >>> b @= bytes([1, 2, 3])
        >>> bytes([1, 2, 3]) @ b
        True
        >>> bytes([4, 5, 6]) @ b
        False
        >>> b = blooms(1)
        >>> b @= bytes([0])
        >>> bytes([8]) @ b
        True

        The bytes-like object of length zero is a member of every :obj:`blooms`
        instance.

        >>> b = blooms(1)
        >>> bytes() @ b
        True

        If the supplied argument is not a bytes-like object, an exception is
        raised.

        >>> 123 @ b
        Traceback (most recent call last):
          ...
        TypeError: supplied argument must be a bytes-like object
        """
        if not isinstance(argument, (bytes, bytearray)):
            raise TypeError('supplied argument must be a bytes-like object')

        argument = (
            getattr(type(self), '_encode')(argument)
            if hasattr(self, '_encode') else
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

        :param other: Instance to use for the union operation.

        This method creates a new :obj:`blooms` instance based on two existing
        instances.

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

        This operation is only defined on instances that have equivalent
        lengths.

        >>> b0 | b1
        Traceback (most recent call last):
          ...
        ValueError: instances must have equivalent lengths
        >>> b0 | 123
        Traceback (most recent call last):
          ...
        TypeError: supplied argument must be a blooms instance
        """
        if not isinstance(other, blooms):
            raise TypeError('supplied argument must be a blooms instance')

        if len(self) != len(other):
            raise ValueError('instances must have equivalent lengths')

        return blooms([s | o for (s, o) in zip(self, other)])

    def issubset(self: blooms, other: blooms) -> bool:
        """
        Determine whether this instance represents a subset of another
        instance.

        :param other: Instance for which to check the subset relationship.

        Note that the subset relationship being checked is between the
        sets of all bytes-like objects that are accepted by each instance,
        regardless of whether they were explicitly inserted into an instance
        or not (*i.e.*, all bytes-like objects that are false positives are
        considered to be members).

        >>> b0 = blooms([0, 0, 1])
        >>> b1 = blooms([0, 0, 3])
        >>> b0.issubset(b1)
        True
        >>> b1.issubset(b0)
        False

        This operation is only defined on instances that have equivalent
        lengths.

        >>> b0 = blooms(100)
        >>> b1 = blooms(200)
        >>> b0.issubset(b1)
        Traceback (most recent call last):
          ...
        ValueError: instances must have equivalent lengths
        >>> b0.issubset(123)
        Traceback (most recent call last):
          ...
        TypeError: supplied argument must be a blooms instance
        """
        if not isinstance(other, blooms):
            raise TypeError('supplied argument must be a blooms instance')

        if len(self) != len(other):
            raise ValueError('instances must have equivalent lengths')

        return all(x <= y for (x, y) in zip(self, other))

    @classmethod
    def from_base64(cls, s: str) -> blooms:
        """
        Convert a Base64 UTF-8 string representation into an instance.

        :param s: Base64 UTF-8 string representation of an instance.

        This method creates a new instance based on the supplied string.

        >>> b = blooms(100)
        >>> b @= bytes([1, 2, 3])
        >>> b = blooms.from_base64(b.to_base64())
        >>> bytes([1, 2, 3]) @ b
        True
        >>> bytes([4, 5, 6]) @ b
        False

        If a non-string input is supplied, an exception is raised.

        >>> blooms.from_base64(123)
        Traceback (most recent call last):
          ...
        TypeError: supplied argument must be a string
        """
        if not isinstance(s, str):
            raise TypeError('supplied argument must be a string')

        ba = bytearray.__new__(cls)
        ba.extend(base64.standard_b64decode(s))
        return ba

    def to_base64(self: blooms) -> str:
        """
        Convert this instance to a Base64 UTF-8 string representation.

        >>> isinstance(blooms(100).to_base64(), str)
        True
        """
        return base64.standard_b64encode(self).decode('utf-8')

    def saturation(self: blooms, length: int) -> float:
        """
        Return the approximate saturation of this instance as a value between
        ``0.0`` and ``1.0`` (assuming that all bytes-like objects that have been
        or will be inserted have the specified length).

        :param length: Length of bytes-like objects in queries.

        The approximation is an upper bound on the true saturation, and its
        accuracy degrades as the number of insertions approaches the value
        ``len(self) // 8``.

        >>> b = blooms(32)
        >>> b.saturation(4)
        0.0
        >>> from secrets import token_bytes
        >>> for _ in range(8):
        ...     b @= token_bytes(4)
        >>> b.saturation(4) < 0.1
        True
        >>> b.saturation(-1)
        Traceback (most recent call last):
          ...
        ValueError: length must be nonnegative
        >>> b.saturation('abc')
        Traceback (most recent call last):
          ...
        TypeError: length must be an integer

        The saturation of an instance can be interpreted as an upper bound on
        the rate at which false positives can be expected when querying the
        instance with bytes-like objects that have the specified length.
        """
        if not isinstance(length, int):
            raise TypeError('length must be an integer')

        if length < 0:
            raise ValueError('length must be nonnegative')

        # This implementation converts into a 32-bit integer each subsequence of
        # four bytes within a bytes-like object being inserted. Thus, each four-byte
        # portion contributes to one bit position in an instance. The terms below
        # capture this and are used throughout the formula for saturation.
        (exp_div, exp_mod) = ((length // 4), (1 if length % 4 > 0 else 0))

        # The numerator represents an upper bound on the number of insertions
        # that may have occurred to obtain the bit pattern in this instance.
        numerator = sum(bin(b).count('1') for b in self) ** (exp_div + exp_mod)

        # The denominator represents the total number of possible combinations
        # of bits that can be set to ``1`` when an insertion occurs.
        denominator = (
            # Each bit obtained from the bytes-like object being inserted
            # can appear in any of the bit positions within this instance.
            ((8 * len(self)) ** exp_div)
            *
            # Include additional factor in case there are bytes that do not
            # form a complete 32-bit integer, but still contribute another bit
            # when performing an insertion. Using the :obj:`min` operator, we
            # compensate for cases in which the length of this instance also
            # is larger than the range of possible positions for this bit that
            # can be derived from the right-most ``length % 4`` bytes.
            (min(8 * len(self), max(256, len(self) ** 2) * (length % 4)) ** exp_mod)
        )

        return numerator / denominator

    def capacity(self: blooms, length: int, saturation: float) -> Union[int, float]:
        """
        Return this instance's approximate capacity: the number of bytes-like
        objects of the specified length that can be inserted into an empty version
        of this instance before the specified saturation is likely to be reached.

        :param length: Length of bytes-like objects in queries.
        :param saturation: Saturation with respect to which to estimate capacity.

        This method is defined for nonnegative length and saturation values.

        >>> b = blooms(32)
        >>> b.capacity(8, 0.05)
        28
        >>> b.capacity(12, 0.05)
        31
        >>> b.capacity(-1, 0)
        Traceback (most recent call last):
          ...
        ValueError: length must be nonnegative
        >>> b.capacity('abc', 0)
        Traceback (most recent call last):
          ...
        TypeError: length must be an integer
        >>> b.capacity(0, -1)
        Traceback (most recent call last):
          ...
        ValueError: saturation must be nonnegative
        >>> b.capacity(0, 'abc')
        Traceback (most recent call last):
          ...
        TypeError: saturation must be an integer or a floating-point number

        The capacity of an instance is not bounded for a saturation of ``1.0`` or
        for bytes-like objects of length zero.

        >>> b.capacity(0, 0.1)
        inf
        >>> b.capacity(4, 1.0)
        inf

        Note that **capacity is independent of the number of insertions into this
        instance that have occurred**. It is the responsibility of the user to keep
        track of the number of bytes-like objects that have been inserted into an
        instance.
        """
        if not isinstance(length, int):
            raise TypeError('length must be an integer')

        if length < 0:
            raise ValueError('length must be nonnegative')

        if not isinstance(saturation, (int, float)):
            raise TypeError('saturation must be an integer or a floating-point number')

        if saturation < 0:
            raise ValueError('saturation must be nonnegative')

        # Special cases are handled separately, ensuring there are no outliers among
        # the outputs (in terms of accuracy) over the range of these special cases.
        if length == 0 or saturation >= 1.0:
            return float('inf')

        # This implementation converts into a 32-bit integer each subsequence of
        # four bytes within a bytes-like object being inserted. Thus, each four-byte
        # portion contributes to one bit position in an instance. The terms below
        # capture this and are used throughout the formula for capacity.
        (exp_div, exp_mod) = ((length // 4), (1 if length % 4 > 0 else 0))

        # In the :obj:`saturation` method, we have that
        # ``saturation == numerator / denominator``. It then follows that
        # ``saturation * denominator == numerator``. It is thus sufficient to compute
        # the numerator and then derive a worst-case capacity bound from the number
        # of non-zero bits (as represented by the numerator).
        denominator = (
            ((8 * len(self)) ** exp_div)
            *
            (min(8 * len(self), max(256, len(self) ** 2) * (length % 4)) ** exp_mod)
        )
        return int(
            ((saturation * denominator) ** (1 / (exp_div + exp_mod)))
            /
            ((length // 4) + exp_mod)
        )

    @staticmethod
    def specialize(
            name: str,
            encode: Callable[[Union[bytes, bytearray]], Union[bytes, bytearray]]
        ) -> type:
        """
        Return a class derived from :obj:`blooms` that uses
        the supplied encoding for members.

        :param name: Name of derived class being defined.
        :param encode: Custom encoding function that the derived class will use.

        The supplied encoding function must accept one bytes-like object as an
        input and must return a bytes-like object as an output.

        >>> from hashlib import sha256
        >>> encode = lambda x: sha256(x).digest()[:2]
        >>> blooms_custom = blooms.specialize(name='blooms_custom', encode=encode)
        >>> b = blooms_custom(4)
        >>> b @= bytes([1, 2, 3])
        >>> bytes([1, 2, 3]) @ b
        True
        """
        return type(name, (blooms,), {'_encode': encode})

if __name__ == '__main__':
    doctest.testmod() # pragma: no cover
