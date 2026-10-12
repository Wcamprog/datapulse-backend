import datetime
import requests
from django.conf import settings
from django.db import transaction
from .models import Country, ExchangeRate, EconomicIndicator


class DataSyncService:
    WORLD_BANK_INDICATORS = {
        'NY.GDP.MKTP.CD': {'tipo': 'PIB', 'unidad': 'USD'},
        'FP.CPI.TOTL.ZG': {'tipo': 'INFLACION', 'unidad': 'PORCENTAJE'},
        'SL.UEM.TOTL.ZS': {'tipo': 'DESEMPLEO', 'unidad': 'PORCENTAJE'},
        'NE.RSB.GNFS.ZS': {'tipo': 'BALANZA_COMERCIAL', 'unidad': 'PORCENTAJE'},
        'GC.DOD.TOTL.GD.ZS': {'tipo': 'DEUDA_PIB', 'unidad': 'PORCENTAJE'},
        'NY.GDP.PCAP.CD': {'tipo': 'PIB_PERCAPITA', 'unidad': 'USD'}
    }

    REGIONES_LATAM_MAP = {
        'CO': 'ANDINA', 'PE': 'ANDINA', 'EC': 'ANDINA', 'BO': 'ANDINA', 'VE': 'ANDINA',
        'AR': 'CONO_SUR', 'CL': 'CONO_SUR', 'BR': 'CONO_SUR', 'UY': 'CONO_SUR', 'PY': 'CONO_SUR',
        'MX': 'CENTROAMERICA', 'PA': 'CENTROAMERICA', 'CR': 'CENTROAMERICA', 'GT': 'CENTROAMERICA',
        'HN': 'CENTROAMERICA', 'SV': 'CENTROAMERICA', 'NI': 'CENTROAMERICA',
        'DO': 'CARIBE', 'CU': 'CARIBE', 'PR': 'CARIBE'
    }

    @classmethod
    def sync_all(cls):
        try:
            res_paises = cls._sync_rest_countries()
            res_wb = cls._sync_world_bank()
            res_tasas = cls._sync_exchange_rates()

            return True, f"Sincronización completa. {res_paises} | {res_wb} | {res_tasas}"
        except Exception as e:
            return False, f"Error durante la sincronización: {str(e)}"

    @classmethod
    def _sync_rest_countries(cls):
        """
        Sincroniza y actualiza los países que ya existen en la base de datos.
        """
        paises_existentes = Country.objects.filter(activo=True)
        if not paises_existentes.exists():
            return "No hay países activos en la base de datos para sincronizar"

        api_key = getattr(settings, 'API_KEY_COUNTRIES', '')
        headers = {'Authorization': f"Bearer {api_key}"} if api_key else {}

        actualizados = 0

        with transaction.atomic():
            for pais in paises_existentes:
                url = f"https://api.restcountries.com/countries/v5?q={pais.nombre.strip()}&pretty=1"

                try:
                    res = requests.get(url, headers=headers, timeout=10)
                    if res.status_code != 200:
                        continue

                    json_data = res.json()
                    objects = json_data.get('data', {}).get('objects', [])
                    if not objects:
                        continue

                    item = objects[0]

                    currencies = item.get('currencies', [])
                    if currencies and isinstance(currencies, list):
                        pais.moneda_codigo = currencies[0].get('code', pais.moneda_codigo)
                        pais.moneda_nombre = currencies[0].get('name', pais.moneda_nombre)

                    capitals = item.get('capitals', [])
                    if capitals and isinstance(capitals, list):
                        coords = capitals[0].get('coordinates', {})
                        lat = coords.get('lat')
                        lng = coords.get('lng')
                    else:
                        lat = item.get('coordinates', {}).get('lat', pais.latitud)
                        lng = item.get('coordinates', {}).get('lng', pais.longitud)

                    if lat is not None:
                        pais.latitud = str(lat)
                    if lng is not None:
                        pais.longitud = str(lng)

                    if item.get('population'):
                        pais.poblacion = item.get('population')

                    if pais.codigo_iso in cls.REGIONES_LATAM_MAP:
                        pais.region = cls.REGIONES_LATAM_MAP[pais.codigo_iso]

                    pais.save()
                    actualizados += 1

                except Exception as ex:
                    print(f"Error sincronizando país {pais.nombre}: {ex}")
                    continue

        return f"Países actualizados: {actualizados} (de {paises_existentes.count()} existentes)"

    @classmethod
    def _sync_world_bank(cls):
        paises = Country.objects.filter(activo=True)
        registros = 0

        for pais in paises:
            for wb_code, config in cls.WORLD_BANK_INDICATORS.items():
                db_tipo = config['tipo']
                db_unidad = config['unidad']

                url = f"https://api.worldbank.org/v2/country/{pais.codigo_iso}/indicator/{wb_code}?date=2021:2026&format=json"
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        data_json = response.json()
                        if isinstance(data_json, list) and len(data_json) > 1:
                            datos_wb = data_json[1]
                            if isinstance(datos_wb, list):
                                for dato in datos_wb:
                                    if isinstance(dato, dict) and dato.get('value') is not None:
                                        EconomicIndicator.objects.update_or_create(
                                            pais=pais,
                                            tipo=db_tipo,
                                            anio=int(dato.get('date', 0)),
                                            defaults={
                                                'valor': dato.get('value'),
                                                'unidad': db_unidad,
                                                'fuente': 'WORLD_BANK',
                                            }
                                        )
                                        registros += 1
                except Exception:
                    continue
        return f"Indicadores macroeconómicos guardados: {registros}"

    @classmethod
    def _sync_exchange_rates(cls):
        api_url = getattr(settings, 'API_URL', None)
        if not api_url or not str(api_url).strip():
            raise ValueError(
                "La URL de la API de tipos de cambio no existe o no está configurada.")

        try:
            response = requests.get(api_url.strip(), timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"No fue posible conectar con la URL de tipos de cambio '{api_url}': {str(e)}")

        rates = data.get('rates', {}) if isinstance(data, dict) else {}
        if not rates:
            raise ValueError(f"La URL '{api_url}' no devolvió la estructura esperada de tasas de cambio ('rates').")

        paises = Country.objects.filter(activo=True)
        tasas_creadas = 0
        hoy = datetime.date.today()

        with transaction.atomic():
            for pais in paises:
                if isinstance(rates, dict):
                    tasa_actual = rates.get(pais.moneda_codigo)
                    if tasa_actual:
                        _, created = ExchangeRate.objects.update_or_create(
                            moneda_origen=pais.moneda_codigo,
                            moneda_destino="USD",
                            fecha=hoy,
                            defaults={
                                'tasa': tasa_actual,
                                'fuente': 'EXCHANGE_RATE_API'
                            }
                        )
                        if created:
                            tasas_creadas += 1

        return f"Tasas registradas hoy: {tasas_creadas}"

    @classmethod
    def consultar_pais_externo(cls, query):
        """
        Consulta REST Countries v5 para autocompletar el formulario de creación.
        Valida que el país pertenezca estrictamente a Latinoamérica.
        """
        api_key = getattr(settings, 'API_KEY_COUNTRIES', '')
        headers = {'Authorization': f"Bearer {api_key}"} if api_key else {}

        url = f"https://api.restcountries.com/countries/v5?q={query.strip()}&pretty=1"
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()

        data = res.json()
        objects = data.get('data', {}).get('objects', [])
        if not objects:
            raise ValueError(f"No se encontró información de '{query}'.")

        item = objects[0]
        iso = item.get('codes', {}).get('alpha_2', '').upper()

        if iso not in cls.REGIONES_LATAM_MAP:
            nombre = item.get('names', {}).get('common', query)
            raise ValueError(f"El país '{nombre}' ({iso}) no pertenece a Latinoamérica.")

        nombre = (
            item.get('names', {}).get('native', {}).get('spa', {}).get('common')
            or item.get('names', {}).get('common', query)
        )

        currencies = item.get('currencies', [])
        if currencies and isinstance(currencies, list):
            moneda_codigo = currencies[0].get('code', 'USD')
            moneda_nombre = currencies[0].get('name', 'Dólar')
        else:
            moneda_codigo, moneda_nombre = "USD", "Dólar"

        capitals = item.get('capitals', [])
        if capitals and isinstance(capitals, list):
            coords = capitals[0].get('coordinates', {})
            lat = coords.get('lat')
            lng = coords.get('lng')
        else:
            lat = item.get('coordinates', {}).get('lat', 0.0)
            lng = item.get('coordinates', {}).get('lng', 0.0)

        poblacion = item.get('population', 0)

        return {
            "codigo_iso": iso,
            "nombre": nombre,
            "moneda_codigo": moneda_codigo,
            "moneda_nombre": moneda_nombre,
            "region": cls.REGIONES_LATAM_MAP[iso],
            "latitud": str(lat),
            "longitud": str(lng),
            "poblacion": poblacion,
            "activo": True
        }