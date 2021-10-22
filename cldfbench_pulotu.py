import re
import pathlib
import collections

from clldutils.text import split_text
from clldutils.misc import slug
from cldfbench import Dataset as BaseDataset, CLDFSpec

# The following variables go into LanguageTable, we want to be able to identify these by ID:
MD = {
    'Latitude': '5',
    'Longitude': '6',
}
QID2MD = {v: k for k, v in MD.items()}
STRIP_FROM_CODES = [
    ' (SKIP REMAINDER OF SECTION)',
    'NA (do not select)',
]
# We want to uniformly add units to relevant questions:
QUESTIONS = {
    'Distance to nearest continent': 'Distance to nearest continent (km)',
    'Longitude of culture’s location': 'Longitude of culture’s location (°)',
    'Latitude of culture’s location': 'Latitude of culture’s location (°)',
}


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "pulotu"

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return CLDFSpec(
            dir=self.cldf_dir,
            data_fnames={
                'LanguageTable': 'cultures.csv',
                'ParameterTable': 'questions.csv',
                'ValueTable': 'responses.csv',
            },
            module="StructureDataset")

    def cmd_download(self, args):
        pass

    def read(self, name, d=None):
        for row in (d or self.raw_dir).read_csv(name, dicts=True):
            yield collections.OrderedDict((k, v.strip()) for k, v in row.items())

    def cmd_makecldf(self, args):
        args.writer.cldf.add_columns(
            'LanguageTable',
            'Comment',
            { 'name': 'Ethonyms', 'separator': '; '})
        args.writer.cldf.add_columns(
            'ValueTable',
            { 'name': 'Uncertain', 'datatype': 'boolean'})
        args.writer.cldf.add_columns(
            'ParameterTable', 'Simplified_Name', 'Datatype', 'Section_Notes',
            'Category', 'Section', 'Subsection')
        args.writer.cldf.add_component('CodeTable')
        args.writer.cldf.add_table(
            'glossary.csv',
            {
                'name': 'ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id',
            },
            {
                'name': 'Term',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#name',
            },
            {
                'name': 'Definition',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#description',
            },
        )

        args.writer.cldf.sources.read(self.etc_dir / 'sources.bib')

        for r in self.read('core_glossary.csv'):
            args.writer.objects['glossary.csv'].append(dict(
                ID=slug(r['term']), Term=r['term'], Definition=r['definition']))

        cats = {r['id']: r['category'] for r in self.read('categories.csv')}
        sections = {}
        for r in self.read('sections.csv'):
            r['category'] = cats.get(r['category_id'])
            sections[r['id']] = r

        abvd2gc = {r['ID']: r['Glottocode'] for r in self.read('languages.csv', d=self.etc_dir)}
        l2abvd = {r['id']: r['abvdcode'] for r in self.read('languages.csv')}
        c2abvd = {r['culture_id']: l2abvd[r['language_id']] for r in self.read('cultures_languages.csv')}

        c2id = {}
        cultures = collections.OrderedDict()
        for r in self.read('cultures.csv'):
            c2id[r['id']] = r['slug']
            cultures[r['id']] = dict(
                ID=r['slug'],
                Name=r['culture'],
                Comment=r['notes'],
                Glottocode=abvd2gc.get(c2abvd[r['id']]),
                Ethonyms=split_text(r['ethonyms'], separators=';', strip=True),
                # FIXME: Add Glottolog classification for navigation/searching?
            )

        codes = collections.defaultdict(collections.OrderedDict)
        for r in self.read('questions_option.csv'):
            opts = re.split('(\([0-9?]\))', r['options'])
            assert not opts[0].strip()
            for k, v in zip(opts[1::2], opts[::2][1:]):
                codes[r['question_ptr_id']][k[1:-1]] = v.strip()

        public_questions = {}
        for r in self.read('questions.csv'):
            if r['displayPublic'] != 't':
                public_questions[r['id']] = r['response_type']
                name = r['question'].strip()
                args.writer.objects['ParameterTable'].append(dict(
                    ID=r['id'],
                    Name=QUESTIONS.get(name, name),
                    Simplified_Name=r['simplified_question'],
                    # Don't add internal information which is targeted at coders.
                    #Description=r['information'].replace('(VARIABLE LABEL REVERSED)', '').strip(),
                    Section_Notes=sections[r['section_id']]['notes'] or sections[r['subsection_id']]['notes'],
                    Datatype=r['response_type'] if r['id'] != '10' else 'Int',
                    Category=sections[r['subsection_id']]['category'] or sections[r['section_id']]['category'],
                    Section=sections[r['subsection_id']]['section'],
                    Subsection=sections[r['section_id']]['section'],
                ))
                if r['id'] in codes:
                    for k, v in codes[r['id']].items():
                        for s in STRIP_FROM_CODES:
                            v = v.replace(s, '').strip()
                        args.writer.objects['CodeTable'].append(dict(
                            ID='{}-{}'.format(r['id'], k.replace('?', 'NA')),
                            Parameter_ID=r['id'],
                            Name=k,
                            Description=v,
                        ))

        responses = collections.defaultdict(dict)
        for label, t in [('options', 'Option'), ('floats', 'Float'), ('integers', 'Int'), ('texts', 'Text')]:
            for r in self.raw_dir.read_csv('responses_{}.csv'.format(label), dicts=True):
                responses[t][r['response_ptr_id']] = r['response']

        srcmap = {r['id']: r['slug'] for r in self.read('sources.csv')}

        for r in self.read('responses.csv'):
            if r['question_id'] in public_questions:
                sources = []
                for i in range(1, 6):
                    sid, page = r['source{}_id'.format(i)], r['page{}'.format(i)]
                    if sid:
                        sid = srcmap[sid]
                        if sid not in ['source-not-applicable2014']:
                            sources.append('{}[{}]'.format(sid, page.replace(';', ',')) if page else sid)
                res = responses[public_questions[r['question_id']]][r['id']]
                if not res:
                    continue
                if r['question_id'] == '10':
                    res = int(res.replace(',', ''))
                mdkey = QID2MD.get(r['question_id'])
                if mdkey in ['Latitude', 'Longitude']:
                    cultures[r['culture_id']][mdkey] = float(res)
                cid = None
                if r['question_id'] in codes:
                    cid = '{}-{}'.format(r['question_id'], res.replace('?', 'NA'))
                args.writer.objects['ValueTable'].append(dict(
                    ID=r['id'],
                    Language_ID=c2id[r['culture_id']],
                    Parameter_ID=r['question_id'],
                    Value=res,
                    Code_ID=cid,
                    Source=sources,
                    # Uncertainty is not really informative or useful.
                    #Uncertain=r['uncertainty'] == 't',
                    # Coder's notes are typically informal, not meant for public release.
                    #Comment=r['codersnotes'],
                ))

        args.writer.objects['LanguageTable'] = list(cultures.values())
