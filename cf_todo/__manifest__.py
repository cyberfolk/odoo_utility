# -*- coding: utf-8 -*-
# Powered by cyberfolk

{
    'name': "Cyberfolk | TODO",
    'icon': '/cf_todo/static/description/icon.png',
    'sequence': 2,
    'version': '0.0.1',
    'category': 'Utility',
    'author': "cyberfolk",
    'summary': "Introduce i TODO.",
    'description':
        """In questa APP si possono creare TODO.""",
    'license': 'AGPL-3',
    'data': [
        "security/ir.model.access.csv",
        "views/menu_root.xml",
        "views/todo.xml",
    ],
    'assets': {
        'web.assets_backend': [
            '/cf_todo/static/src/css/style.css',
        ],
        'web.assets_frontend': [
            '/cf_todo/static/src/css/style.css',
        ]
    },
    'depends': [],
    'demo': [],
    'application': True,
    'installable': True,
}
