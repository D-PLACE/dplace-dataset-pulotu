import re
import pathlib
import subprocess
import collections

from clldutils.text import split_text
from clldutils.misc import slug
from cldfbench import Dataset as BaseDataset, CLDFSpec

import errata

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
CNAMES = {
    'Maori': 'Māori',
}

CATEGORIES = [
    'Traditional Culture',
    'Post Contact History',
    'Current Culture',
]
SECTIONS = [
    'Belief (Current)',
    'Religious History',
    'Secular History',
    'Belief (Indigenous)',
    'Isolation',
    'Physical Environment',
    'Practice (Indigenous)',
    'Social Environment',
    'Subsistence and Economy',
]
SUBSECTIONS = [
    'Supernatural Beings',
    'Supernatural Punishment',
    'Afterlife and Creation',
    'General Features (Indigenous Belief)',
    'Classes of Tapu',
    'Mana',
    'General Supernatural Practices (Indigenous)',
    'Rites',
    'Conflict',
    'Land-based means of subsistence',
    'Water-based means of subsistence',
    'Commercial Activity',
    'Geographical Range of Culture',
    'Features of Island with Largest Culture Population',
    'Conversion',
    'Syncretic Movements',
    'Demographic and Social Changes',
    'Economic Changes',
    'Modern Infrastructure',
    'Loss of Autonomy',
    'Religious Demographics',
]


def parameter_sort(parameter):
    cat = parameter['Category']
    sec = parameter['Section']
    subsec = parameter['Subsection']
    return (
        CATEGORIES.index(cat) if cat in CATEGORIES else -1,
        SECTIONS.index(sec) if sec in SECTIONS else -1,
        SUBSECTIONS.index(subsec) if subsec in SUBSECTIONS else -1
    )


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
        """
        Collect the data from the dev branches of the UD repository forks
        """
        subprocess.check_call(
            'git -C {} submodule update --remote'.format(self.dir.resolve()), shell=True)

    def read(self, name, d=None):
        for row in (d or self.raw_dir.joinpath('pulotu-internal')).read_csv(name, dicts=True):
            yield collections.OrderedDict((k, v.strip()) for k, v in row.items())

    def cmd_makecldf(self, args):
        args.writer.cldf.add_columns(
            'LanguageTable',
            'Comment',
            { 'name': 'Ethonyms', 'separator': '; '})
        args.writer.cldf.add_columns(
            'ParameterTable',
            'Simplified_Name', 'Datatype', 'Section_Notes',
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
            {
                'name': 'Source',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#source',
                'separator': ';'
            },
        )

        args.writer.cldf.sources.read(self.etc_dir / 'sources.bib')

        for r in self.read('core_glossary.csv'):
            d = dict(
                ID=slug(r['term']), Term=r['term'], Definition=r['definition'])
            dd = errata.GLOSSARY.get(d['Term'])
            if dd:
                if len(dd) == 2:
                    term, definition = dd
                    source = None
                else:
                    term, definition, source = dd
                    d['Source'] = [source]
                if term:
                    d['Term'] = term
                    d['ID'] = slug(term)
                if isinstance(definition, str):
                    d['Definition'] = definition
                else:
                    d['Definition'] = definition(d['Definition'])

            args.writer.objects['glossary.csv'].append(d)

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
                Name=CNAMES.get(r['culture'], r['culture']),
                Comment=r['notes'].replace('Maori', 'Māori'),
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
                    Description=r['information'].replace('(VARIABLE LABEL REVERSED)', '').strip(),
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
            for r in self.read('responses_{}.csv'.format(label)):
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
        args.writer.objects['ParameterTable'] = sorted(
            args.writer.objects['ParameterTable'], key=parameter_sort)


VPK_2015 = {
"1": "v1",
"2": "v2",
"3": "v3",
"4": "v4",
"5": "v5",
"6": "v6",
"7": "v7",
"8": "v8",
"9": "v9",
"10": "v10",
"11": "v11",
"14": "v14",
"15": "v15",
"16": "v16",
"17": "v17",
"19": "v19",
"20": "v20",
"21": "v21",
"94": "v22",
"23": "v24",
"24": "v25",
"25": "v26",
"26": "v27",
"27": "v28",
"28": "v29",
"140": "v30",
"30": "v31",
"31": "v32",
"34": "v35",
"36": "v37",
"95": "v38",
"37": "v39",
"38": "v40",
"39": "v41",
"40": "v42",
"42": "v44",
"44": "v46",
"45": "v47",
"46": "v48",
"47": "v49",
"49": "v51",
"50": "v52",
"51": "v53",
"54": "v56",
"55": "v57",
"56": "v58",
"57": "v59",
"58": "v60",
"59": "v61",
"61": "v63",
"62": "v64",
"63": "v65",
"64": "v66",
"65": "v67",
"66": "v68",
"67": "v69",
"68": "v70",
"69": "v71",
"70": "v72",
"71": "v73",
"72": "v74",
"73": "v75",
"74": "v76",
"75": "v77",
"77": "v79",
"78": "v80",
"79": "v81",
"80": "v82",
"81": "v83",
"82": "v84",
"83": "v85",
"84": "v86",
"87": "v89",
"88": "v90",
"90": "v92",
"91": "v93",
"92": "v94",
"105": "v105",
"106": "v106",
}