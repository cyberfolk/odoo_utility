# Menu interattivo per avviare una shell Odoo.
# Flusso:
# 1. mostra la lista custom_path
# 2. imposta database e custom_path in base alla scelta
# 3. chiede conferma del database proposto
# 4. se necessario permette di inserirne uno diverso
# 5. lancia `odoo-bin shell` con gli addons standard + custom addons

echo "Scegli il cliente. Inserisci il numero:"

select CHOICE in HIC RIFO AUTEL METEL BUSSOLA CHECKPRO COCKTAIL OLIVIERI; do
  case "$CHOICE" in
         OPZ_1)  DB_NAME="db_name_opz_1";  CUSTOM_PATH="path_opz_1" ;;
         OPZ_2)  DB_NAME="db_name_opz_2";  CUSTOM_PATH="path_opz_2" ;;
         OPZ_3)  DB_NAME="db_name_opz_3";  CUSTOM_PATH="path_opz_3" ;;
    *) echo "Scelta non valida: $REPLY"; exit 1 ;;
  esac
  break
done

echo ""

while true; do
  read -r -p "Sto per lanciare il database \"$DB_NAME\". Confermi? [s/n]: " CONFIRM
  case "$CONFIRM" in
    s|S) break                                                   ;;
    n|N) read -r -p "Inserisci il nuovo nome database: " DB_NAME ;;
      *) echo "Risposta non valida. Scrivi s oppure n."          ;;
  esac
done

echo ""

cd "/c/Users/andre/odoo-17" || exit 1

python odoo/odoo-bin shell \
  -c ./odoo.conf \
  -d "$DB_NAME" \
  --addons-path="odoo/addons,cyberfolk/$CUSTOM_PATH"
