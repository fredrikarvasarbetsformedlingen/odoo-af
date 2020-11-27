# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2019 Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

class Sni(models.Model): 
    _name = 'res.sni'

    partner_ids = fields.Many2many(comodel_name="res.partner")
    
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Official Code',help="Official code, group, sub-group or detail group.")
    description = fields.Char(string='Description')
    parent_id = fields.Many2one(comodel_name='res.sni', string='Parent')
