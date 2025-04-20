import base64
import json
import logging
from collections import Counter

from odoo.exceptions import ValidationError, UserError

from odoo import models, fields, api
from ..utilities.utility import format_error, join_dikt


class DataHandler(models.Model):
    _name = "data.handler"
    _description = "Modello per gestire batch di dati"

    record_in_batch = fields.Integer(
        string="Record in batch",
        help="Numero di record in batch",
        default=5,
        required=True,
    )

    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Modello",
        required=True,
        ondelete="cascade",  # Evita il problema di 'restrict'
    )

    model_name = fields.Char(
        string="Modello Nome",
        related="model_id.model",
    )

    datas_file = fields.Binary(
        string="DATAs File"
    )

    datas_file_name = fields.Char(
        string="Nome DATAs File",
    )

    custom_handler_id = fields.Many2one(
        comodel_name="data.handler.custom",
        string="Custom Handler",
        help="Handler personalizzato",
    )

    is_standard_import = fields.Boolean(
        string="Standard Import",
        help="Effettua l'importazione standard",
        default=True,
    )

    state = fields.Selection([
        ('draft', 'Bozza'),
        ('completed_correctly', 'Completato con Successo'),
        ('completed_with_errors', 'Completato con Errori'),
        ('partially_processed', 'Processato Parzialmente'),
    ], required=True, string='Stato', default='draft')

    datas = fields.Text(
        string="DATAs",
    )

    name = fields.Char(
        string="Nome",
        help="Nome del file",
        required=True,
    )

    list_error = fields.Text(
        string="Elenco errori",
        help="Elenco dei record che non si è riuscito ad importare",
    )

    already_done = fields.Integer(
        string="Record Processati",
        help="Numero di record processati",
        default=0,
        readonly=True,
    )

    rec_total = fields.Integer(
        string="Record Totali",
        help="Numero di record in json",
        readonly=True,
    )

    datas_len = fields.Integer(
        compute="compute_datas_len",
    )

    list_duplicated = fields.Text(
        string="Elenco Record Duplicati",
        compute="list_compute_duplicated",
    )

    active = fields.Boolean(
        default=True,
    )

    error_support_field = fields.Boolean(compute="compute_error_support_field")
    error_unique_field = fields.Text(compute="compute_error_support_field")
    error_x_data_id_field = fields.Text(compute="compute_error_support_field")
    error_x_data_hash_field = fields.Text(compute="compute_error_support_field")

    @api.depends('model_id', 'model_id.unique_fields')
    def compute_error_support_field(self):
        for rec in self:
            if not rec.model_id:
                error_unique_field = 'Modello non impostato, impossibile verificare il campo "unique_fields"'
                error_x_data_id_field = 'Modello non impostato, impossibile verificare il campo "x_data_id"'
                error_x_data_hash_field = 'Modello non impostato, impossibile verificare il campo "x_data_hash"'
            else:
                error_unique_field = rec.model_id.unique_field_is_void()
                error_x_data_id_field = rec.model_id.support_field_is_wrong('x_data_id')
                error_x_data_hash_field = rec.model_id.support_field_is_wrong('x_data_hash')
            rec.write({
                'error_support_field': any([error_unique_field, error_x_data_id_field, error_x_data_hash_field]),
                'error_unique_field': error_unique_field,
                'error_x_data_id_field': error_x_data_id_field,
                'error_x_data_hash_field': error_x_data_hash_field,
            })

    def fix_error_x_data_id_field(self):
        self.model_id.x_data_id_field_fix()

    def fix_error_x_data_hash_field(self):
        self.model_id.x_data_hash_field_fix()

    def download_datas(self):
        """Scarica il contenuto del campo DATAs come file JSON."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f"/data_handler/download_datas?id={self.id}",
            'target': 'new',
        }

    @api.depends('datas')
    def compute_datas_len(self):
        """Conta il numero di caratteri nel campo DATAs."""
        self.ensure_one()
        self.datas_len = len(self.datas) if self.datas else 0

    @api.constrains('datas')
    def _check_datas(self):
        """Validazione del campo DATAs. Evita che l'utente invalidi il json"""
        for rec in self:
            if not rec.datas:
                continue
            try:
                new_datas = json.loads(rec.datas)
            except json.JSONDecodeError as e:
                raise ValidationError(f"Il campo DATAs contiene un valore non valido.\n{e}")

    def process_datas(self, data_list, log_name, count, total, manage_error=False):
        """ Funzione core per creare record processando data_list. Viene implementata in questi 3 metodi.
            - start_import_from_zero() -----> data_list=datas; count=0; total=len(data_list).
            - continue_import_from_pause() -> data_list=dati_rimanenti; count=already_done; total = record_rimanenti
            - import_reported_errors() -----> data_list=list_error; count= 0; total=len(list_error); manage_error=True
        :param data_list: Lista di dizionari da processare,
        :param log_name: Nome del log da usare, in apertura, in chiusura e nelle pause per salvare i record nel db.
        :param count: Valore iniziale del counter dei record da processare.
        :param total: Totale record da processare.
        :param manage_error: Se è True mantengo already_done=already_done e mantengo status=completed_with_errors
        :return: Il record creato o aggiornato. """
        try:
            logging.info(f"*** START *** {log_name}")
            model = self.model_name
            RECORD_IN_BATCH = self.record_in_batch

            list_duplicated = {}
            list_duplicated_count = sum(list_duplicated.values())
            summary = {
                'rec_handled': 0,
                'rec_updated': 0,
                'rec_created': 0,
                'rec_skipped': 0,
                'rec_error': 0,
                'list_duplicated_count': list_duplicated_count,
                'list_duplicated': list_duplicated,
                'list_error': json.loads(self.list_error)
            }

            for data_dict in data_list:
                count += 1
                x_data_id, esito, msg = self.env[model].create_data_record(data_dict, count)
                summary[esito] += 1
                log_template = f"- ({count}/{total}) {model} -> {msg}"
                if esito == 'rec_error':
                    logging.error(log_template)
                    summary['list_error'].append({x_data_id: msg})
                else:
                    logging.info(log_template)

                if count % RECORD_IN_BATCH == 0:
                    if manage_error:
                        self.state = 'completed_with_errors'
                    else:
                        self.already_done += RECORD_IN_BATCH
                        self.state = 'partially_processed'
                    self.list_error = format_error(summary['list_error'])
                    logging.info(f"*** PAUSE *** Processati {RECORD_IN_BATCH} records")
                    logging.info(f"*** PAUSE *** In attesa che il batch di dati venga salvato nel Database")
                    self.env.cr.commit()
                    logging.info(f"*** PLAY  *** Ripresa {log_name}")

            self.env.cr.commit()
            self.already_done = self.rec_total
            summary['rec_handled'] = count

            logging.info(f"*** HANDLED {summary['rec_handled']}")
            logging.info(f"*** UPDATED {summary['rec_updated']}")
            logging.info(f"*** CREATED {summary['rec_created']}")
            logging.info(f"*** SKIPPED {summary['rec_skipped']}")

            if summary['list_duplicated_count']:
                logging.warning(f" NUMERO DUPLICATI PRESENTI NEL JSON {summary['list_duplicated_count']}")
                logging.warning(f" LISTA  DUPLICATI PRESENTI NEL JSON {summary['list_duplicated']}")
            if not summary['list_error']:
                self.state = 'completed_correctly'
            else:
                self.state = 'completed_with_errors'
                self.list_error = format_error(summary['list_error'])
                summary['list_error'] = join_dikt(summary['list_error'])

            logging.info(f"*** END *** {log_name}")
            return summary

        except Exception as e:
            logging.error(f"*** ERRORE *** {log_name}\n{e}")
            raise Exception(e)

    def start_import_from_zero(self):
        """Inizia il processo d'importazione del campo json. Inizializza already_done=0 ed list_error="[]",
         poi inizia il processo partendo dal record numero zero."""
        log_name = f"IMPORT JSON_FIELD FROM ZERO di {self.name}"
        self.already_done = 0
        self.list_error = "[]"
        data_list = json.loads(self.datas)
        self.rec_total = len(data_list)
        start_index = 0
        self.process_datas(data_list, log_name, start_index, self.rec_total)

    def continue_import_from_pause(self):
        """Ricomincia il processo d'importazione del campo json partendo dallo stato da dove si era interrotto.
         Mantiene la list_error già tracciata e riparte a processare dal record numero already_done."""
        log_name = f"CONTINUE IMPORT JSON_FIELD FROM PAUSE {self.name}"
        if self.state != 'partially_processed':
            logging.info(f"*** SKIP  *** {log_name} perchè state = {self.state}")
            return
        if self.already_done > 0:
            data_list = json.loads(self.data)
            data_list_remaining = data_list[self.already_done:]
            logging.info(f"*** SKIP  *** Saltati i primi {self.already_done} perchè già processati")
            start_index = self.already_done
            self.process_datas(data_list_remaining, log_name, start_index, self.rec_total)
        else:
            logging.info(f"*** SKIP  *** {log_name} perchè already_done = {self.already_done}")

    def import_reported_errors(self):
        """Prova a reimportare i record tracciati nel campo list_error."""
        return
        # log_name = f"IMPORT REPORTED_ERRORS {self.name}"
        # if self.state != 'completed_with_errors':
        #     logging.info(f"*** SKIP  *** {log_name} perchè state = {self.state}")
        #     return
        # if self.list_error:
        #     data_list_error = self.get_data_list_error()
        #     self.list_error = "[]"
        #     num_error = len(data_list_error)
        #     start_index = 0
        #     self.process_datas(data_list_error, log_name, start_index, num_error, manage_error=True)
        # else:
        #     logging.info(f"*** SKIP  *** {log_name} perchè already_done = {self.list_error}")

    # def get_data_list_error(self):
    #     """Filtra i dizionari di DATAs con solo quelli il cui uniquecode è presente in list_error"""
    #     model, field_odoo, _list_field = MAP_TYPE_MODEL[self.type]
    #     list_error_list = json.loads(self.list_error)
    #     code_list_error = [list(dikt.keys())[0] for dikt in list_error_list]
    #     data_list = json.loads(self.data)
    #     if _list_field[0] is '_custom_iterator':
    #         data_list_error = [data_list[int(x)] for x in code_list_error]
    #     else:
    #         data_list_error = [dikt for dikt in data_list if
    #                            get_uniquecode(_list_field, dikt, self.type) in code_list_error]
    #     return data_list_error

    def list_compute_duplicated(self):
        for rec in self:
            if not self.datas:
                rec.list_duplicated = 'DATAs non ancora caricati'
                continue

            try:
                ModelClass = self.env.get(self.model_name)  # Ottieni il modello dinamicamente

                data_list = json.loads(self.datas)
                list_unique_id = [ModelClass.get_unique_id(dikt) for dikt in data_list]
                counter = Counter(list_unique_id)  # Contare le occorrenze di ciascun valore
                duplicates = {value: count for value, count in counter.items() if count > 1}  # Filtrare solo i duplicati

                rec.list_duplicated = json.dumps(duplicates, indent=4)
            except Exception as e:
                rec.list_duplicated = f"Errore: {str(e)}"

    @api.onchange('datas_file')
    def _onchange_datas_file(self):
        if not self.datas_file:
            return
        try:
            file_content = base64.b64decode(self.datas_file).decode('utf-8')  # Decodifica il file da base64
            json_data = json.loads(file_content)  # Converte in JSON per vedere se genera errori
            self.datas = file_content  # Salva il contenuto del file JSON
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise UserError("Il file caricato non è un JSON valido.")
