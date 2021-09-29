import re
import pathlib
import collections

from clldutils.text import split_text
from clldutils.misc import slug
from cldfbench import Dataset as BaseDataset, CLDFSpec
from pycldf.sources import Source


MD = {
    'Latitude': '5',
    'Longitude': '6',
}
QID2MD = {v: k for k, v in MD.items()}


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

    def cmd_makecldf(self, args):
        args.writer.cldf.add_columns(
            'LanguageTable',
            'Comment',
            { 'name': 'Ethonyms', 'separator': '; '})
        args.writer.cldf.add_columns('ParameterTable', 'Datatype', 'Category', 'Section', 'Subsection')
        args.writer.cldf.add_component('CodeTable')
        args.writer.cldf.add_table(
            'glossary.csv',
            'ID',
            'Term',
            'Definition')

        for r in self.raw_dir.read_csv('core_glossary.csv', dicts=True):
            args.writer.objects['glossary.csv'].append(dict(
                ID=slug(r['term']),
                Term=r['term'],
                Definition=r['definition'].strip(),
            ))

        cats = {r['id']: r['category'] for r in self.raw_dir.read_csv('categories.csv', dicts=True)}
        sections = {}
        for r in self.raw_dir.read_csv('sections.csv', dicts=True):
            r['notes'] = r['notes'].strip()
            r['category'] = cats.get(r['category_id'])
            sections[r['id']] = r

        abvd2gc = {r['ID']: r['Glottocode'] for r in self.etc_dir.read_csv('languages.csv', dicts=True)}
        l2abvd = {
            r['id']: r['abvdcode'] for r in self.raw_dir.read_csv('languages.csv', dicts=True)}
        c2abvd = {r['culture_id']: l2abvd[r['language_id']] for r in self.raw_dir.read_csv('cultures_languages.csv', dicts=True)}

        c2id = {}
        cultures = collections.OrderedDict()
        for r in self.raw_dir.read_csv('cultures.csv', dicts=True):
            c2id[r['id']] = r['slug']
            cultures[r['id']] = dict(
                ID=r['slug'],
                Name=r['culture'],
                Comment=r['notes'],
                Glottocode=abvd2gc.get(c2abvd[r['id']]),
                Ethonyms=split_text(r['ethonyms'], separators=';', strip=True)
            )

        codes = collections.defaultdict(collections.OrderedDict)
        for r in self.raw_dir.read_csv('questions_option.csv', dicts=True):
            opts = re.split('(\([0-9?]\))', r['options'])
            assert not opts[0].strip()
            for k, v in zip(opts[1::2], opts[::2][1:]):
                codes[r['question_ptr_id']][k[1:-1]] = v.strip()

        public_questions = {}
        for r in self.raw_dir.read_csv('questions.csv', dicts=True):
            if r['displayPublic'] != 't':
                public_questions[r['id']] = r['response_type']
                args.writer.objects['ParameterTable'].append(dict(
                    ID=r['id'],
                    Name=r['question'].strip(),
                    Description=sections[r['section_id']]['notes'] or sections[r['subsection_id']]['notes'],
                    Datatype=r['response_type'] if r['id'] != '10' else 'Int',
                    Category=sections[r['subsection_id']]['category'] or sections[r['section_id']]['category'],
                    Section=sections[r['subsection_id']]['section'],
                    Subsection=sections[r['section_id']]['section'],
                ))
                if r['id'] in codes:
                    for k, v in codes[r['id']].items():
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

        #Option (126x)
        #	                       Float (14x)
        #	                       Int (7x)
        #	                       Text (6x)

        for r in self.raw_dir.read_csv('sources.csv', dicts=True):
            args.writer.cldf.sources.add(Source(
                'misc', r['id'], author=r['author'], year=r['year'], note=r['reference']))

        for r in self.raw_dir.read_csv('responses.csv', dicts=True):
            if r['question_id'] in public_questions:
                sources = []
                for i in range(1, 6):
                    sid, page = r['source{}_id'.format(i)], r['page{}'.format(i)]
                    if sid:
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
                    #Description=r['notes'],
                ))

        args.writer.objects['LanguageTable'] = list(cultures.values())
