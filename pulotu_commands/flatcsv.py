"""

"""
import itertools
import collections

from clldutils.path import git_describe
from csvw.dsv import UnicodeWriter

from cldfbench_pulotu import Dataset


def run(args):
    ds = Dataset()
    cldf = ds.cldf_reader()
    cultures = {r['ID']: r for r in cldf['LanguageTable']}
    variables = collections.OrderedDict([
        (r['ID'], (r['Simplified_Name'] or r['Name']).replace(' ', '_'))
        for r in cldf['ParameterTable']])

    with UnicodeWriter(
            ds.dir / 'Pulotu_Database_{}.txt'.format(git_describe(ds.dir)), delimiter='\t') as w:
        header = ['Culture', 'Culture_Notes', 'Glottocode']
        for vid, vname in variables.items():
            header.extend(['v{}.{}'.format(vid, vname), 'v{}.Source'.format(vid)])
        w.writerow(header)
        for lid, values in itertools.groupby(
            sorted(cldf['ValueTable'], key=lambda v: v['Language_ID']),
            lambda v: v['Language_ID']
        ):
            values = {v['Parameter_ID']: v for v in values}
            row = [
                cultures[lid]['Name'],
                cultures[lid]['Comment'],
                cultures[lid]['Glottocode'],
            ]
            for vid in variables:
                v = values.get(vid, {})
                row.extend([v.get('Value'), '; '.join(v.get('Source', []))])
            w.writerow(row)
