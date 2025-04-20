# =============================================================
# LEGGERE
# =============================================================

# create_data_record()
# → Metodo principale chiamato in data.handler all'interno di process_datas().
# → Gestisce la creazione dei record a partire dal campo 'datas'.

# to_odoo_dict()
# → Converte il dizionario 'data_dict' in un dizionario compatibile con Odoo ('odoo_dict').

# manage_after_creation()
# → Eseguito dopo la creazione del record o sul obj_id recuperato tramite hashcode.
# → Utile per modificare campi non gestibili con write() e create().

import hashlib
import json
import logging

from odoo import models
from ..utilities.utility import clean_list

_logger = logging.getLogger(__name__)

EXCLUDED_FIELDS = {'write_date', 'write_uid', 'create_date', 'create_uid', 'display_name', 'id', 'x_data_id', 'x_data_hash'}


class Base(models.AbstractModel):
    _inherit = 'base'

    def export_json(self):
        """Richiama il controller per l'export dei record in formato JSON."""
        return {
            'type': 'ir.actions.act_url',
            'url': f"/data_handler/export_json?model={self._name}&ids={self.ids}",
            'target': 'new',
        }

    @staticmethod
    def from_rec_to_dikt(rec, skip_fields=None):
        """Trasforma un record di Odoo in un dizionario."""

        if skip_fields:
            EXCLUDED_FIELDS.update(skip_fields)

        dikt = {}
        for f_name, f_info in rec._fields.items():  # f_name  -> field_name, f_info -> field_info
            f_value = rec[f_name]  # f_value -> field_value
            f_type = f_info.type  # f_type  -> field_type

            if (f_name in EXCLUDED_FIELDS or f_info.compute or f_info.related) and f_name != 'name':
                continue
            elif f_type in ['binary']:
                dikt[f_name] = f_value.decode('utf-8') if f_value else ''
            elif f_type in ['html']:
                dikt['description'] = str(f_value) if f_value else ''
            elif f_type in ['many2one']:
                dikt[f_name] = f_value.get_unique_dict() or False  # TODO f_value.get_inner_dict()
            elif f_type in ['many2many', 'one2many']:
                dikt[f_name] = [x.get_unique_dict() for x in f_value] if f_value else []
            else:
                dikt[f_name] = f_value

        return dikt

    def get_domain_unique(self, data_dikt=None):
        """ Ritorna domain_unique basato sul campo unique_fields del modello.
            Di base ritorna il domain_unique del record dentro self, altrimenti
            Se il parametro data_dikt è impostato, ritorna il domain_unique relativo a data_dikt.
        """
        if not data_dikt and not self:
            return []

        dikt = data_dikt or self.read()[0]
        model = self.env['ir.model']._get(self._name)
        unique_fields = model.unique_fields

        if not unique_fields:
            raise Exception(f'Settare il campo "Campi Univoci" del modello "{self._name}" [ir.model({model.id})]')

        domain = [(field, '=', dikt.get(field)) for field in unique_fields]
        return domain

    def get_unique_id(self, data_dikt=None):
        """ Ritorna lo unique_id basato sul unique_fields del modello.
            Di base ritorna lo unique_id del record dentro self, altrimenti
            Se il parametro data_dikt è impostato, ritorna lo unique_id relativo data_dikt.
        """
        if not data_dikt and not self:
            return ''

        dikt = data_dikt or self.read()[0]
        model = self.env['ir.model']._get(self._name)
        unique_fields = model.unique_fields

        if not unique_fields:
            raise Exception(f'Settare il campo "Campi Univoci" del modello "{self._name}" [ir.model({model.id})]')

        def resolve_value(field_name, value):
            field = self._fields.get(field_name)
            if not field or value in (False, None, '', []):
                return ''

            if field.type == 'many2one':
                if isinstance(value, tuple) and value[0]:
                    rec = self.env[field.comodel_name].browse(value[0])
                    return rec.get_unique_id() if hasattr(rec, 'get_unique_id') else str(value[0])
                return ''

            elif field.type in ('many2many', 'one2many'):
                if isinstance(value, list) and value:
                    ids = value if isinstance(value[0], int) else [v[0] for v in value if isinstance(v, tuple)]
                    recs = self.env[field.comodel_name].browse(ids)
                    return '+'.join([
                        rec.get_unique_id() if hasattr(rec, 'get_unique_id') else str(rec.id)
                        for rec in recs
                    ])
                return ''

            return str(value)

        unique_fields_value = [
            resolve_value(field, dikt.get(field))
            for field in unique_fields if dikt.get(field)
        ]

        unique_id = '_'.join(filter(None, unique_fields_value))
        return unique_id

    def get_unique_dict(self, data_dikt=None):
        """ Ritorna lo unique_dict basato sul unique_fields del modello.
            Di base ritorna lo unique_dict del record dentro self, altrimenti
            Se il parametro data_dikt è impostato, ritorna lo unique_id relativo data_dikt.
        """
        if not data_dikt and not self:
            return {}

        dikt = data_dikt or self.read()[0]
        model = self.env['ir.model']._get(self._name)
        unique_fields = model.unique_fields

        if not unique_fields:
            raise Exception(f'Settare il campo "Campi Univoci" del modello "{self._name}" [ir.model({model.id})]')

        def resolve_value(field_name, value):
            field = self._fields.get(field_name)
            if not field:
                return value

            if field.type == 'many2one':
                if isinstance(value, tuple) and value[0]:
                    related_model = field.comodel_name
                    rec = self.env[related_model].browse(value[0])
                    return rec.get_unique_dict()
                return None

            elif field.type in ('one2many', 'many2many'):
                if isinstance(value, list):
                    related_model = field.comodel_name
                    return [
                        self.env[related_model].browse(record_id).get_unique_dict()
                        for record_id in value if record_id
                    ]
                return []

            return value

        unique_fields_dict = {
            field: resolve_value(field, dikt.get(field))
            for field in unique_fields
            if dikt.get(field) is not None
        }

        return unique_fields_dict

    def get_existing_records(self, data_dikt=None):
        """ Ritorna tutti i record già presenti nel db che hanno un domain_unique
            uguale a quello passato in data_dikt oppure presente in self.
        """
        if not data_dikt and not self:
            return []

        dikt = data_dikt or self.read()[0]
        domain_unique = self.get_domain_unique(dikt)

        existing_records = self.search(domain_unique)
        return existing_records

    def create_data_record(self, data_dict, count):
        """Crea un record partendo dai dati ricevuti in data_dict
        :return: (esito, msg)
            - esito: Possibili valori ['rec_created', 'rec_updated', 'rec_skipped', 'rec_error']
            - msg: Messaggio di esito."""
        x_data_id = count
        try:
            x_data_id = self.sudo().get_unique_id(data_dict)

            obj_id = self.sudo().get_existing_records(data_dict)

            # SE HO TROVATO PIÙ DI UN RECORD => ERRORE
            if len(obj_id) > 1:
                raise Exception(f"Errore: Trovati {len(obj_id)} record relativi a {x_data_id}")

            # CREO UN HASH DI DATA_DICT
            element_str = json.dumps(data_dict, sort_keys=True)  # converto il dict in una string JSON ordinata
            hash_object = hashlib.sha256(element_str.encode())  # Creazione dell'oggetto hash
            x_data_hash = hash_object.hexdigest()  # salvo hash in formato esadecimale

            # SE HASH CREATO == HASH DEL RECORD TROVATO => PASSO AL ITERAZIONE SUCCESSIVA
            if obj_id and obj_id.x_data_hash == x_data_hash:
                return x_data_id, 'rec_skipped', "Presente - PASS  - x_data_hash uguali"

            # odoo_dict = dizionario coi dati di data_dict ma tradotto per creare record di odoo
            odoo_dict = self.to_odoo_dict(data_dict, x_data_hash, x_data_id)  # TODO CUSTOM IMPORT

            # SE HASH CREATO != HASH DEL RECORD TROVATO => AGGIORNO RECORD TROVATO
            if obj_id and obj_id.x_data_hash != x_data_hash:
                filtered_dict = {k: v for k, v in odoo_dict.items() if v or k == 'is_company'}  # TODO FIX False/None
                obj_id.sudo().write(filtered_dict)

                # msg = f"Trovato stesso uniquecode({x_data_id})"
                # self.sudo().write_chatter_note(msg, obj_id.id)
                # obj_id.manage_after_creation(data_dict)
                return x_data_id, 'rec_updated', "Presente - WRITE - data_hash diversi"

            # SE NON HO TROVATO NESSUN RECORD LO CREO USANDO ODOO_DICT
            if not obj_id:
                rec = self.sudo().create(odoo_dict)
                # rec.manage_after_creation(data_dict)
                return x_data_id, 'rec_created', "Assente  - CREATE"

        except Exception as e:
            return x_data_id, 'rec_error', str(e).replace("\n", "")

    def manage_after_creation(self, data_dict):
        """Metodo eseguito dopo la creazione o sul obj_id recuperato tramite hashcode,
           serve per modificare i campi del record non gestibili tramite write e create.
        """
        pass

    def to_odoo_dict(self, data_dict, x_data_hash, x_data_id):
        """ Traduce il dizionario 'data_dict' nel dizionario 'odoo_dict', ovvero un dizionario adatto a creare
        record del modello che eredita il mixin.
        @param data_dict: (dict) il dizionario da tradurre.
        @param x_data_hash: (str) ash di data_dict
        @param x_data_id: (str) codice univoco per il record.
        """
        # TO OVERRIDE - La procedura qui riportata è un placeholder d'esempio
        # Implementare la logica di traduzione e i relativi controlli nei modelli che necessitano una logica custom.

        odoo_dict = data_dict

        for f_name, f_info in self._fields.items():
            f_value = odoo_dict.get(f_name)  # field_value
            f_type = f_info.type  # field_type
            f_comodel = f_info.comodel_name
            if f_name in EXCLUDED_FIELDS or f_info.compute or f_info.related:
                continue
            elif f_type in ['binary']:
                odoo_dict[f_name] = odoo_dict.get('image').encode('utf-8') if odoo_dict.get('image') else False
            elif f_type in ['many2one']:
                rec = self.env[f_comodel].sudo().get_existing_records(f_value)
                if f_value and not rec:
                    raise Exception(f"Errore: {f_value} non trovato in {f_comodel}")
                odoo_dict[f_name] = rec.id if rec else False
            elif f_type in ['many2many', 'one2many']:
                rec_list = []
                if not f_value:
                    continue
                for x in f_value:
                    rec = self.env[f_comodel].sudo().get_existing_records(x)
                    if x and not rec:
                        rec = self.env[f_comodel].sudo().create(x)
                        # raise Exception(f"Errore: {x} non trovato in {f_comodel}")
                    rec_list.append(rec)
                odoo_dict[f_name] = [rec.id for rec in rec_list] if rec_list else False
                odoo_dict[f_name] = clean_list(odoo_dict[f_name])  # TODO perchè la necessita di clean_list?

        odoo_dict['x_data_hash'] = x_data_hash
        odoo_dict['x_data_id'] = x_data_id
        return odoo_dict

    # region NON ANCORA USATI
    # def get_comodel_map(self):
    #     COMODEL_MAP = {}
    #     for f_name, f_info in self._fields.items():
    #         comodel_name = f_info.comodel_name
    #         if comodel_name:
    #             comodel_records = self.env[comodel_name].search([])
    #             MAP_MODEL_ID = {x.name: x.id for x in comodel_records}
    #             COMODEL_MAP[comodel_name] = MAP_MODEL_ID
    #     return COMODEL_MAP

    # def write_chatter_note(self, msg, record_id):
    #     self.env['mail.message'].create({
    #         'body': msg,
    #         'model': self._name,
    #         'res_id': record_id,
    #         'message_type': 'comment',
    #         'subtype_id': self.env.ref('mail.mt_note').id,
    #     })

    # def get_inner_dict(self):
    #     """Ritorna un dizionario da inserire nei campi many2many, one2many e many2one, all'interno del json"""
    #     # self.get_domain_unique()
    #     dikt = {
    #         'id': self.id,
    #         # 'x_data_id': self.x_data_id,  # è un campo che interessa solo il data_batch
    #         'name': self.name,
    #         'model_name': self.name
    #     }
    #     return False
    # endregion
