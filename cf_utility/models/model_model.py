from odoo import models

EXCLUDED_FIELDS = {'write_date', 'write_uid', 'create_date', 'create_uid', 'display_name', 'id'}


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    def get_fields_dict(self):
        """Ritorna un dict[campo: (tipo, comodel)] e un dict[categoria: [lista campi]]."""
        fields_dict = {}
        group_fields = {
            'base': [],
            'one2many': [],
            'many2one': [],
            'many2many': []
        }

        for field_name, field in self._fields.items():
            # Ignora i campi esclusi o quelli con compute/related
            if field_name in EXCLUDED_FIELDS or field.compute or field.related:
                continue

            # Aggiungi al dizionario dei campi
            fields_dict[field_name] = (field.type, field.comodel_name)

            # Classifica il campo in base al tipo
            if field.type in group_fields:
                group_fields[field.type].append(field_name)
            else:
                group_fields['base'].append(field_name)

        return fields_dict, group_fields
