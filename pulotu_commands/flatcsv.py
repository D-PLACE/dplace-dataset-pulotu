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

    with UnicodeWriter(
            ds.dir / 'dist' / 'Pulotu_Database_{}.txt'.format(git_describe(ds.dir)), delimiter='\t') as w:
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
        """# Pulotu Codebook 
Updated:  30/6/2015 
Pulotu:  Database of Austronesian Supernatural Belief and Practice 
Authors:  Joseph Watts, Oliver Sheehan, Simon J. Greenhill, Stephanie Gomes-Ng, 
Quentin D. Atkinson, Joseph Bulbulia and Russell D. Gray 
Website: www.pulotu.com
""",
        #'## Section 1: Indigenous Time Focus'
        #'### v1.Subdee',
        # info
        # ul of possible values
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

    ds.dir.joinpath('dist', 'Pulotu_Database_{}_codebook.md'.format(git_describe(ds.dir))).write_text(
        '\n'.join(codebook),
        encoding='utf8')
