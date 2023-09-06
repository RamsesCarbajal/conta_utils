import pdfplumber
import re
import csv
import os

TABLE_HEADER = "FECHA REFERENCIA CONCEPTO CARGOS ABONOS SALDO"
months_string = {"ENE": "ENERO",
                 "FEB": "FEBRERO",
                 "MAR": "MARZO",
                 "ABR": "ABRIL",
                 "MAY": "MAYO",
                 "JUN": "JUNIO",
                 "JUL": "JULIO",
                 "AGO": "AGOSTO",
                 "SEP": "SEPTIEMBRE",
                 "OCT": "OCTUBRE",
                 "NOV": "NOVIEMBRE",
                 "DIC": "DICIEMBRE"}

months_integer = {"ENE": 1,
                  "FEB": 2,
                  "MAR": 3,
                  "ABR": 4,
                  "MAY": 5,
                  "JUN": 6,
                  "JUL": 7,
                  "AGO": 8,
                  "SEP": 9,
                  "OCT": 10,
                  "NOV": 11,
                  "DIC": 12}

def get_files(path):
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            yield file

def get_list_of_files(path):
    all_files=[]
    for file in get_files(path):
        all_files.append(f'{path}/{file}')
    return all_files


def build_date(year, string_date):
    month_day = string_date.split(" ")
    return f'{month_day[1]}/{month_day[0]}/{year}'


