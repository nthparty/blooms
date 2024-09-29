"""
Test suite containing functional unit tests for specific methods of
the exported class.
"""
from unittest import TestCase
import itertools
import random

from blooms import blooms

def randbytes(n: int) -> bytes:
    """
    Get pseudorandom bytes-like object of specified size using
    in a manner that is compatible across Python versions.
    """
    return (
        random.randbytes(n)
        if hasattr(random, 'randbytes') else
        bytes(random.getrandbits(8) for _ in range(n))
    )

def saturation_from_data(b: blooms, length: int) -> float:
    """
    Compute the saturation of an instance into which bytes-like
    objects of the specified length have been inserted.
    """
    (members, candidates) = (0, 2 ** 16)
    for _ in (range(candidates)):
        members += 1 if randbytes(length) @ b else 0
    return members / candidates

class Test_blooms_methods(TestCase):
    """
    Container for tests of the exported class.
    """

# Create an ensemble of distinct saturation and capacity test methods (within
# the container class) for different combinations of parameters. This is done
# in order to provide more granular progress and result feedback.
for blooms_length in [2 ** k for k in range(0, 21, 2)]:
    # A bytes-like object having length ``64`` represents
    # a digest from an invocation of SHA-512.
    for item_length in itertools.chain(range(8), range(8, 64, 13)):
        # The saturation tests for this combination of lengths are encapsulated in the
        # methods below.
        def method_for_saturation_test(
                test: Test_blooms_methods,
                blooms_len: int = blooms_length,
                item_len: int = item_length
            ):
            """
            Test the accuracy of the approximations returned by the method for
            calculating the saturation of an instance.
            """
            # The number of insertions is bounded above by ``len(instance) // 8``, based
            # on the known limitations of Bloom filters. Also, avoid tests in which the
            # number of insertions exceeds the number of distinct bytes-like objects of
            # the current length.
            for item_count in [
                2 ** k
                for k in range(2, blooms_len.bit_length() - 2)
                if 2 ** k < 256 ** item_len
            ]:
                # Set the random seed at this point to ensure that tests are deterministic
                # (and consistent regardless of the order in which they are executed).
                random.seed(blooms_len + item_len + item_count)

                # Populate an instance with random data.
                b = blooms(blooms_len // 8)
                b @= [randbytes(item_len) for _ in range(item_count)]

                # If the instance at this length is close to saturation, there
                # is no need to try larger quantities of insertions.
                saturation_reference = saturation_from_data(b, item_len)
                if saturation_reference > 0.75:
                    break

                # The approximation returned by the method should be within the expected
                # range. It should also be at least as large as the saturation observed
                # using random data. Its error should be bounded reasonably well (within
                # 1% of the saturation observed using random data).
                saturation_method = b.saturation(item_len)
                error = saturation_method - saturation_reference
                test.assertTrue(0.0 <= saturation_method <= 1.0)
                test.assertTrue(error < 0.01)

        # Add the method to the container class.
        setattr(
            Test_blooms_methods,
            '_'.join([
                'test_saturation',
                'blooms_len', str(blooms_length),
                'item_len', str(item_length)
            ]),
            method_for_saturation_test
        )

        # The capacity tests for this combination of lengths are encapsulated in the
        # methods below.
        def method_for_capacity_test(
                test: Test_blooms_methods,
                blooms_len: int = blooms_length,
                item_len: int = item_length
            ):
            """
            Test the accuracy of the approximations returned by the method for
            calculating the capacity of an instance.
            """
            # The number of insertions is bounded above by ``len(instance) // 8``, based
            # on the known limitations of Bloom filters. Also, avoid tests in which the
            # number of insertions exceeds the number of distinct bytes-like objects of
            # the current length.
            for item_count in [
                2 ** k
                for k in range(2, blooms_len.bit_length() - 2)
                if 2 ** k < 256**item_len
            ]:
                # Set the random seed at this point to ensure that tests are deterministic
                # (and consistent regardless of the order in which they are executed).
                random.seed(blooms_len + item_len + item_count)

                # Populate an instance with random data.
                b = blooms(blooms_len // 8)
                b @= [randbytes(item_len) for _ in range(item_count)]

                # The capacity method is tested only for a range of saturations that
                # would reasonably be of interest to users.
                saturation = b.saturation(item_len)
                if saturation > 0.3:
                    break

                # The approximate capacity for the observed saturation (given the
                # number of insertions) should be with a reasonable factor of the
                # actual number of insertions performed.
                capacity = b.capacity(item_len, saturation)
                test.assertTrue(1.0 <= (item_count / capacity) <= 4.0)

        # Add the method to the container class.
        setattr(
            Test_blooms_methods,
            '_'.join([
                'test_capacity',
                'blooms_len', str(blooms_length),
                'item_len', str(item_length)
            ]),
            method_for_capacity_test
        )
