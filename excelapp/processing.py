# excelapp/processing.py
import pandas as pd
import concurrent.futures
import requests
import json

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Token f94180ce121a4a9cd8d4e9b35e928abcedd1e3b4",
    "Organization": "164"
    }

def trigger_add_MO_v2(item):
    ChangeStatusurl = " https://app.sytex.io/api/import/SimpleOperationItemImport/go/"
    payload = json.dumps(item)

    try:
        response = requests.post(ChangeStatusurl, headers=headers,data=payload)

        if response.status_code in [200,201]:
            print("añadido corecto de item: "+item['operation'])
            mensaje = 'añadido corecto de item: '
            mensaje += (item['operation'])            
            return True, mensaje
        else:
            data = response.json()
            
            print("Datos de la API:", data)
            if 'serial_number' in item:
                print(item['serial_number'])
            print(item['operation'])
            
            mensaje = 'Datos de la API: '
            mensaje += (str(data))
            if 'serial_number' in item:
                mensaje += (', Con Num Serie: ')
                mensaje += (str(item['serial_number']))
            mensaje += (', en la MO: ')
            mensaje += (str(item['operation']))
            
            return False , mensaje, item['operation']
    except Exception as e:
        print(f"Error:  {str(e)}")
        mensaje = 'Error: '
        mensaje += (str(e))
        mensaje += (', en la MO: ')
        mensaje += (str(item['operation']))
        return False, mensaje    

def create_MO_Devol_retiro(Commit,referencia,tipo,Attribute):##
    
    ChangeStatusMOurl = "https://app.sytex.io/api/simpleoperation/"
    referencia_concatenada = " ".join(referencia)
    if tipo == 2:
        Mo_config={
        "operation_type":tipo,
        # "source_location":{"id": origen,"_class": "staff"},
        # "destination_location":{"id": destino,"_class": "client"},
        #"preparation_responsible":origen,
        "reference_number":referencia_concatenada,
        "description":Commit,
        "project":2004,
        "attributes":[Attribute]
        }
    elif tipo == 1:
        Mo_config={
        "operation_type":tipo,
        # "source_location":{"id": origen,"_class": "staff"},
        # "destination_location":{"id": destino,"_class": "client"},
        #"preparation_responsible":origen,
        "entry_type":1,
        "reference_number":referencia_concatenada,
        "description":Commit,
        "project":2004,
        "attributes":[Attribute]
        }
    
    payload = json.dumps(Mo_config)
    
    try:
        response = requests.post(ChangeStatusMOurl, headers=headers,data=payload)

        if response.status_code in [200,201]:
            print("creacion exitosa de la MO")
            data = response.json()
            print(data['code'])
            #mo.append(data['code'])
            #mo.append(data['id'])
            return data['code']

        else:
            data = response.json()
            print("Datos de la API:", data)
            print(f"Error en la solicitud. Código de estado: {response.status_code}")

    except Exception as e:
        print(f"Error en la solicitud: {str(e)}")
        return (f"Error en la solicitud: {str(e)}") 
  
def RunApi(URL):

    api_url = URL
    try:
    # Realiza una solicitud GET a la API
        response = requests.get(api_url,headers=headers)

        if response.status_code in [200,201]:
            return response.json()
        else:
            data = response.json()
            print("Datos de la API:", data)
            #mensajes_errores.append("Datos de la API:", data)
            return ("Datos de la API:", data)
               
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud a la API: {str(e)}")
        #mensajes_errores.append(f"Error al realizar la solicitud a la API: {str(e)}")
        return (f"Error al realizar la solicitud a la API: {str(e)}")
        
    except Exception as e:
        #mensajes_errores.append(f"Ocurrió un error: {str(e)}")
        print(f"Ocurrió un error: {str(e)}")
        return (f"Ocurrió un error: {str(e)}")

def FindStock(id): 
    Taskurl = " https://app.sytex.io/api/materialstock/?q="+id
    return RunApi(Taskurl)
     
def process_excel(file_path):
    # Leer el archivo Excel usando pandas
    df = pd.read_excel(file_path)

    #table = df.to_html()

    # Crea un diccionario para almacenar las filas separadas
    dict_by_cc = {}

    # Selecciona la columna 'CC'
    columnsn = df['SN']

    # Convierte la columna a una lista
    column_list_sn = [str(value) for value in columnsn]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        sn = list(executor.map(FindStock, column_list_sn))
    i=0
    list_results_dict_sn = dict(zip(column_list_sn, sn))
    # Itera sobre cada fila del DataFrame
    for _, row in df.iterrows():
        cc_value = row['CC']
        
        if sn[i]['count']==1:
            estado = 'Existe'
        else:
            estado = 'No_Existe'
            
        if cc_value not in dict_by_cc:
            dict_by_cc[cc_value] = {}
        
        if 'Existe' not in dict_by_cc[cc_value]:
            dict_by_cc[cc_value]['Existe']={}
            
        if 'No_Existe' not in dict_by_cc[cc_value]:
            dict_by_cc[cc_value]['No_Existe']={}
            
        if 'Retiro' not in dict_by_cc[cc_value][estado]:
            dict_by_cc[cc_value][estado]['Retiro']=[]
        if 'Devolucion' not in dict_by_cc[cc_value][estado]:
            dict_by_cc[cc_value][estado]['Devolucion']=[]
        
        dict_by_cc[cc_value][estado][row['Tipo Movimiento']].append(row.to_dict())
        
        i+=1
    
    #print(dict_by_cc)
    
    #table = process_dicc(dict_by_cc,list_results_dict_sn)
    
    table = "ejecucion exitosa"
    return table

