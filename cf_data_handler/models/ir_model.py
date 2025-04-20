# SETTARE A MANO
# - Campo `unique_fields_str` (STR): Lista di campi che identificano in modo univo un Record (STR).

# VERRANNO POPOLATI
# - Campo `unique_fields` (JSON): Lista di campi che identificano in modo univo un Record (JSON).
# - Campo `unique_fields_display` (DISPLAY): Lista di campi che identificano in modo univo un Record (DISPLAY).

import json
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class IrModel(models.Model):
    _inherit = "ir.model"

    # region CAMPI UNIQUE
    unique_fields_str = fields.Char(
        string="Campi Univoci (STR)",
        help="Lista di campi che identificano in modo univo un Record (STR).",
    )

    unique_fields = fields.Json(
        string="Campi Univoci (JSON)",
        compute="_compute_unique_fields",
        help="Lista di campi che identificano in modo univo un Record (JSON).",
    )

    unique_fields_display = fields.Char(
        string="Campi Univoci (DISPLAY)",
        compute="_compute_unique_fields",
        help="Lista di campi che identificano in modo univo un Record (DISPLAY).",
    )

    @api.depends("unique_fields_str")
    def _compute_unique_fields(self):
        for rec in self:
            if not rec.unique_fields_str:
                rec.unique_fields = []
                rec.unique_fields_display = False
                continue

            ModelClass = rec.env.get(rec.model)  # Ottieni il modello dinamicamente
            model_fields = ModelClass._fields
            unique_fields = rec.unique_fields_str.split(',')
            unique_fields = [field.strip() for field in unique_fields]
            for field in unique_fields:
                if field not in model_fields:
                    raise models.ValidationError(
                        f'Nel modello "{rec.model}"\n'
                        f' - Non esiste alcun campo "{field}".\n'
                        f' - Correggere il campo "Campi Univoci" di ir.model({rec.id}).\n'
                        f'\n'
                        f'I Campi che si possono usare sono:\n'
                        f' {list(model_fields.keys())}'
                    )
            rec.unique_fields = unique_fields
            rec.unique_fields_display = json.dumps(unique_fields)

    # endregion

    # region CAMPI SKIP
    skip_fields_str = fields.Char(
        string="Campi Skip (STR)",
        help="Lista di campi che non vengono gestiti dal data_handler (STR).",
    )

    skip_fields = fields.Json(
        string="Campi Skip (JSON)",
        compute="_compute_skip_fields",
        help="Lista di campi che non vengono gestiti dal data_handler (JSON).",
    )

    skip_fields_display = fields.Char(
        string="Campi Skip (DISPLAY)",
        compute="_compute_skip_fields",
        help="Lista di campi che non vengono gestiti dal data_handler (DISPLAY).",
    )

    @api.depends("skip_fields_str")
    def _compute_skip_fields(self):
        for rec in self:
            if not rec.skip_fields_str:
                rec.skip_fields = []
                rec.skip_fields_display = False
                continue

            ModelClass = rec.env.get(rec.model)  # Ottieni il modello dinamicamente
            model_fields = ModelClass._fields
            skip_fields = rec.skip_fields_str.split(',')
            skip_fields = [field.strip() for field in skip_fields]
            for field in skip_fields:
                if field not in model_fields:
                    raise models.ValidationError(
                        f'Nel modello "{rec.model}"\n'
                        f' - Non esiste alcun campo "{field}".\n'
                        f' - Correggere il campo "Campi Skip" di ir.model({rec.id}).\n'
                        f'\n'
                        f'I Campi che si possono usare sono:\n'
                        f' {list(model_fields.keys())}'
                    )
            rec.skip_fields = skip_fields
            rec.skip_fields_display = json.dumps(skip_fields)

    # endregion

    # region CAMPI SUPPORT - ALERT
    warning_support_field = fields.Boolean(compute="compute_warning_support_field")
    warning_unique_field = fields.Text(compute="compute_warning_support_field")
    warning_x_data_id_field = fields.Text(compute="compute_warning_support_field")
    warning_x_data_hash_field = fields.Text(compute="compute_warning_support_field")

    @api.depends('unique_fields')
    def compute_warning_support_field(self):
        for rec in self:
            warning_unique_field = rec.unique_field_is_void()
            warning_x_data_id_field = rec.support_field_is_wrong('x_data_id')
            warning_x_data_hash_field = rec.support_field_is_wrong('x_data_hash')
            rec.write({
                'warning_support_field': any(
                    [warning_unique_field, warning_x_data_id_field, warning_x_data_hash_field]),
                'warning_unique_field': warning_unique_field,
                'warning_x_data_id_field': warning_x_data_id_field,
                'warning_x_data_hash_field': warning_x_data_hash_field,
            })

    def unique_field_is_void(self):
        if not self.unique_fields:
            return f'Campo "unique_fields" non impostato sul modello {self.model}.'

    def support_field_is_wrong(self, name):
        IrModelFields = self.env['ir.model.fields']
        field = IrModelFields.search([('model', '=', self.model), ('name', '=', name)], limit=1)

        if not field:
            return f'Campo "{name}" non esiste.'
        if field.ttype != 'char':
            return f'Campo "{name}" esiste, MA deve essere di tipo "char".'
        if not field.store:
            return f'Campo "{name}" esiste, MA deve essere store.'
        return False

    def support_field_fix(self, name, description):
        IrModelFields = self.env['ir.model.fields']
        field = IrModelFields.search([('model', '=', self.model), ('name', '=', name)], limit=1)

        if not field:
            new_field = IrModelFields.sudo().create({
                'name': name,
                'model_id': self.id,
                'model': self.model,
                'field_description': description,
                'ttype': 'char',
                'store': True
            })
        if field.ttype != 'char':
            field.ttype = 'char'
        if not field.store:
            field.store = True

    def x_data_id_field_fix(self):
        self.support_field_fix('x_data_id', 'Data ID')

    def x_data_hash_field_fix(self):
        self.support_field_fix('x_data_hash', 'Data Hash')
    # endregion
