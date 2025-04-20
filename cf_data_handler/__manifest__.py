# -*- coding: utf-8 -*-
# Powered by cyberfolk
{
    'name': 'Cyberfolk | Data Handler',
    'version': '1.0',
    'category': 'Utility',
    'summary': 'Gestione di batch di dati e loro importazione/esportazione.',
    'description':
        """Gestione di batch di dati e loro importazione/esportazione.""",
    'license': 'AGPL-3',
    'author': "cyberfolk",
    'depends': ['base'],
    'data': [
        "security/ir.model.access.csv",
        "views/menu_root.xml",
        "views/data_handler_custom.xml",
        "views/data_handler.xml",
        "views/ir_model.xml",
    ],
    'icon': '/cf_data_handler/static/description/icon.png',
    'sequence': 2,
    'assets': {
    },
    'demo': [],
    'application': True,
    'installable': True,
}