def process_dicc(dict_by_cc,list_results_dict_sn):
    """
    procesamiento de diccionario.
    Metodo usado para procesar un diccionario y poder crear MO, Configurar MO e añadir items en sytex
    con el fin de facilitar el trabajo de las devoluciones y retornos.
    
    Args:
        dicc (Diccionario): Dicc que contiene informacion de seriales a mover en sytex

    Returns:
        Lista (List)
    """
    i=0
    MO_re_devo=[]
    mo = ''
    for cc in dict_by_cc:
        #rotamos por cedulas column_list_task
        print(cc)
        for estado in dict_by_cc[cc]:
            print(estado)
            
            for tipo in dict_by_cc[cc][estado]:
                Commit = ""
                referencia = []
                print(tipo)
                #mensaje1=""
                for m in dict_by_cc[cc][estado][tipo]:
                    print(m['Tarea'])
                    if pd.isna(m['Tarea']) and pd.isna(m['Pedido']):
                        mensaje1=""
                    else:
                        int_number = str(int(m['Tarea']))
                        mensaje1 = str(int_number+" - "+m['Pedido'])
    
                    Commit = str(m['Tipo Movimiento']+" entregado por "+str(m['CC'])+" Recibido por "+m['Quien Recibe'])
                    referencia.append(mensaje1)

                #crear la MO
                if estado == "Existe":
                    if tipo == "Retiro":
                        print('creamos la MO movimiento retiro')
                        mo = create_MO_Devol_retiro(Commit,referencia,2,501) #movimiento retiro
                    elif tipo == "Devolucion":
                        print('creamos la MO movimiento devolucion')
                        mo = create_MO_Devol_retiro(Commit,referencia,2,1540) #movimiento devolucion
                elif estado == "No_Existe":
                    if tipo == "Retiro":
                        print('creamos la MO entrada retiro')
                        mo = create_MO_Devol_retiro(Commit,referencia,1,501) #entrada retiro
                    elif tipo == "Devolucion":
                        print('creamos la MO entrada devoluciono')
                        mo = create_MO_Devol_retiro(Commit,referencia,1,1540) #entrada devolucion
                MO_re_devo.append(mo) 
                       
                for item in dict_by_cc[cc][estado][tipo]:
                    #añadir los item
                    print('añadimos item')
                    #print(item)
                    
                    if item['Tipo Movimiento'] == 'Retiro':
                        almacen = 'VW-0211'
                    elif item['Estado'] == 'Inactivo':
                        almacen = 'VW-0211'
                    elif item['Estado'] == 'Activo':
                        almacen = '1337'
                        
                    if pd.isna(m['Tarea']) and pd.isna(m['Pedido']):
                        referencia_str = ''
                    else:
                        int_number = str(int(m['Tarea']))
                        referencia_str = str(int_number+" - "+item['Pedido']+" obs:"+item['Comentarios'])
                        
                    if estado == "Existe":
                        count = list_results_dict_sn[item['SN']]
                        if count['count'] == 1:
                            cod_eq = count['results'][0]['material_code']
                            print('0')
                            
                        item_data = {
                        "material": cod_eq,
                        "serial_number": item['SN'],
                        "quantity": 1,
                        "source_location_type":count['results'][0]['location']['_class_name'],
                        "source_location":count['results'][0]['location']['code'],
                        "destination_location_type":'depósito virtual',
                        "destination_location":almacen,
                        "operation": mo,
                        "comments":referencia_str
                        }
                    elif estado == "No_Existe":
                        cod_eq = 'Pruebas 01'
                        
                        item_data = {
                        "material": cod_eq,
                        "serial_number": item['SN'],
                        "quantity": 1,
                        # "source_location_type":count['results'][0]['location']['_class_name'],
                        # "source_location":count['results'][0]['location']['code'],
                        "destination_location_type":'depósito virtual',
                        "destination_location":almacen,
                        "operation": mo,
                        "comments":referencia_str
                        }

                    trigger_add_MO_v2(item_data)
                    #serial,codigo serial,segun el estado(tipo destino,destino),estado,# de referencia,comentarios en el items
    print(MO_re_devo)

    return MO_re_devo

def Revision_xls(file_path):
    """
    Revisar archivo excel.
    metodo para obtener archivo xls y hacer una validacion antes de pasar al procesamiento del mismo 
    
    Args:
        file_path (XLS): xls plantilla para ingresas devolucion y retornos

    Returns:
        Booleano
    """
    return None


#process_excel('C:\\Users\\tecnologo.operacag\\Documents\\Sytex_SACC\\sytex_controller\\excelapp\\Devoluciones-Retiros.xlsx')