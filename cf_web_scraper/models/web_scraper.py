import json
import logging

import requests
from bs4 import BeautifulSoup

from odoo import models, fields

_logger = logging.getLogger(__name__)


# STATE_LIST = [
#     ('draft', 'Bozza'),
#     ('url-validated-success', 'Url Validati'),
#     ('url-validated-error', 'Errore Validazione URL'),
#     ('data-scraped', 'Dati Estratti'),
#     ('error', 'Errore'),
#     ('data-created', 'Dati Creati')
# ]


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

    # state = fields.Selection(
    #     selection=STATE_LIST,
    #     string="Stato",
    #     default="draft",
    # )

    # box_errors = fields.Text(
    #     string="Errori Generali",
    # )
    #
    # box_tags = fields.Text(
    #     string="Errori TAGs",
    # )

    urls = fields.Text(
        string="URLs",
        help="Lista di URLs da cui recuperare i dati",
    )

    urls_errors = fields.Text(
        string="URLs Errori",
    )

    urls_state = fields.Selection(
        string="URLs Stato",
        selection=[('url-draft', 'Url Bozza'), ('url-valid', 'Url Validi'), ('url-invalid', 'Url Non Validi')],
        default='url-draft',
    )

    tags = fields.Text(
        string="TAGs",
        help="Lista di TAGs CSS da cercare nel DOM per recuperare i dati",
    )

    tags_errors = fields.Text(
        string="TAGs Errori",
    )

    tags_state = fields.Selection(
        string="TAGs Stato",
        selection=[('tag-draft', 'Bozza'), ('tag-valid', 'Validi'), ('tag-invalid', 'Non Validi')],
        default='tag-draft',
    )

    # scraped_data = fields.Text(
    #     string="Dati Estratti"
    # )

    def validate_urls(self):
        self.ensure_one()
        urls_errors = ""

        if not self.urls:
            self.urls_state = 'url-invalid'
            self.urls_errors = "Il campo URLs è vuoto"
            return

        url_list = [url.strip() for url in self.urls.split(',')]  # Rimuove gli spazi

        for i, url in enumerate(url_list):
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
            except Exception as e:
                urls_errors += f"URL #{i}: {url} → {str(e)}\n"

        self.urls_state = 'url-invalid' if urls_errors else 'url-valid'
        self.urls_errors = urls_errors if urls_errors else False

    # @api.onchange("urls")
    # def _onchange_urls(self):
    #     self.urls_state = 'invalid'

    def validate_tags(self):
        self.ensure_one()
        tags_errors = ""

        if not self.tags:
            self.tags_state = 'tag-invalid'
            self.tags_errors = "Il campo TAGs è vuoto, occorre rimpirlo per procedere."
            return

        if not self.model_id:
            self.tags_state = 'tag-invalid'
            self.tags_errors = "Il campo model_id è vuoto, occorre riempirlo per procedere."
            return

        try:
            tag_list = json.loads(self.tags)
            model_name = self.model_id.model  # Nome del modello di destinazione
            model_rec = self.env[model_name]  # Record del modello di destinazione
            model_fields_name = list(model_rec._fields.keys())  # Nomi dei campi del modello di destinazione
            if not isinstance(tag_list, dict):
                raise Exception("TAGs deve essere un Dizionario")
            for k, v in tag_list.items():
                if not isinstance(k, str) and not isinstance(v, str):
                    tags_errors += f'Sia la "Chiave"="{k}" che il "Valore"="{v}" devono essere di tipo stringa.\n'
                if not isinstance(k, str):
                    tags_errors += f'La "Chiave" = "{k}" deve essere di tipo stringa.\n'
                if not isinstance(v, str):
                    tags_errors += f'Il "Valore" = "{v}" deve essere di tipo stringa.\n'

                if k not in model_fields_name:
                    tags_errors += f'La chiave "{k}" non esiste nel modello "{model_name}.\n'
        except Exception as e:
            tags_errors = str(e)

        self.tags_state = 'tag-invalid' if tags_errors else 'tag-valid'
        self.tags_errors = tags_errors if tags_errors else False

    # @api.constrains("urls")
    # def _check_urls(self):
    #     for rec in self:
    #         if not rec.urls:
    #             continue
    #         url_list = [url.strip() for url in self.urls.split(',')]  # Rimuove gli spazi
    #         for i, url in enumerate(url_list, start=1):
    #             if ' ' in url:
    #                 raise ValidationError(f"URL #{i}: Rimuovere spazi in \"{url}\".")
    #             if not url:
    #                 raise ValidationError(f"Rimuovere URL #{i} perchè vuoto.")

    def do_scrape(self):
        self.ensure_one()

        if not self.urls:
            self.state = 'url-validated-error'
            self.box_errors = "Il campo URLs è vuoto"
            return

        url_list = [url.strip() for url in self.urls.split(',')]  # Rimuove gli spazi
        error_info = ""

        # --------------------------------------------------------------------------------------------------------------
        for i, url in enumerate(url_list):
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.find('h1', id='firstHeading')
                body = soup.find('div', id='mw-content-text')

                # Dizionario per contenere i dati estratti
                spell_data = {}

                # Estrarre il nome dell'incantesimo
                spell_data["Scuola"] = soup.find("p").text.strip()

                # Estrarre altre informazioni
                for p in soup.find_all("p")[1:]:  # Saltare il primo paragrafo
                    text = p.get_text(separator=" ").strip()
                    if ":" in text:
                        key, value = text.split(":", 1)
                        spell_data[key.strip()] = value.strip()

                if spell_data:
                    self.scraped_data = json.dumps(spell_data, indent=4)
                    self.state = 'data-scraped'
                else:
                    self.state = 'error'

            except Exception as e:
                error_info += f"URL #{i}: {url} → {str(e)}\n"

        if not error_info:
            self.state = 'url-validated-success'
            self.box_errors = False  # Nessun errore
        else:
            self.state = 'url-validated-error'
            self.box_errors = error_info  # Mostra gli errori

    # def write(self, values):
    #     tags = values.get('tags')
    #     if tags:
    #         tags_data = json.loads(tags)
    #         values['tags'] = json.dumps(tags_data, indent=4)
    #     return super(WebScraper, self).write(values)
