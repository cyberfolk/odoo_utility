import json
from ast import literal_eval

from odoo.exceptions import UserError
from odoo.http import route, request

from odoo import http


def get_headers(name_file):
    headers = [
        ('Content-Type', 'application/json'),
        ('Content-Disposition', f'attachment; filename="{name_file}.json"')
    ]
    return headers


class DataHandlerController(http.Controller):

    @route('/data_handler/download_datas', type='http', auth='user')
    def download_datas(self, **kwargs):
        """Rotta che permette di scaricare in formato JSON il contenuto del campo Datas del modello data.handler."""
        try:
            data_handler_id = literal_eval(kwargs.get('id', ''))
            data_handler = request.env['data.handler'].sudo().browse(data_handler_id)
            datas = data_handler.datas or '[]'
            name_file = data_handler.name

            headers = get_headers(name_file)
            txt = request.make_response(datas, headers=headers)
            return txt

        except Exception as ex:
            raise UserError(f"Errore durante la generazione del json:\n{ex}")

    @route('/data_handler/export_json', type='http', auth='user')
    def export_json(self, **kwargs):
        """Rotta che permette di scaricare i dati di un record in formato JSON."""
        try:
            ids = literal_eval(kwargs.get('ids', ''))
            model = kwargs.get('model', '')
            Model = request.env[model]
            records = request.env[model].sudo().browse(ids)
            ir_model = request.env['ir.model'].sudo().search([('model', '=', model)], limit=1)
            name_file = model.replace('.', '_')
            skip_fields_base = ir_model.skip_fields or []
            skip_fields_other = literal_eval(kwargs.get('skip_fields', '[]'))
            skip_fields = skip_fields_other + skip_fields_base
            custom_transform_method = kwargs.get('custom_transform_method', '')

            dicts = []
            for rec in records:
                dikt = Model.from_rec_to_dikt(rec, skip_fields, custom_transform_method)
                if dikt:
                    dicts.append(dikt)

            dicts_json = json.dumps(dicts, indent=4, ensure_ascii=False)
            datas = dicts_json or '[]'

            headers = get_headers(name_file)
            txt = request.make_response(datas, headers=headers)
            return txt

        except Exception as ex:
            raise UserError(f"Errore durante export json:\n{ex}")
