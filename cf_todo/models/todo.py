import logging

from odoo.exceptions import ValidationError

from odoo import fields, models, api

_logger = logging.getLogger(__name__)

TODO_TYPE_SELECTION = [('add', '[ADD]'), ('del', '[DEL]'), ('upd', '[UPD]'), ('rfct', '[RFCT]')]


class Todo(models.Model):
    _name = "todo"
    _description = "TODO"

    name = fields.Char(
        string="Nome",
    )

    time = fields.Float(
        string="Tempo",
    )

    description = fields.Text(
        string="Descrizione",
    )

    type = fields.Selection(
        selection=TODO_TYPE_SELECTION,
        string="Tipo",
        default='upd'
    )

    importance = fields.Integer(
        string="Importanza",
        default=3
    )

    completed = fields.Boolean(
        string="Completato",
        default=False
    )

    focus = fields.Boolean(
        string="Focus",
    )

    @api.constrains('importance')
    def _check_importance(self):
        if self.importance < 1 or self.importance > 5:
            raise ValidationError('Importanza deve essere compresa tra 1 e 5')

    sequence = fields.Integer(string="Sequence", default=10)
