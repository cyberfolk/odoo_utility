# -*- coding: utf-8 -*-
# Powered by cyberfolk

{
    'name': "Cyberfolk | One2Many Expand Popup",
    'icon': '/cf_o2m_expand_popup/static/description/cyberfolk.png',
    'version': '17.0',
    'category': 'Utility',
    'author': "cyberfolk",
    'summary': "Aggiunge un bottone per estendere a schermo intero i pop-up dei record generati dai campi o2m'.",
    'description':
        """Questo Modulo introduce il widget 'o2m_expand_popup' il quale aggiunge il bottone 'Expand' nelle
        viste pop-up dei record o2m, cliccando su questo bottone si apre la vista a dimensione intera.""",
    'license': 'AGPL-3',
    'data': [],
    'depends': [],
    'demo': [],
    'application': False,
    'installable': True,
    'assets': {
        'web.assets_backend': [
            '/cf_o2m_expand_popup/static/src/o2m_expand_popup/*',
        ],
    },
}
