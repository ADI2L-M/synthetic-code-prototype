from models.types import ProgrammingTask, TestCase


def lab_12_q2_task() -> ProgrammingTask:
    """Return the manually specified contract for Lab 12 Question 2."""
    return ProgrammingTask(
        id="Lab_12_Q2",
        name="Sum even and odd values",
        description=(
            "Return a tuple containing the sum of even values and the sum of "
            "odd values in a list of integers."
        ),
        function_name="get_sum_evens_odds",
        contexts=["T2", "list_processing"],
        functional_requirements=[
            "Accept a list of integers.",
            "Return a two-item tuple.",
            "The first item is the sum of even values.",
            "The second item is the sum of odd values.",
            "Return (0, 0) for an empty list.",
        ],
        test_cases=[
            TestCase(args=[[]], expected=[0, 0], expected_type="tuple"),
            TestCase(args=[[1, 2, 3, 4]], expected=[6, 4], expected_type="tuple"),
            TestCase(args=[[-5, -4, 0, 7]], expected=[-4, 2], expected_type="tuple"),
            TestCase(args=[[2, 2, 1, 1, 0]], expected=[4, 2], expected_type="tuple"),
        ],
    )
