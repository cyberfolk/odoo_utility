import logging
import math

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

    score = fields.Float(
        string="Punteggio",
        compute="_compute_score",
        store=True,
        help="Punteggio calcolato da Importanza e Tempo"
    )

    @api.constrains('importance')
    def _check_importance(self):
        if self.importance < 1 or self.importance > 5:
            raise ValidationError('Importanza deve essere compresa tra 1 e 5')

    @api.constrains('time')
    def _check_time(self):
        if self.importance < 0.5 or self.importance > 16:
            raise ValidationError('Tempo deve essere compresa tra 00:30 e 16:00')

    @api.depends('time', 'importance')
    def _compute_score(self):
        for rec in self:
            impo_norm = 1 + rec.importance / 5  # [1.2; 2]
            time_norm = 1 + rec.time / 16  # [1.03125; 2]
            score = impo_norm / time_norm - 1  # [0,163; 1]
            rec.score = math.floor(score * 100) / 100  # Tronco a due cifre decimali

    def complete_todo(self):
        self.completed = True

    sequence = fields.Integer(string="Sequence", default=10)
