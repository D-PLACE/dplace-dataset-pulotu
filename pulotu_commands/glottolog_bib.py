"""
Create a bib file suitable for inclusion into Glottolog as refprovider

Augment Pulotu bib with
- hhtype = {ethnographic}
- lgcode = {<culture name> [glottocode]}
"""
import collections

from cldfbench_pulotu import Dataset
from pycldf.sources import Sources

def run(args):
    cldf = Dataset().cldf_reader()
    langs = {r['id']: r for r in cldf.iter_rows('LanguageTable', 'id', 'name', 'glottocode')}
    citations = collections.defaultdict(set)
    for r in cldf.iter_rows('ValueTable', 'source', 'languageReference'):
        for ref in r['source']:
            sid, _ = Sources.parse(ref)
            citations[sid].add(r['languageReference'])
    for src in cldf.sources:
        if src.id in citations:
            src['hhtype'] = 'ethnographic'
            src['lgcode'] = '; '.join([
                '{} [{}]'.format(langs[lid]['name'], langs[lid]['glottocode'])
                for lid in sorted(citations[src.id])])
        print(src.bibtex())
