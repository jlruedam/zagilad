"""
Diagnóstico del bug "documento no encontrado en OPR_SALUD".

Uso:
    python manage.py diag_tipo_usuario 1003562012
    python manage.py diag_tipo_usuario 1003562012 1023456789 80123456
"""
from django.core.management.base import BaseCommand

from home.modules import utils
from home.modules.conexionBD import conexionBD


SEP = "=" * 70


def header(titulo):
    print()
    print(SEP)
    print(titulo)
    print(SEP)


class Command(BaseCommand):
    help = "Diagnostica la consulta de tipo de usuario contra OPR_SALUD."

    def add_arguments(self, parser):
        parser.add_argument(
            "documentos",
            nargs="+",
            help="Uno o más documentos a probar (ej: 1003562012)",
        )

    def handle(self, *args, **options):
        documentos = options["documentos"]
        primer_doc = documentos[0]

        # ───────────────────────────────────────────────────────────────
        # TEST 1: query individual (la vieja, ya estaba en producción)
        # ───────────────────────────────────────────────────────────────
        header(f"TEST 1: utils.obtener_tipo_usuario('{primer_doc}')  [single]")
        try:
            df = utils.obtener_tipo_usuario(primer_doc)
            print(f"Filas devueltas: {len(df)}")
            if len(df):
                print(df)
            else:
                print("(sin filas — el documento no fue encontrado en OPR_SALUD)")
        except Exception as e:
            print(f"FALLA: {type(e).__name__} -> {e}")

        # ───────────────────────────────────────────────────────────────
        # TEST 2: batch con TODOS los documentos pasados
        # ───────────────────────────────────────────────────────────────
        header(f"TEST 2: utils.obtener_tipo_usuario_batch({documentos})  [batch]")
        try:
            res = utils.obtener_tipo_usuario_batch(documentos)
            print(f"Resultado dict ({len(res)} entradas):")
            for k, v in res.items():
                print(f"  {k!r} -> {v!r}")
            faltantes = [d for d in documentos if str(d) not in res]
            if faltantes:
                print(f"Documentos que NO volvieron en el batch: {faltantes}")
        except Exception as e:
            print(f"FALLA: {type(e).__name__} -> {e}")

        # ───────────────────────────────────────────────────────────────
        # TEST 3: SQL crudo con IN (replica exacta del batch)
        # ───────────────────────────────────────────────────────────────
        header("TEST 3: SQL crudo con IN (replica del batch, sin CASE)")
        docs_in = ", ".join(f"''{d}''" for d in documentos)
        query_in = f"""
            SELECT * FROM OPENQUERY(OPR_SALUD, '
            SELECT NRO_TIPO_IDENTIFICACION, AFIC_REGIMEN, TIPO_AFILIADO
            FROM OASIS.T_AFILIADO_MUTUALSER_EP
            WHERE NRO_TIPO_IDENTIFICACION IN ({docs_in})
            ')
        """
        print("SQL:")
        print(query_in)
        try:
            rows = conexionBD(query_in)
            print(f"Filas: {len(rows)}")
            for r in rows:
                print(f"  {r}")
        except Exception as e:
            print(f"FALLA: {type(e).__name__} -> {e}")

        # ───────────────────────────────────────────────────────────────
        # TEST 4: SQL crudo con = (replica de la query single)
        # ───────────────────────────────────────────────────────────────
        header(f"TEST 4: SQL crudo con = (replica del single, sin CASE) — {primer_doc}")
        query_eq = f"""
            SELECT * FROM OPENQUERY(OPR_SALUD, '
            SELECT NRO_TIPO_IDENTIFICACION, AFIC_REGIMEN, TIPO_AFILIADO
            FROM OASIS.T_AFILIADO_MUTUALSER_EP
            WHERE NRO_TIPO_IDENTIFICACION = ''{primer_doc}''
            ')
        """
        print("SQL:")
        print(query_eq)
        try:
            rows = conexionBD(query_eq)
            print(f"Filas: {len(rows)}")
            for r in rows:
                print(f"  {r}")
        except Exception as e:
            print(f"FALLA: {type(e).__name__} -> {e}")

        # ───────────────────────────────────────────────────────────────
        # TEST 5: tamaño del SQL del batch real (con CASE completo)
        # ───────────────────────────────────────────────────────────────
        header("TEST 5: tamaño del SQL del batch real (CASE completo)")
        from home.modules.utils import _BATCH_SIZE_TIPO_USUARIO
        # reconstruimos el SQL exacto que arma obtener_tipo_usuario_batch
        sql_batch = f"""
            SELECT * FROM OPENQUERY(OPR_SALUD, '
            SELECT
                NRO_TIPO_IDENTIFICACION,
                CASE
                    WHEN AFIC_REGIMEN = ''S'' AND TIPO_AFILIADO IN (''BENEFICIARIO'', ''ND'', ''SEGUNDO COTIZANTE'', ''CABEZA DE FAMLIA'', ''COTIZANTE'', ''f'', ''O'') THEN ''04''
                    WHEN AFIC_REGIMEN = ''C'' AND TIPO_AFILIADO = ''CABEZA DE FAMLIA'' THEN ''02''
                    WHEN AFIC_REGIMEN = ''C'' AND TIPO_AFILIADO IN (''ND'', ''f'', ''COTIZANTE'', ''SEGUNDO COTIZANTE'') THEN ''01''
                    WHEN AFIC_REGIMEN = ''C'' AND TIPO_AFILIADO = ''BENEFICIARIO'' THEN ''02''
                    WHEN AFIC_REGIMEN = ''C'' AND TIPO_AFILIADO = ''ADICIONAL'' THEN ''03''
                    ELSE AFIC_REGIMEN
                END AS ID_TIPO_AFILIADO
            FROM OASIS.T_AFILIADO_MUTUALSER_EP
            WHERE NRO_TIPO_IDENTIFICACION IN ({docs_in})
            ')
        """
        print(f"BATCH_SIZE configurado: {_BATCH_SIZE_TIPO_USUARIO}")
        print(f"Documentos en este test: {len(documentos)}")
        print(f"Tamaño total del SQL: {len(sql_batch)} bytes")
        # estimar el tamaño con el batch máximo, asumiendo doc de 10 dígitos
        bytes_por_doc = len("''1234567890'', ")
        overhead = len(sql_batch) - len(docs_in)
        sql_full_estimado = overhead + bytes_por_doc * _BATCH_SIZE_TIPO_USUARIO
        print(f"Tamaño estimado con batch lleno ({_BATCH_SIZE_TIPO_USUARIO} docs): ~{sql_full_estimado} bytes")
        print("(OPENQUERY tiene un límite de ~8000 bytes en la cadena interna)")

        try:
            rows = conexionBD(sql_batch)
            print(f"Filas con CASE completo: {len(rows)}")
            for r in rows:
                print(f"  {r}")
        except Exception as e:
            print(f"FALLA con CASE completo: {type(e).__name__} -> {e}")

        # ───────────────────────────────────────────────────────────────
        # TEST 6: estructura de la tabla T_AFILIADO_MUTUALSER_EP
        # ───────────────────────────────────────────────────────────────
        header("TEST 6: columnas de OASIS.T_AFILIADO_MUTUALSER_EP")
        sql_cols = """
            SELECT * FROM OPENQUERY(OPR_SALUD, '
            SELECT column_name, data_type, data_length
            FROM all_tab_columns
            WHERE owner = ''OASIS'' AND table_name = ''T_AFILIADO_MUTUALSER_EP''
            ORDER BY column_id
            ')
        """
        try:
            rows = conexionBD(sql_cols)
            print(f"Columnas encontradas: {len(rows)}")
            for r in rows:
                print(f"  {r}")
        except Exception as e:
            print(f"FALLA: {type(e).__name__} -> {e}")

        # ───────────────────────────────────────────────────────────────
        # TEST 7: muestra de 3 filas para ver formato real de los datos
        # ───────────────────────────────────────────────────────────────
        header("TEST 7: 3 filas de muestra (cualquier documento)")
        sql_sample = """
            SELECT * FROM OPENQUERY(OPR_SALUD, '
            SELECT * FROM OASIS.T_AFILIADO_MUTUALSER_EP WHERE ROWNUM <= 3
            ')
        """
        try:
            rows = conexionBD(sql_sample)
            print(f"Filas: {len(rows)}")
            for r in rows:
                print(f"  {r}")
        except Exception as e:
            print(f"FALLA: {type(e).__name__} -> {e}")

        # ───────────────────────────────────────────────────────────────
        # TEST 8: búsqueda flexible del documento (LIKE)
        # ───────────────────────────────────────────────────────────────
        header(f"TEST 8: búsqueda LIKE '%{primer_doc}%' en NRO_TIPO_IDENTIFICACION")
        sql_like = f"""
            SELECT * FROM OPENQUERY(OPR_SALUD, '
            SELECT NRO_TIPO_IDENTIFICACION, AFIC_REGIMEN, TIPO_AFILIADO
            FROM OASIS.T_AFILIADO_MUTUALSER_EP
            WHERE NRO_TIPO_IDENTIFICACION LIKE ''%{primer_doc}%''
            AND ROWNUM <= 10
            ')
        """
        try:
            rows = conexionBD(sql_like)
            print(f"Filas: {len(rows)}")
            for r in rows:
                print(f"  {r}")
            if not rows:
                print("(no hay match ni con LIKE — el documento no está en esta tabla bajo esa columna)")
        except Exception as e:
            print(f"FALLA: {type(e).__name__} -> {e}")

        # ───────────────────────────────────────────────────────────────
        # TEST 9: total de filas en la tabla (sanidad)
        # ───────────────────────────────────────────────────────────────
        header("TEST 9: COUNT(*) de OASIS.T_AFILIADO_MUTUALSER_EP")
        sql_count = """
            SELECT * FROM OPENQUERY(OPR_SALUD, '
            SELECT COUNT(*) AS total FROM OASIS.T_AFILIADO_MUTUALSER_EP
            ')
        """
        try:
            rows = conexionBD(sql_count)
            print(f"Total de filas: {rows[0][0] if rows else '?'}")
        except Exception as e:
            print(f"FALLA: {type(e).__name__} -> {e}")

        print()
        print(SEP)
        print("FIN DEL DIAGNÓSTICO")
        print(SEP)
