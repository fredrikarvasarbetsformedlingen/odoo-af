# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Af Automatic Digital Customer Dialogue',
    'summary': "Adds an automatic Emailing Trigger based service",
    'version': '12.0.1.1.2',
    'author': 'Vertel AB',
    'license': 'AGPL-3',
    'maintainer': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'depends': ['base_setup', 
		'mail',
		'af_security',
		'partner_daily_notes'],
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/menuitem.xml',
        'views/partner_event_view.xml',
        'data/mail_template.xml',
        'data/data.xml',
    ],
    'auto_install': False,
    'installable': True,
}