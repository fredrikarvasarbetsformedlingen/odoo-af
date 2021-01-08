# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': "Disable access for core menus",
    'summary': "Hide some specific menus for internal type of user.",
    'description': "This module adds a access-group for standard-menus. If the user is not part of that group, the menu will be hidden.\n
    The current hidden menues are: contacts, discuss, calendar. \n
    v12.0.1.0.1 Added description and removed Website Config.", 
    
    "author": "Vertel AB",
    "license": "AGPL-3",
    "website": "https://vertel.se/",
    'category': 'Tools',
    'version': '12.0.1.0.1',
    'depends': ['calendar','website','contacts'],
    'data': [
        'security/security_view.xml',
    ],
    "application": False,
    "installable": True,
}
