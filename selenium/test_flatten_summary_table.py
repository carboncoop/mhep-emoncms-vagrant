import io
import json

from utils import flatten_summary_table


def test_flatten_summary_table():
    with io.open('test_data/example_summary_table.html', 'r') as f:
        out = flatten_summary_table(f.read())

    with io.open('test_data/example_summary_table.json', 'r') as f:
        expected = json.load(f)

        assert out == expected
