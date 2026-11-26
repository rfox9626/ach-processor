from ach.services import chunked


def test_chunked_uneven():
    assert chunked(list(range(25)), 10) == [
        list(range(0, 10)),
        list(range(10, 20)),
        list(range(20, 25)),
    ]


def test_chunked_exact():
    assert chunked(list(range(20)), 10) == [list(range(0, 10)), list(range(10, 20))]


def test_chunked_empty():
    assert chunked([], 10) == []
