# -*- coding: utf-8 -*-
# Powered by cyberfolk
{
    'name': 'Cyberfolk | Web Scraper',
    'version': '1.0',
    'category': 'Utility',
    'summary': 'Scraping di pagine web e creazione di record in Odoo',
    'description':
        """Scraping di pagine web e creazione di record in Odoo.""",
    'license': 'AGPL-3',
    'author': "cyberfolk",
    'depends': [],
    'data': [
        "security/ir.model.access.csv",
        "views/menu_root.xml",
        "views/web_scraper.xml",
    ],
    'icon': '/cf_web_scraper/static/description/icon.png',
    'sequence': 2,
    'assets': {
    },
    'demo': [],
    'application': True,
    'installable': True,
}
