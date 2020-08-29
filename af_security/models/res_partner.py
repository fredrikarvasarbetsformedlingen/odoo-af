# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2020 Vertel AB (<http://vertel.se>).
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
from pytz import timezone
from datetime import timedelta
from zeep.client import CachingClient
from zeep import xsd
from uuid import uuid4

import logging
_logger = logging.getLogger(__name__)

LOCAL_TZ = timezone('Europe/Stockholm')
WSDL_NYCKELTJANST = 'http://bhtj.arbetsformedlingen.se/KeyService/ws/nyckeltjanst?wsdl'
WSDL_INITIERANDE_NYCKELTJANST = 'http://bhtj.arbetsformedlingen.se/KeyService/ws/initierandenyckeltjanst?wsdl'
NYCKELTJANST = None
INITIERANDE_NYCKELTJANST = None
INIT_HEADER_SYSTEM_ID = 'CRM'
INIT_HEADER_API_VERSION = '1.3'

    
class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Access rights to archive contacts. This is probably not good enough.
    # Can't specify read/write.
    # Can't specify domains per group (causes crossover between employers and jobseekers officers)
    # TODO: Look for a solution. Existing module or build one.
    #       Look at that encryption module to add new parameters to fields.
    active = fields.Boolean(groups='base.group_system,af_security.group_af_employers_high,af_security.group_af_jobseekers_high')
    jobseeker_access_ids = fields.One2many(comodel_name='jobseeker.access', inverse_name='partner_id', string='Authorized Users')
    
    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        """Assign access rights when creating a jobseeker."""
        _logger.warn(vals_list)
        _logger.warn(self.env.context)
        for vals in vals_list:
            if vals.get('is_jobseeker'):
                vals['jobseeker_access_ids'] = [(0, 0, {
                    'user_id': self.env.user.id,
                })]
        return super(ResPartner, self).create(vals_list)
    
    @api.model
    def _bhtj_get_nyckeltjanst(self):
        """Fetch or initialize connection to BHTJ for checking access rights."""
        if NYCKELTJANST:
            return NYCKELTJANST
        try:
            key_service = CachingClient(WSDL_NYCKELTJANST)
            if not NYCKELTJANST:
                global NYCKELTJANST = key_service
            return NYCKELTJANST
        except:
            raise Warning(_("Could not connect to BHTJ to check access rights!"))
    
    @api.model
    def _bhtj_get_initierande_nyckeltjanst(self):
        """Fetch or initialize connection to BHTJ for granting access rights."""
        if INITIERANDE_NYCKELTJANST:
            return INITIERANDE_NYCKELTJANST
        try:
            key_service = CachingClient(WSDL_INITIERANDE_NYCKELTJANST)
            if not INITIERANDE_NYCKELTJANST:
                global INITIERANDE_NYCKELTJANST = key_service
            return INITIERANDE_NYCKELTJANST
        except:
            raise Warning(_("Could not connect to BHTJ to grant access rights!"))
        

    @api.multi
    def _grant_jobseeker_access(self, access_type, user=None, reason_code=None, reason=None, granting_user=None, start=None, interval=1):
        """ Grant temporary access to these jobseekers.
            :param access_type: The type of access. One of 'STARK' or 'MYCKET STARK'.
            :param user: The user that is to be granted permission. Defaults to current user.
            :param reason_code: The reason code for granting extra permissions.
            :param reason: Freetext reason for granting extra permissions.
            :param granting_user: Optional. The user granting this access. Maybe?
            :param start: Datetime. The time when access is to start. Defaults to now. Works in mysterious ways.
            Past dates (time seems to be ignored) generates an error. Future times grant access immediately. Ignore it.
            :param interval: Integer. How many days access is to last. One of 1, 7, 14, 30, 60, 100 and 365.
        """
        user = user or self.env.user
        start = start or datetime.now()
        pnr = []
        missing_pnr = []
        for partner in self:
            if partner.ccompany_registry:
        if not (interval in (1, 7, 14, 30, 60, 100, 365)):
            raise Warning(_("BHTJ: interval must be one of 1, 7, 14, 30, 60, 100, 365."))
        if not (reason or reason_code):
            raise Warning(_("BHTJ: You must provide a reason or reason_code."))
        if access_type not in ('STARK', 'MYCKET STARK'):
            raise Warning(_("BHTJ: Access type must be either STARK or MYCKET STARK."))
        values = {
            '_soapheaders': {
                'apiVersion': INIT_HEADER_API_VERSION,
                'pisaID': granting_user and granting_user.login or '',
                'systemID': INIT_HEADER_SYSTEM_ID,
                'transactionID': uuid4()}
            'arbetssokandeLista': pnr,
            'giltigFran': start,
            'intervall': 'Dagar_%i' interval,
            'orsak': {
                'friTxt': reason or '',
                'orsakKod': reason_code or '',},
            'nyckelTyp': type,
            'signatur': user.login
        }
        if reason_code:
            values['orsak']['orsakDef'] = 'NYKOD'
        else:
            values['orsak']['orsakDef'] = 'FRITXT'

        bhtj = self._bhtj_get_initierande_nyckeltjanst()
        #try:
        if True:
            response = bhtj.service.skapaNyckel(**values)
        #except:
        #    raise Warning(_("Could not connect to BHTJ."))
        return response

    @api.model
    def af_security_install_rules(self):
        """Update existing rules that can't be changed through XML."""
        self.env.ref('base.res_partner_rule_private_employee').active = False

class JobseekerAccess(models.TransientModel):
    _name = 'jobseeker.access'
    _description = 'Jobseeker Access'

    partner_id = fields.Many2one(comodel_name='res.partner', string='Jobseeker', required=True, ondelete='cascade')
    user_id = fields.Many2one(comodel_name='res.users', string='User', required=True, ondelete='cascade')
    stop_datetime = fields.Datetime(string='Stop Time', default=lambda self: self._default_stop_datetime(), required=True)

    @api.model
    def _default_stop_datetime(self):
        """Give permissions until the end of day + 24 h."""
        return self.local2utc(
            (fields.Datetime.now() + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0))

    @api.model
    def _transient_vacuum(self, force=False):
        """Override autovacuum to use stop_datetime."""
        query = ("SELECT id FROM " + self._table + " WHERE"
            " stop_datetime::timestamp"
            " < (now() at time zone 'UTC')")
        self._cr.execute(query)
        ids = [x[0] for x in self._cr.fetchall()]
        self.sudo().browse(ids).unlink()

    @api.model
    def local2utc(self, dt, tz=None):
        """Compensate for timezone. Use this when writing a datetime."""
        tz = tz or LOCAL_TZ
        return dt - tz.utcoffset(dt)