def create_dict(dates, references, details, debits, credits, balance, year):
    current_row = ""
    current_movement = ""
    banking_movements = []
    regex_list = {"DEPOSITOSPEI": r'^CLAVE DE RASTREO',
                  "DEPOSITOTEF": r'.*\d{3}$',
                  "TRASPASOSPEIINBURED": r'.*RFC [A-Za-z0-9]{12,13}$',
                  "TRANSFERENCIASPEI": r'.*RFC [A-Za-z0-9]{12,13}$'}
    while len(details) > 0:
        row = details.pop(0)
        #print(row)
        #revisar aqui
        # if (current_movement == "TRASPASO"):
        #     if len(current_row.replace(" ", "")) != 12 and len(current_row.replace(" ", "")) != 13:
        #         banking_movements.append({"date": build_date(year, dates.pop(0)),
        #                                   "details": f'{current_movement}',
        #                                   "reference": references.pop(0),
        #                                   "debit": debits.pop(0),
        #                                   "balance": balance.pop(0)})
        #         current_row = row
        #         current_movement = row
        # hasta revisar aqui
        if current_movement != "":
            current_row += f'\n{row}'
            if current_movement == "TRASPASO ENTRE CUENTAS":
                if len(row) == 11:
                    banking_movements.append({"date": build_date(year, dates.pop(0)),
                                              "details": current_row,
                                              "reference": references.pop(0),
                                              "credit": credits.pop(0),
                                              "balance": balance.pop(0)})
                    current_row = ""
                    current_movement = ""
                    continue

            if current_movement == "DEVOLUCION SPEI":
                if " :" in current_row:
                    banking_movements.append({"date": build_date(year, dates.pop(0)),
                                              "details": current_row,
                                              "reference": references.pop(0),
                                              "credit": credits.pop(0),
                                              "balance": balance.pop(0)})
                    current_row = ""
                    current_movement = ""
                    continue
            if current_movement == "DEPOSITO SPEI" or current_movement == "DEPOSITO TEF":
                #print(current_row)
                if re.match(regex_list[current_movement.replace(" ", "")], row):
                    #if "002601002103310000556804" in current_row:
                    #    print("aqui")
                    banking_movements.append({"date": build_date(year, dates.pop(0)),
                                              "details": current_row,
                                              "reference": references.pop(0),
                                              "credit": credits.pop(0),
                                              "balance": balance.pop(0)})
                    current_row = ""
                    current_movement = ""

                    continue
            if current_movement == "TRASPASO SPEI INBURED" or current_movement == "TRANSFERENCIA SPEI":

                if (re.match(regex_list[current_movement.replace(" ", "")], row)
                        or "RFC NO DISPONIBLE" in current_row):
                    banking_movements.append({"date": build_date(year, dates.pop(0)),
                                              "details": current_row,
                                              "reference": references.pop(0),
                                              "debit": debits.pop(0),
                                              "balance": balance.pop(0)})
                    current_row = ""
                    current_movement = ""

                    continue
            if current_movement == "CARGO EN CUENTA":
                if "REF-" in row:
                    banking_movements.append({"date": build_date(year, dates.pop(0)),
                                              "details": current_row,
                                              "reference": references.pop(0),
                                              "debit": debits.pop(0),
                                              "balance": balance.pop(0)})
                    current_row = ""
                    current_movement = ""
                    continue

            if (current_movement == "COMISION POR MOVIMIENTOS INBURED"
                    or current_movement == "IVA COMISION POR MOVIMIENTOS INBURED"
                    or current_movement == "TRANSFERENCIA TEF"
                    or current_movement == "IVA COMISION MANEJO DE CUENTA"
                    or current_movement == "TRASPASO"
                    or current_movement == "IVA POR TRANSFERENCIA DE FONDOS"):
                #print(current_row)
                banking_movements.append({"date": build_date(year, dates.pop(0)),
                                          "details": current_row,
                                          "reference": references.pop(0),
                                          "debit": debits.pop(0),
                                          "balance": balance.pop(0)})
                current_row = ""
                current_movement = ""
                continue

            if (current_movement == "DEPOSITO INBURED"
                    or current_movement == "DEPOSITO CHEQUES SBC"
                    or current_movement == "DEPOSITO EN CUENTA"):
                banking_movements.append({"date": build_date(year, dates.pop(0)),
                                          "details": current_row,
                                          "reference": references.pop(0),
                                          "credit": credits.pop(0),
                                          "balance": balance.pop(0)})
                current_row = ""
                current_movement = ""
                continue

        if row == "BALANCE INICIAL":
            banking_movements.append(
                {"date": build_date(year, dates.pop(0)), "details": row, "balance": balance.pop(0)})

            continue
        if row == "INTERESES GANADOS":
            banking_movements.append({"date": build_date(year, dates.pop(0)),
                                      "details": row,
                                      "reference": references.pop(0),
                                      "credit": credits.pop(0),
                                      "balance": balance.pop(0)})
            continue
        if (row == "DEPOSITO SPEI"
                or row == "DEPOSITO TEF"
                or row == "TRASPASO SPEI INBURED"
                or row == "TRASPASO"
                or row == "COMISION POR MOVIMIENTOS INBURED"
                or row == "IVA COMISION POR MOVIMIENTOS INBURED"
                or row == "CARGO EN CUENTA"
                or row == "TRANSFERENCIA TEF"
                or row == "TRANSFERENCIA SPEI"
                or row == "DEPOSITO INBURED"
                or row == "DEPOSITO CHEQUES SBC"
                or row == "DEPOSITO EN CUENTA"
                or row == "IVA COMISION MANEJO DE CUENTA"
                or row == "IVA POR TRANSFERENCIA DE FONDOS"
                or row == "DEVOLUCION SPEI"
                or row == "TRASPASO ENTRE CUENTAS"):
            current_row = row
            current_movement = row
            continue
        if (row == "ISR RETENIDO"):
            banking_movements.append({"date": build_date(year, dates.pop(0)),
                                      "details": row,
                                      "reference": references.pop(0),
                                      "debit": debits.pop(0),
                                      "balance": balance.pop(0)})
            current_row = ""
            current_movement = ""
            continue

        if "DEVOLUCION COMISION INBURRED" == row :
            banking_movements.append({"date": build_date(year, dates.pop(0)),
                                      "details": row,
                                      "reference": references.pop(0),
                                      "credit": credits.pop(0),
                                      "balance": balance.pop(0)})
            current_row = ""
            current_movement = ""
            continue
        if current_movement == "":
            #print("condicion especial")

            #print(row)
            banking_movements.append({"date": build_date(year, dates.pop(0)),
                                      "details": row,
                                      "reference": references.pop(0),
                                      "debit": debits.pop(0),
                                      "balance": balance.pop(0)})
            current_row = ""
            current_movement = ""

    if current_movement != "":
        banking_movements.append({"date": build_date(year, dates.pop(0)),
                                  "details": current_movement,
                                  "reference": references.pop(0),
                                  "debit": debits.pop(0),
                                  "balance": balance.pop(0)})

        current_row = ""
        current_movement = ""
    return banking_movements


