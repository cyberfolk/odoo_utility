import logging

from odoo.exceptions import ValidationError

from odoo import fields, models, api

_logger = logging.getLogger(__name__)

TODO_TYPE_SELECTION = [('add', '[ADD]'), ('del', '[DEL]'), ('upd', '[UPD]'), ('rfct', '[RFCT]')]
STATUS_SELECTION = [('todo', 'TODO'), ('focus', 'FOCUS'), ('done', 'FATTA'), ('skip', 'SKIP')]


class Todo(models.Model):
    _name = "todo"
    _description = "TODO"

    name = fields.Char(
        string="Nome",
        required=True
    )

    time = fields.Float(
        string="Tempo",
        default=8,
        required=True
    )

    description = fields.Text(
        string="Descrizione",
    )

    type = fields.Selection(
        selection=TODO_TYPE_SELECTION,
        string="Tipo",
        default='upd',
        required=True
    )

    importance = fields.Integer(
        string="Importanza",
        default=3,
        required=True
    )

    score = fields.Float(
        string="Punteggio",
        compute="_compute_score",
        store=True,
        help="Punteggio calcolato da Importanza e Tempo"
    )

    status = fields.Selection(
        selection=STATUS_SELECTION,
        default='todo',
        required=True
    )

    @api.constrains('importance')
    def _check_importance(self):
        if self.importance < 1 or self.importance > 5:
            raise ValidationError('Importanza deve essere compresa tra 1 e 5')

    @api.constrains('time')
    def _check_time(self):
        if self.time < 0.5 or self.time > 16:
            raise ValidationError('Tempo deve essere compresa tra 00:30 e 16:00')

    @api.depends('time', 'importance')
    def _compute_score(self):
        for rec in self:
            if rec.time and rec.importance:
                impo_norm = rec.importance / 5  # [1, 5] -> [0.2, 1]
                time_norm = rec.time / 16  # [0.5, 16] -> [0.03125, 1]
                raw_score = impo_norm - time_norm

                # Normalizzazione tra -0.8 e 0.96875
                min_score = -0.8
                max_score = 0.96875

                normalized = (raw_score - min_score) / (max_score - min_score)
                rec.score = round(normalized, 2)
            else:
                rec.score = 0.0

    def complete_todo(self):
        self.completed = True

    sequence = fields.Integer(string="Sequence", default=10)
