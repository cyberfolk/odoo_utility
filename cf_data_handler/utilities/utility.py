import json

EXCLUDED_FIELDS = {
    'write_date', 'write_uid', 'create_date', 'create_uid', 'display_name', 'id', 'x_data_id', 'x_data_hash'
}


def clean_list(_list):
    """Rimuove tutti i valori None da una lista e ritorna la lista filtrata.
        Se la lista risultante è vuota, ritorna False. """
    if not _list:
        return False
    if not isinstance(_list, list):
        raise ValueError("Il parametro deve essere una lista.")
    filtered_list = [x for x in _list if x is not None]  # Filtra i valori None
    return filtered_list if filtered_list else False  # Ritorna None se la lista filtrata è vuota


def remove_duplicates(list_dikt):
    """Rimuove i duplicati da una lista di dizionari"""
    seen = set()
    new_list = []
    for d in list_dikt:
        t = tuple(d.items())
        if t not in seen:
            seen.add(t)
            new_list.append(d)
    return new_list


def format_error(list_error):
    """Ritorna una stringa formattata partendo dalla lista dei dizionari degli errori,
    Ed elimina i dizionari duplicati nella lista"""
    list_error_lis = json.dumps(remove_duplicates(list_error))
    return (list_error_lis
            .replace("{\n", "{")
            .replace("\"\n", "\"")
            .replace("        ", "")
            .replace("    ", "")
            .replace(", ", ",\n")
            .replace(" [", "[")
            .replace("\n", " ")
            .replace("}, {", "},\n{")
            )


def join_dikt(list_dikt):
    """Ritorna un unico dizionario partendo da una lista di dizionari.
       Le chiavi duplicate combinano i valori in liste rimuovendo i duplicati,
       mantenendo un singolo valore se identico per tutte le occorrenze.
    """
    single_dikt = {}
    for d in list_dikt:
        for key, value in d.items():
            if key in single_dikt:
                if isinstance(single_dikt[key], list):
                    single_dikt[key].append(value)
                else:
                    single_dikt[key] = [single_dikt[key], value]
            else:
                single_dikt[key] = value

    # Elimina i duplicati dalle liste, se tutti i valori sono uguali, sostituisce la lista con il valore singolo.
    for key, value in single_dikt.items():
        if isinstance(value, list):
            unique_values = list(set(value))
            if len(unique_values) == 1:
                single_dikt[key] = unique_values[0]
            else:
                single_dikt[key] = unique_values

    return single_dikt
