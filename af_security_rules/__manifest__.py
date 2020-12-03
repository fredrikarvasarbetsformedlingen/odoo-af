# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "AF Security Rules",
    "version": "12.0.1.0.2",
    "author": "Vertel AB",
    "license": "AGPL-3",
    "description": "Security rules for Arbetsförmedlingen. v12.0.1.0.2 Added ServiceDesk user-rights",
    "website": "https://vertel.se/",
    "category": "Tools",
    "depends": [
        "af_security",
        "partner_view_360",
        "partner_daily_notes",
        "calendar_af",
        ],
    "external_dependencies": {'python': ['zeep']},
    "data": [
        "security/af_security.xml",
        "security/ir.model.access.csv",
    ],
    "application": True,
    "installable": True,
}
