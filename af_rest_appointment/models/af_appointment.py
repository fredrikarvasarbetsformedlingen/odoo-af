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
from datetime import datetime
import pytz
from urllib import request
from urllib.error import URLError, HTTPError
import json
import logging
from odoo.exceptions import Warning

# TODO: only use this in remote tests
import ssl

_logger = logging.getLogger(__name__)

LOCAL_TZ = 'Europe/Stockholm'

class AfAppointment(models.Model):
    _name = "af.appointment"
    _description = "Integration helper class"

    def _generate_tracking_id(self, af_system_id, af_environment):
        tracking_number = datetime.now().strftime("%y%m%d%H%M%S")
        tracking_id = "%s-%s-%s" % (af_system_id.upper(), af_environment.upper(), tracking_number)
        return tracking_id

    def _generate_ctx(self, is_remote):
        ctx = ssl.create_default_context()
        if is_remote:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        else:
            pass # TODO: implement mTSL here?
        return ctx

    def _generate_headers(self, af_environment, af_system_id, af_tracking_id):
        get_headers = {
            'AF-Environment': af_environment,
            'AF-SystemId': af_system_id,
            'AF-TrackingId': af_tracking_id,
        }
        return get_headers

    # /appointments
    def get_appointments(self, from_date, to_date, user = '', pnr = '', appointment_types = [], status_list = []):
        client_id = self.env['ir.config_parameter'].sudo().get_param('af_rest.client_id')
        client_secret = self.env['ir.config_parameter'].sudo().get_param('af_rest.client_secret')
        af_environment = self.env['ir.config_parameter'].sudo().get_param('af_rest.af_environment')
        af_port = self.env['ir.config_parameter'].sudo().get_param('af_rest.ipf_port')
        af_url = self.env['ir.config_parameter'].sudo().get_param('af_rest.ipf_url')
        af_system_id = self.env['ir.config_parameter'].sudo().get_param('af_rest.af_system_id')

        if not (af_url or af_port or client_id or client_secret or af_environment or af_system_id):
            raise Warning('Please setup AF integrations')

        # Generate a tracking-id
        af_tracking_id = self._generate_tracking_id(af_system_id, af_environment)

        # Define base url
        # ex: https://ipfapi.arbetsformedlingen.se:443/appointments/v1/appointments?client_id=da03472cd17e4ce4bb2d017156db7156&client_secret=B4BC32F21a314Cb9B48877989Cc1e3b8&from_date=2010-10-01&pnr=199601265516
        base_url = "{url}:{port}/{path}?client_id={client}&client_secret={secret}&from_date={from_date_str}&to_date={to_date_str}{user_str}{pnr_str}{appointment_types_str}{status_list_str}"

        # Insert values into base_url
        get_url = base_url.format(
            url = af_url, # https://ipfapi.arbetsformedlingen.se
            port = af_port, # 443
            path = "appointments/v1/appointments", # TODO: remove hardcoding?
            client = client_id, # check in anypoint for example
            secret = client_secret, # check in anypoint for example
            from_date_str = from_date.strftime("%Y-%m-%d"), # 2020-03-17T00:00:00Z
            to_date_str = to_date.strftime("%Y-%m-%d"), # 2020-03-25T00:00:00Z
            user_str = ("&user_id=%s" % user) if user else '', # 'eridd'
            pnr_str = ("&pnr=%s" % pnr) if pnr else '', # '16280810XXXX'
            appointment_types_str = ("&appointment_types=%s" % appointment_types) if appointment_types else '', # TODO: implement better, expected: comma seperated list.
            status_list_str = ("&status_list=%s" %status_list) if status_list else '', # TODO: implement better, expected: comma seperated list.
        )

        # Generate headers for our get
        get_headers = self._generate_headers(af_environment, af_system_id, af_tracking_id)

        # Build our request using url and headers
        # Request(url, data=None, headers={}, origin_req_host=None, unverifiable=False, method=None)
        req = request.Request(url=get_url, headers=get_headers)

        ctx = self._generate_ctx(is_remote=True) # TODO: change to False

        # send GET and read result
        res_json = request.urlopen(req, context=ctx).read()
        # Convert json to python format: https://docs.python.org/3/library/json.html#json-to-py-table 
        res = json.loads(res_json)

        # get list of appointments
        appointments = res.get("appointments")

        # loop over list
        for appointment in appointments:
            app_id = appointment.get('id')
            date = appointment.get('appointment_date') # "2019-10-02"
            stop = appointment.get('appointment_end_time') # "12:30:00"
            start = appointment.get('appointment_start_time') # "12:00:00"

            stop_datetime = datetime.strptime((date + "T" + stop), "%Y-%m-%dT%H:%M:%S")
            start_datetime = datetime.strptime((date + "T" + start), "%Y-%m-%dT%H:%M:%S")

            partner = self.env['res.partner'].search(['customer_id', '=', (appointment.get('customer_id'))]) # TODO: change to customer_id?
            user = self.env['res.users'].search([('signature', '=', appointment.get('employee_signature'))])
            
            # check if appointment exists
            app = self.env['calendar.appointment'].search([('ipf_id', '=', app_id)])
            if app:
                _logger.warn("DAER: app exists! app_id: %s app.channel: %s app: %s" % (app.id, app.channel, app))
                # TODO: update existing appointment
                pass
            else:
                # create new appointment
                vals = {
                    'ipf_id': app_id,
                    'name': appointment.get('appointment_title'),
                    # 'user_id': user.id, # disabled because of testing TODO: re-add
                    # 'partner_id': partner.id, # disabled because of testing TODO: re-add
                    'start': start_datetime,
                    'stop': stop_datetime,
                    'duration': appointment.get('appointment_length'),
                    'app_type': appointment.get('appointment_type'),
                    'status': appointment.get('status'),
                    'location_code': appointment.get('location_code'),
                    'office_code': appointment.get('office_code'),
                    'channel': appointment.get('appointment_channel'),
                }
                self.env['calendar.appointment'].create(vals)

            # Unused values from appointment:
            # appointment.get('customer_name')
            # appointment.get('employee_name')
            # appointment.get('employee_phone')
            # appointment.get('office_address')
            # appointment.get('office_name')

    # /resource-planning/competencies/schedules
    def get_schedules(self, from_datetime, to_datetime, type_ids):
        """fetches schedules from Teleopti via IPF and creates calendar.schedule in odoo"""
        client_id = self.env['ir.config_parameter'].sudo().get_param('af_rest.client_id')
        client_secret = self.env['ir.config_parameter'].sudo().get_param('af_rest.client_secret')
        af_environment = self.env['ir.config_parameter'].sudo().get_param('af_rest.af_environment')
        af_port = self.env['ir.config_parameter'].sudo().get_param('af_rest.ipf_port')
        af_url = self.env['ir.config_parameter'].sudo().get_param('af_rest.ipf_url')
        af_system_id = self.env['ir.config_parameter'].sudo().get_param('af_rest.af_system_id')

        if not (af_url or af_port or client_id or client_secret or af_environment or af_system_id):
            raise Warning('Please setup AF integrations')

        res = self.env['calendar.schedule']

        # Convert list of types into a string to be used in url
        type_str = ""
        for type_id in type_ids:
            type_str += "&competence_id=" + type_id.ipf_id

        # Generate a tracking-id
        af_tracking_id = self._generate_tracking_id(af_system_id, af_environment)

        # Define base url
        # ex: https://ipfapi.arbetsformedlingen.se:443/appointments/v1/resource-planning/competencies/schedules?from_date=2020-03-17T00:00:00Z&client_id=XXXXXXXXX&client_secret=XXXXXXXXX&to_date=2020-03-25T00:00:00Z&competence_id=ded72445-e5d3-4e21-a356-aad200dac83d
        base_url = "{url}:{port}/{path}?client_id={client}&client_secret={secret}&from_date={from_date}&to_date={to_date}{comps}"

        # Insert values into base_url
        get_url = base_url.format(
            url = af_url, # https://ipfapi.arbetsformedlingen.se
            port = af_port, # 443
            path = "appointments/v1/resource-planning/competencies/schedules", # TODO: remove hardcoding?
            client = client_id, # check in anypoint for example
            secret = client_secret, # check in anypoint for example
            from_date = from_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"), # 2020-03-17T00:00:00Z
            to_date = to_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"), # 2020-03-25T00:00:00Z
            comps = type_str, # &competence_id=ded72445-e5d3-4e21-a356-aad200dac83d
        )

        # Generate headers for our get
        get_headers = self._generate_headers(af_environment, af_system_id, af_tracking_id)

        # Build our request using url and headers
        # Request(url, data=None, headers={}, origin_req_host=None, unverifiable=False, method=None)
        req = request.Request(url=get_url, headers=get_headers)

        ctx = ctx = self._generate_ctx(is_remote=True) # TODO: change to False

        # send GET and read result
        req_res_json = request.urlopen(req, context=ctx).read()
        # Convert json to python format: https://docs.python.org/3/library/json.html#json-to-py-table 
        req_res = json.loads(req_res_json)

        # Create calendar.schedule from req_res
        # req_res: list of dicts with list of schedules
        # schedules: list of dicts of schedules
        for comp_day in req_res:
            # assumes that there's only ever one competence
            type_name = comp_day.get('competence').get('name')
            type_id = self.env['calendar.appointment.type'].search([('ipf_id','=',comp_day.get('competence').get('id'))])
            for schedule in comp_day.get('schedules'):
                start_time = datetime.strptime(schedule.get('start_time'), "%Y-%m-%dT%H:%M:%SZ")
                stop_time = datetime.strptime(schedule.get('end_time'), "%Y-%m-%dT%H:%M:%SZ")

                # Integration gives us times in local (Europe/Stockholm) tz
                # Convert to UTC
                start_time_utc = pytz.timezone(LOCAL_TZ).localize(start_time).astimezone(pytz.utc)
                stop_time_utc = pytz.timezone(LOCAL_TZ).localize(stop_time).astimezone(pytz.utc)

                # schedules can exist every half hour from 09:00 to 16:00
                # check if calendar.schedule already exists 
                schedule_id = self.env['calendar.schedule'].search([('type_id','=',type_id.id), ('start','=',start_time_utc)])
                if schedule_id:
                    # Update existing schedule only two values can change 
                    vals = {
                        'scheduled_agents': schedule.get('scheduled_agents'), # number of agents supposed to be available for this
                        'forecasted_agents': schedule.get('forecasted_agents'), # May be implemented at a later date.
                    }
                    schedule_id.update(vals)
                    res |= schedule_id
                else:
                    # create new schedule
                    vals = {
                        'name': type_name,
                        'start': start_time_utc,
                        'stop': stop_time_utc,
                        'duration': 30.0,
                        'scheduled_agents': int(schedule.get('scheduled_agents')), # number of agents supposed to be available for this. Can sometimes be float.
                        'forecasted_agents': int(schedule.get('forecasted_agents')), # May be implemented at a later date. Can sometimes be float.
                        'type_id': type_id.id,
                        'channel': type_id.channel,
                    }
                    res |= self.env['calendar.schedule'].create(vals)

        return res
