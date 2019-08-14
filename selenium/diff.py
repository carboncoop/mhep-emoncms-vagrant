import io
import json

from collections import OrderedDict


def main():
    with io.open('test_assessment.json', 'r') as f:
        expected_assessment = json.load(f)
        del expected_assessment['scenario1']

    with io.open('test_data/got_assessment.json', 'r') as f:
        got_assessment = json.load(f)

    expected_flat = sort(flatten_json(expected_assessment))
    got_flat = sort(flatten_json(got_assessment))

    with io.open('test_data/expected_assessment.txt', 'w') as f:
        for k, v in expected_flat:
            f.write('{} = {}\n'.format(k, v))

    with io.open('test_data/got_assessment.txt', 'w') as f:
        for k, v in got_flat:
            f.write('{} = {}\n'.format(k, v))


def sort(od):
    return sorted(od.items(), key=lambda kv: kv[0].upper())


def flatten_json(nested_json):
    """
        Flatten json object with nested keys into a single level.
        Args:
            nested_json: A nested json object.
        Returns:
            The flattened json object if successful, None otherwise.
    """
    out = OrderedDict()

    def flatten(x, name=''):
        if type(x) is dict:
            for key in x:
                flatten(x[key], name + '.' + key)
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + '[' + str(i) + ']')
                i += 1
        else:
            out[name[1:]] = x

    flatten(nested_json)
    return out


if __name__ == '__main__':
    main()