# Open the PDF file

def csv_creation(array_of_dict, headers):
    with open('estado_de_cuenta.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(array_of_dict)


def enrich_data_companies(movements):
    for move in movements:
        details_list = move["details"].split("\n")
        if "DEPOSITO SPEI" in move["details"]:
            move["company"] = details_list[1]
            move["ref_trans"] = details_list[2]
            continue
        if "DEPOSITO TEF" in move["details"]:
            move["company"] = details_list[1]
            continue
        if "TRASPASO SPEI INBURED" in move["details"]:
            move["company"] = details_list[1]
            move["ref_trans"] = details_list[3]
            continue
        if details_list[0] not in ["TRASPASO", "COMISION POR MOVIMIENTOS", "IVA COMISION POR MOVIMIENTOS",
                                   "INTERESES GANADOS", "ISR RETENIDO"]:
            move["company"] = details_list[0]


def enrich_dates(movements):
    for move in movements:
        date_array = move["date"].split("/")
        day = date_array[0]
        raw_string_date = date_array[1]
        month = months_string[raw_string_date]
        year = date_array[2]
        correct_date = f'{day}/{month}/{year}'
        move["date"] = correct_date
        move["date_day"] = int(day)
        move["date_month"] = months_integer[raw_string_date]
        move["date_year"] = int(year)


def get_cargos_abonos(movements):
    all_cargos = 0.0
    all_abonos = 0.0

    for move in movements:
        if "debit" in move:
            all_cargos += float(move["debit"].replace(",", ""))
        if "credit" in move:
            all_abonos += float(move["credit"].replace(",", ""))
    return {"cargo_total": round(all_cargos,2), "abono_total": round(all_abonos,2)}

def transform_movements_to_table(array):
    main_table = [TABLE_HEADER.split(" ")]
    for movement in array:
        date = movement["date"]
        details = movement["details"]

        balance = movement["balance"]
        ref = ""
        debit = ""
        credit = ""
        if "reference" in movement:
            ref = movement["reference"]
        if "credit" in movement:
            credit = movement["credit"]
        if "debit" in movement:
            debit = movement["debit"]
        main_table.append([date, ref, details, debit, credit, balance])
    return main_table


def prepare_edo_cuenta(page):
    operaciones = ["BALANCE INICIAL",
                    "INTERESES GANADOS",
                    "DEPOSITO SPEI",
                    "TRASPASO SPEI INBURED",
                    "TRASPASO",
                    "COMISION POR MOVIMIENTOS INBURED",
                    "IVA COMISION POR MOVIMIENTOS INBURED",
                    "CARGO EN CUENTA",
                    "TRANSFERENCIA TEF",
                    "TRANSFERENCIA SPEI",
                    "DEPOSITO INBURED",
                    "DEPOSITO CHEQUES SBC",
                    "DEPOSITO EN CUENTA",
                    "IVA COMISION MANEJO DE CUENTA",
                    "IVA POR TRANSFERENCIA DE FONDOS",
                    "ISR RETENIDO",
                    "DEVOLUCION COMISION INBURRED",
                    "COMISION POR TRANSFERENCIA DE FONDOS",
                    "DEVOLUCION SPEI",
                    "TRASPASO ENTRE CUENTAS"]
    total_rows = len(page)
    current_row = 0
    while current_row < total_rows:
        if page[current_row] == "TRASPASO" or page[current_row] == "CARGO EN CUENTA":
            #print(f'current_row: {current_row}')
            if current_row+1 < total_rows and page[current_row+1] in operaciones:
                page.insert(current_row + 1,"REF-")
                total_rows = len(page)

        current_row += 1
    #print("-.-..-.-.-.-.--.-")
    #print(page)
    #print("-.-..-.-.-.-.--.-")
    return page

#estados_de_cuenta=get_list_of_files(r'pruebas/inbursa')
estados_de_cuenta=get_list_of_files(r'estados_de_cuenta/inbursa')
movimientos_globales=[]
for edo_cuenta in estados_de_cuenta:
    print(f'edo_cuenta: {edo_cuenta}')
    with pdfplumber.open(edo_cuenta) as pdf:

        # Extract text from each page
        for page in pdf.pages:

            page_text = page.extract_text()
            row_with_date_prefix = "PERIODO Del"
            abono_prefix = "ABONOS "
            cargo_prefix = "CARGOS "
            periodo_raw_string = ""
            abono_raw_string = ""
            cargo_raw_string = ""
            abono_raw = None
            cargo_raw = None
            period_year = None
            pattern = r"PERIODO\s+Del\s+(\d{1,2})\s+\w+\s+(\d{4})\s+al\s+(\d{1,2}).*"
            abono_pattern = r'^(ABONOS\s+(\d{1,3}(?:,\d{3})*(?:\.\d+)?))'
            cargo_pattern = r'^(CARGOS\s+(\d{1,3}(?:,\d{3})*(?:\.\d+)?))'

            #enriched_page = prepare_edo_cuenta(page_text.split("\n"))

            for row in page_text.split("\n"):
                if row_with_date_prefix in row:
                    periodo_raw_string = row

                if abono_prefix in row and " ABONOS " not in row:
                    abono_raw_string = row
                if cargo_prefix in row and " CARGOS " not in row:
                    cargo_raw_string = row

            match = re.search(pattern, periodo_raw_string)
            cargo_match = re.search(cargo_pattern, cargo_raw_string)
            abono_match = re.search(abono_pattern, abono_raw_string)

            if match:
                period_year = match.group(2)
                print(f'el año del periodo {period_year}')

            if cargo_match:
                cargo_raw = cargo_match.group(2)
                cargo_raw = cargo_raw.replace(",", "")
                cargo_raw = float(cargo_raw)
                print(f'CARGO total: {cargo_raw}')

            if abono_match:
                abono_raw = abono_match.group(2)
                abono_raw = abono_raw.replace(",", "")
                abono_raw = float(abono_raw)
                print(f'ABONO total: {abono_raw}')

            break
        # Extract tables from each page
        all_raw_movements = []
        for page in pdf.pages:

            tables = page.extract_tables()

            for table in tables:
                if table[0][0] != TABLE_HEADER:
                    continue
                # print(f'tabla: {table}')
                for row in table:
                    if row[0] == TABLE_HEADER:
                        continue

                    dates = row[0]
                    references = row[1]
                    details = row[2]
                    enriched_details = prepare_edo_cuenta(details.split("\n"))
                    debits = row[3]
                    credits = row[4]
                    balance = row[5]
                    raw_movements = create_dict(dates.split("\n"),
                                                references.split("\n"),
                                                enriched_details,
                                                debits.split("\n"),
                                                credits.split("\n"),
                                                balance.split("\n"),
                                                period_year)

                    # print(f'page_table: {page_table}')
                    all_raw_movements.extend(raw_movements)



        # csv_table = transform_movements_to_table(all_raw_movements)
        # move["date_day"] = int(day)
        # move["date_month"] = months_integer[raw_string_date]
        # move["date_year"] = int(year)

        enrich_data_companies(all_raw_movements)
        enrich_dates(all_raw_movements)

        ## Validation section
        validaciones = get_cargos_abonos(all_raw_movements)
        valid_edo_cuenta = False
        if(round(cargo_raw,2) == validaciones["cargo_total"] and round(abono_raw,2) == validaciones["abono_total"]):
            valid_edo_cuenta = True
        print(f'estado de cuenta: {edo_cuenta} es {valid_edo_cuenta}')
        if not valid_edo_cuenta:
            print(validaciones)
        movimientos_globales.extend(all_raw_movements)

csv_headres = ["date", "reference", "details", "debit", "credit", "balance", "company",
                       "ref_trans", "date_year", "date_month", "date_day"]
csv_creation(movimientos_globales, csv_headres)


