"""
Test suite containing functional unit tests for specific methods of
the exported class.
"""
from unittest import TestCase
import random

from blooms import blooms

# Set the random seed to ensure that tests are deterministic.
random.seed(0)

def saturation_from_data(b: blooms, length: int) -> float:
    """
    Compute the saturation of an instance into which bytes-like
    objects of the specified length have been inserted.
    """
    (members, candidates) = (0, 2 ** 16)
    for _ in (range(candidates)):
        members += 1 if random.randbytes(length) @ b else 0
    return members / candidates

class Test_blooms_methods(TestCase):
    """
    Container for tests of the exported class.
    """

# Create an ensemble of distinct saturation test methods (within the container
# class) for different combinations of parameters. This is done in order to
# provide more granular progress and result feedback.
for blooms_length in [2 ** k for k in range(2, 21, 2)]:
    # A bytes-like object having length ``64`` represents
    # a digest from an invocation of SHA-512.
    for item_length in range(8, 64, 13):
        # The tests for this combination of lengths are encapsulated in the
        # method below.
        def method_for_saturation_test(test, blooms_len=blooms_length, item_len=item_length):
            """
            Test the accuracy of the approximations returned by the method for
            calculating the saturation of an instance.
            """
            # The number of insertions is bounded above by ``len(instance) // 8``,
            # based on the known limitations of Bloom filters.
            for item_count in [2 ** k for k in range(2, blooms_len.bit_length() - 2)]:

                # Populate an instance with random data.
                b = blooms(blooms_len // 8)
                for _ in range(item_count):
                    b @= random.randbytes(item_len)

                # The approximation returned by the method should always be
                # at least as large as the saturation observed using random data.
                # Its error should be bounded reasonably well (within 1% of the
                # saturation observed using random data).
                saturation_reference = saturation_from_data(b, item_len)
                saturation_method = b.saturation(item_len)
                error = saturation_method - saturation_reference
                test.assertTrue(error < 0.01)

                # If the instance at this length is close to saturation, there
                # is no need to try larger quantities of insertions.
                if saturation_reference > 0.75:
                    break

        # Add the method to the container class.
        setattr(
            Test_blooms_methods,
            "_".join([
                "test_saturation",
                "blooms_len", str(blooms_length),
                "item_len", str(item_length)
            ]),
            method_for_saturation_test
        )

# Create an ensemble of distinct capacity test methods (within the container
# class) for different combinations of parameters. This is done in order to
# provide more granular progress and result feedback.
for blooms_length in [2 ** k for k in range(2, 21, 2)]:
    # A bytes-like object having length ``64`` represents
    # a digest from an invocation of SHA-512.
    for item_length in range(8, 64, 13):
        # The tests for this combination of lengths are encapsulated in the
        # method below.
        def method_for_capacity_test(test, blooms_len=blooms_length, item_len=item_length):
            """
            Test the accuracy of the approximations returned by the method for
            calculating the capacity of an instance.
            """
            # The number of insertions is bounded above by ``len(instance) // 8``,
            # based on the known limitations of Bloom filters.
            for item_count in [2 ** k for k in range(2, blooms_len.bit_length() - 2)]:

                # Populate an instance with random data.
                b = blooms(blooms_len // 8)
                for _ in range(item_count):
                    b @= random.randbytes(item_len)

                # The approximate capacity for the observed saturation (given the
                # number of insertions) should be with a reasonable factor of the
                # actual number of insertions performed.
                saturation = b.saturation(item_len)
                capacity = b.capacity(item_len, saturation)
                test.assertTrue(1.0 <= (item_count / capacity) <= 4.0)

                # If the instance at this length is close to saturation, there
                # is no need to try larger quantities of insertions.
                if saturation > 0.2:
                    break

        # Add the method to the container class.
        setattr(
            Test_blooms_methods,
            "_".join([
                "test_capacity",
                "blooms_len", str(blooms_length),
                "item_len", str(item_length)
            ]),
            method_for_capacity_test
        )
