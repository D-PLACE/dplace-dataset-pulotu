"""

"""
import textwrap
import itertools
import collections

from clldutils.path import git_describe
from csvw.dsv import UnicodeWriter

from cldfbench_pulotu import Dataset

#
# FIXME: add codebook!
#
def run(args):
    ds = Dataset()
    cldf = ds.cldf_reader()
    cultures = {r['ID']: r for r in cldf['LanguageTable']}
    variables = collections.OrderedDict([
        (r['ID'], (r['Simplified_Name'] or r['Name']).replace(' ', '_'))
        for r in cldf['ParameterTable']])

    with UnicodeWriter(ds.dir / 'dist' / 'Pulotu_Database.txt', delimiter='\t') as w:
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

    codebook = [
        """# Pulotu: Dataset in tab-delimited txt format

The file [Pulotu_Database.txt](Pulotu_Database.txt) provides the [Pulotu data](../cldf) as
tab-delimited, single CSV file, with cultures as rows and variables as columns. A description
of the variables follows below.

""",
    ]
    codes = {
        pid: list(codes) for pid, codes in
        itertools.groupby(cldf['CodeTable'], lambda r: r['Parameter_ID'])}
    for cat, ps in itertools.groupby(cldf['ParameterTable'], lambda r: r['Category']):
        codebook.extend(['', '## {}'.format(cat)])
        for p in ps:
            codebook.extend(['', '### v{}: {}'.format(p['ID'], p['Name'])])
            if p['Description']:
                codebook.append('')
                codebook.extend(textwrap.wrap(p['Description']))

            if p['ID'] in codes:
                codebook.append('')
                for c in codes[p['ID']]:
                    codebook.append('- ({}) {}'.format(c['Name'], c['Description']))
                codebook.append('- (?) Missing data')

    ds.dir.joinpath('dist', 'README.md').write_text('\n'.join(codebook), encoding='utf8')
