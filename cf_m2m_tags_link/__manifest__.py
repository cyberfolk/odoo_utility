# -*- coding: utf-8 -*-
# Powered by cyberfolk

{
    'name': "Cyberfolk | Many2Many Tags Link",
    'icon': '/cf_hex_base/static/description/cyberfolk.png',
    'version': '17.0',
    'category': 'Utility',
    'author': "cyberfolk",
    'summary': "Permette di raggiungere il record cliccando sul badge del widget 'many2many_tags'.",
    'description':
        """Questo modulo estende il widget "many2many_tags", consentendo di accedere al record cliccando sul 
        badge del widget.""",
    'license': 'AGPL-3',
    'data': [],
    'depends': [],
    'demo': [],
    'application': False,
    'installable': True,
    'assets': {
        'web.assets_backend': [
            '/cf_m2m_tags_link/static/src/many2many_tags/*',
        ],
    },
}
