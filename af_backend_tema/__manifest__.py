# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "AF Backend Tema V12",
    "summary": "AF Backend Theme V12	",
    "version": "12.0.0.5",
    "category": "Theme/Backend",
    "description": """
		AF Backend tema för Odoo 12.0 community edition.
		v12.0.0.3 Added dependancy for the web-module.
		v12.0.0.5 Reverted Odoo Waffle and favicon icon to normal.
    """,
    "author": "Vertel AB",
    "license": "LGPL-3",
    "installable": True,
    "depends": [
        'base', 'portal', 'web'
    ],
    "data": [
        'views/assets.xml',
        'views/template.xml',
    ]
}
