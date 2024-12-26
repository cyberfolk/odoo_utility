# -*- coding: utf-8 -*-
# Powered by cyberfolk

{
    'name': "Cyberfolk | Multiple Image",
    'icon': '/cf_multiple_image/static/description/cyberfolk.png',
    'version': '17.0',
    'category': 'Utility',
    'author': "cyberfolk",
    'summary': "Aggiunge il widget 'MultipleImage' per vedere in serie le immagini in un campo Many2many.",
    'description':
        """Questo Modulo introduce il widget 'MultipleImage' permettendo di visualizzare in serie le
          immagini contenuto dentro un campo Many2many con il modello 'ir.attachment'.""",
    'license': 'AGPL-3',
    'data': [],
    'depends': [],
    'demo': [],
    'application': False,
    'installable': True,
    'assets': {
        'web.assets_backend': [
            '/cf_multiple_image/static/src/MultipleImage/*',
        ],
    },
}
