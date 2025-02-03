import json
import logging

import requests
from bs4 import BeautifulSoup

from odoo import models, fields

payload = ""
headers = {
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/58.0.3029.110 Safari/537.3"
}

_logger = logging.getLogger(__name__)


class WebScraper(models.Model):
    _name = 'web.scraper'
    _description = 'Modulo per il Web Scraping'

    name = fields.Char(
        string="Nome"
    )

    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Modello",
        required=True,
        ondelete="cascade",  # Evita il problema di 'restrict'
        help="Modello in cui verranno caricati i dati estratti",
    )

    # region FIELD URLs ------------------------------------------------------------------------------------------------
    urls = fields.Text(
        string="URLs",
        help="Lista di URLs da cui recuperare i dati",
    )

    urls_toggle = fields.Boolean(
        string="URLs Mostra",
        default=True,
    )

    urls_errors = fields.Text(
        string="URLs Errori",
    )

    urls_errors_toggle = fields.Boolean(
        string="URLs Errori Mostra",
        default=True,
    )

    urls_state = fields.Selection(
        string="URLs Stato",
        selection=[('url-draft', 'Url Bozza'), ('url-valid', 'Url Validi'), ('url-invalid', 'Url Non Validi')],
        default='url-draft',
    )

    urls_list = fields.Json(
        string="URLs List",
    )
    # endregion --------------------------------------------------------------------------------------------------------

    # region FIELD TAGs ------------------------------------------------------------------------------------------------
    tags = fields.Text(
        string="TAGs",
        help="Lista di TAGs CSS da cercare nel DOM per recuperare i dati",
    )

    tags_toggle = fields.Boolean(
        string="TAGs Mostra",
        default=True,
    )

    tags_errors = fields.Text(
        string="TAGs Errori",
    )

    tags_errors_toggle = fields.Text(
        string="TAGs Errori Mostra",
    )

    tags_state = fields.Selection(
        string="TAGs Stato",
        selection=[('tag-draft', 'Tags Bozza'), ('tag-valid', 'Tags Validi'), ('tag-invalid', 'Tags Non Validi')],
        default='tag-draft',
    )

    tags_dict = fields.Json(
        string="TAGs Dict",
    )

    __unique__ = fields.Json(
        string="TAGs Unique",
    )
    # endregion --------------------------------------------------------------------------------------------------------

    # region FIELD DATAs -----------------------------------------------------------------------------------------------
    datas = fields.Text(
        string="DATAs",
        help="Dati recuperati tramite lo scraping",
    )

    datas_toggle = fields.Boolean(
        string="DATAs Mostra",
        default=True,
    )

    datas_errors = fields.Text(
        string="DATAs Errori",
    )

    datas_errors_toggle = fields.Boolean(
        string="DATAs Errori Mostra",
        default=True,
    )

    datas_state = fields.Selection(
        string="DATAs Stato",
        selection=[('data-draft', 'Datas Bozza'), ('data-valid', 'Datas Validi'), ('data-invalid', 'Datas Non Validi')],
        default='data-draft',
    )

    datas_list = fields.Json(
        string="DATAs List",
    )
    # endregion --------------------------------------------------------------------------------------------------------

    # region FIELD RECs -----------------------------------------------------------------------------------------------
    records = fields.Text(
        string="RECs",
        help="Dati recuperati tramite lo scraping",
    )

    records_toggle = fields.Boolean(
        string="RECs Mostra",
        default=True,
    )

    records_errors = fields.Text(
        string="RECs Errori",
    )

    records_warnings = fields.Text(
        string="RECs Warnings",
    )

    records_errors_toggle = fields.Boolean(
        string="RECs Errori Mostra",
        default=True,
    )

    records_warnings_toggle = fields.Boolean(
        string="RECs Warnings Mostra",
        default=True,
    )

    records_state = fields.Selection(
        string="RECs Stato",
        selection=[('record-draft', 'Datas Bozza'), ('record-valid', 'Datas Validi'),
                   ('record-warning', 'Datas Warning'), ('record-invalid', 'Datas Non Validi')],
        default='record-draft',
    )

    # endregion --------------------------------------------------------------------------------------------------------

    def validate_urls(self):
        self.ensure_one()
        urls_errors = ""

        if not self.urls:
            self.urls_state = 'url-invalid'
            self.urls_errors = "Il campo URLs è vuoto, occorre impostarlo per procedere"
            return

        url_list = [url.strip() for url in self.urls.split(',')]  # Rimuove gli spazi

        for i, url in enumerate(url_list):
            try:
                response = requests.get(url, headers=headers, data=payload, timeout=5)
                response.raise_for_status()
            except Exception as e:
                urls_errors += f"URL #{i}: {url} → {str(e)}\n"

        self.urls_state = 'url-invalid' if urls_errors else 'url-valid'
        self.urls_errors = urls_errors if urls_errors else False
        self.urls_list = False if urls_errors else url_list

    def validate_tags(self):
        self.ensure_one()
        tags_errors = ""
        tags_dict = {}
        __unique__ = []

        if not self.tags:
            self.tags_state = 'tag-invalid'
            self.tags_errors = "Il campo TAGs è vuoto, occorre impostarlo per procedere."
            return

        if not self.model_id:
            self.tags_state = 'tag-invalid'
            self.tags_errors = "Il campo model_id è vuoto, occorre impostarlo per procedere."
            return

        try:
            tags_dict = json.loads(self.tags)
            model_name = self.model_id.model  # Nome del modello di destinazione
            model_rec = self.env[model_name]  # Record del modello di destinazione
            model_fields_name = list(model_rec._fields.keys())  # Nomi dei campi del modello di destinazione
            if not isinstance(tags_dict, dict):
                raise Exception("TAGs deve essere un Dizionario")

            # Controllo campo __unique__
            if '__unique__' not in tags_dict:
                raise Exception(f'Manca campo "__unique__": [<lista campi per identificare univocamente il record>].')
            __unique__ = tags_dict.get('__unique__')
            if not isinstance(__unique__, list):
                raise Exception(
                    f'Il Campo "__unique__" deve essere una "lista" di campi per identificare univocamente il record.')
            for field in __unique__:
                if field not in model_fields_name:
                    raise Exception(
                        f'Il Campo "{field}" contenuto nel campo "__unique__" non esiste nel modello "{model_name}".')
            tags_dict.pop('__unique__')

            for k, v in tags_dict.items():
                if not isinstance(k, str) and not isinstance(v, str):
                    tags_errors += f'Sia la "Chiave"="{k}" che il "Valore"="{v}" devono essere di tipo stringa.\n'
                if not isinstance(k, str):
                    tags_errors += f'La "Chiave" = "{k}" deve essere di tipo stringa.\n'
                if not isinstance(v, str):
                    tags_errors += f'Nella "Chiave" = "{k}" il "Valore" = "{v}" deve essere di tipo stringa.\n'
                if not v:
                    tags_errors += f'Nella "Chiave" = "{k}" il "Valore" = "{v}" non può essere una stringa vuota.\n'
                if k not in model_fields_name:
                    tags_errors += f'La chiave "{k}" non esiste nel modello "{model_name}.\n'

        except Exception as e:
            tags_errors = str(e)

        self.tags_state = 'tag-invalid' if tags_errors else 'tag-valid'
        self.tags_errors = tags_errors if tags_errors else False
        self.tags_dict = {} if tags_errors else tags_dict
        self.__unique__ = [] if tags_errors else __unique__

    def scrape_datas(self):
        self.ensure_one()
        datas_errors = ""
        datas_list = []

        # region CHECK: URLs, TAGs e model_id --------------------------------------------------------------------------
        if self.urls_state != "url-valid":
            self.datas_state = 'data-invalid'
            self.datas_errors = "Validare il campo URLs prima di procedere."
            return

        if self.tags_state != "tag-valid":
            self.datas_state = 'data-invalid'
            self.datas_errors = "Validare il campo TAGs prima di procedere."
            return

        if not self.urls:
            self.urls_state = 'url-invalid'
            self.urls_errors = "Il campo URLs è vuoto, occorre impostarlo per procedere"
            return

        if not self.tags:
            self.tags_state = 'tag-invalid'
            self.tags_errors = "Il campo TAGs è vuoto, occorre impostarlo per procedere."
            return

        if not self.model_id:
            self.tags_state = 'tag-invalid'
            self.tags_errors = "Il campo model_id è vuoto, occorre impostarlo per procedere."
            return
        # endregion ----------------------------------------------------------------------------------------------------

        for i, url in enumerate(self.urls_list):
            try:
                data_dict = {}
                data_dict_errors = ""
                response = requests.get(url, headers=headers, data=payload, timeout=5)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                for name_field, tag_to_scrape in self.tags_dict.items():
                    try:
                        find_tag = soup.select_one(tag_to_scrape)
                        if not find_tag:
                            raise Exception(f'Il TAG ha FALLITO la selezione.')
                        find_value = find_tag.get_text()
                        data_dict[name_field] = find_value
                    except Exception as e:
                        data_dict_errors += f' - Campo "{name_field}" - TAG "{tag_to_scrape}": {str(e)}\n'

                # Mi preparo a passare al URL successivo
                datas_list.append(data_dict)
                datas_errors += f"{data_dict_errors}"
                datas_errors += f"\n" if datas_errors else ""

            except Exception as e:
                datas_errors += f"URL #{i}: {url} → {str(e)}\n"

        self.datas_state = 'data-invalid' if datas_errors else 'data-valid'
        self.datas_errors = datas_errors if datas_errors else False
        self.datas_list = [] if datas_errors else datas_list

    def create_records(self):
        self.ensure_one()
        records_errors = ""
        records_warnings = ""

        if self.datas_state != "data-valid":
            self.records_state = 'record-invalid'
            self.records_errors = "Validare il campo Dati prima di procedere."
            return

        for i, data in enumerate(self.datas_list):
            try:
                Model = self.env[self.model_id.model]
                domain = [(x, '=', data[x]) for x in self.__unique__]
                unique_name = '_'.join([data[x] for x in self.__unique__])
                rec_exist = Model.search(domain)
                if rec_exist:
                    msg = f'SKIP - "{unique_name}" già presente nel db: {rec_exist}'
                    records_warnings += f"{msg}\n"
                else:
                    record = Model.create(data)
            except Exception as e:
                records_errors += f"REC #{i} → {str(e)}\n"

        self.records_state = 'record-invalid' if records_errors else 'record-warning' if records_warnings else 'record-valid'
        self.records_errors = records_errors if records_errors else False
        self.records_warnings = records_warnings if records_warnings else False
