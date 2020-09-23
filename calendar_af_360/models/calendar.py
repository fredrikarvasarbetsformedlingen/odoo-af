# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2015 Vertel AB (<http://vertel.se>).
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
from datetime import datetime

_logger = logging.getLogger(__name__)

class CalendarAppointmentSuggestion(models.Model):
    _inherit = 'calendar.appointment.suggestion'
    
    
    @api.multi
    def select_suggestion(self):
        # check state of appointment
        super(CalendarAppointmentSuggestion, self).select_suggestion()
        
        return{
            'name': _("Jobseekers"),
            'res_id': self.appointment_id.partner_id.id,
            'res_model': "res.partner",
            'view_id': self.env.ref("partner_view_360.view_jobseeker_form").id, 
            'view_mode':"form",
            'type': 'ir.actions.act_window',
        }