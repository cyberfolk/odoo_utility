# TODO SVILUPPI ANCORA IN FASE EMBRIONALE

from odoo import fields, models


class DataHandlerCustom(models.Model):
    _name = "data.handler.custom"
    _description = "Modello per gestire le personalizzazione degli import"

    name = fields.Char(
        string="Nome",
    )

    _sql_constraints = [
        ("name_uniq", "unique(name)", "Il nome deve essere univoco"),
    ]

    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Modello",
    )
