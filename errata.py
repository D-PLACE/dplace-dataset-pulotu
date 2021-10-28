"""

Finally, could we add a reference list at the bottom with the following:

Mace, R., & Holden, C. J. (2005). A phylogenetic approach to cultural evolution. Trends in Ecology and Evolution, 20(3), 116-121.

Murdock, G. P. (1950). Feasibility and implementation of comparative community research: With special reference to the Human Relations Area Files. American Sociological Review, 15(6), 713-720.

Swanson, G. E. (1960). The birth of the gods; the origin of primitive beliefs. University of Michigan Press.


"""
GLOSSARY = {
    'Great god': ('god', 'a supernatural agent who was not originally a human being, is not '
                         'identified with or closely tied to a particular physical manifestation, '
                         'and is more powerful than most human beings can expect to be in this '
                         'life or the afterlife.'),
    'Human sacrifice': (None, lambda s: s.replace('sacrifice', 'costly sacrifice')),
    'Nature god': (None, 'a supernatural agent who was not originally a human being, is identified '
                         'with or closely tied to a particular feature of the natural world, and '
                         'is more powerful than most human beings can expect to be in this life '
                         'or the afterlife.'),
    'Nature spirit': (None, 'a supernatural agent who was not originally a human being, is '
                            'identified with or closely tied to a particular feature of the '
                            'natural world, and is not more powerful than most human beings '
                            'can expect to be in this life or the afterlife.'),
    'Internal warfare': (None, 'warfare between members of the same culture'),
    'Local community': (None, '”[t]he maximal group of persons who normally reside together in '
                              'face-to-face association” (Murdock, 1950)”'),
    'Deified ancestor': (None, lambda s: s.replace('became a god after death', 'acquired godlike powers after death')),
    'Tapu': (None, lambda s: s.replace('any restriction placed around', 'a restriction around')),
    'High god': (None, lambda s: s.replace('Murdock, 1967, p 160', 'Swanson, 1960')),
    'Ritual': (None, lambda s: s.replace('A ritual is', '').strip()),
    'Culture': (None, lambda s: s.replace('Currie, Greenhill & Mace, 2010, p 3904; Mace & Jordan, 2005, p 116',
                                          'Holden & Mace, 2005'))
}