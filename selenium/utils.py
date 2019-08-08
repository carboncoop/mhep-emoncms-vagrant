from collections import OrderedDict
import lxml.html



def flatten_summary_table(html):
    root = lxml.html.fromstring(html)

    scenarios = [s.text for s in root.xpath('//th')[1:]]
    # scenarios is e.g. ['master', 'scenario1']

    print(scenarios)

    section_name = 'NOSECTION'

    out = OrderedDict()

    for tr in root.xpath('//table//tr')[1:]:

        cols = [td.text_content().strip() for td in tr.xpath('./td')]

        if all(c == '' for c in cols):  # skip blank row
            continue

        if is_section_row(cols):
            section_name = cols[0]
        else:
            # e.g. ["heating demand", "1.2", '3.4']
            data_key, data_values = cols[0], cols[1:]

            for scenario, data_value in zip(scenarios, data_values):
                key = '{} | {} | {}'.format(scenario, section_name, data_key)
                value = data_value

                out[key] = value

    return out


def is_section_row(columns):
    """
    return True if the first column has text and the remaining n are empty

    e.g. ['Totals', '', ''] # this is a section row

    comes from a row like this:
    <tr>
      <td><b>Totals</b></td>
      <td></td>
      <td></td>
    </tr>
    """

    return columns[0] != '' and all(column == '' for column in columns[1:])
