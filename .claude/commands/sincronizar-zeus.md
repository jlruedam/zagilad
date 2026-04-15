Guía para sincronizar los datos de referencia desde la API de ZEUS a la base de datos local de Zagilad.

Zagilad mantiene una copia local de datos de ZEUS en la app `zeus_mirror`. Estos datos deben sincronizarse periódicamente o cuando aparecen inconsistencias del tipo "no encontrado".

## Datos a sincronizar y sus endpoints

Accede a `/consultasZeus/` en el servidor para usar la interfaz de sincronización, o llama directamente a los endpoints:

| Dato | Endpoint | Modelo destino | Cuándo sincronizar |
|---|---|---|---|
| Médicos | `/consultarMedicos/` | `zeus_mirror.Medico` | Si hay "Medico no encontrado" |
| Finalidades | `/listarFinalidades/` | `zeus_mirror.Finalidad` | Si hay "Finalidad no encontrada" |
| Contratos | `/listarContratos/` | `zeus_mirror.Contrato` | Si hay cambios en contratos |
| Unidades funcionales | `/listarUnidadesFuncionales/` | `zeus_mirror.UnidadFuncional` | Raramente |
| Centros de costo | `/listarCentrosCostos/` | `zeus_mirror.CentroCosto` | Raramente |
| Puntos de atención | `/listarPuntosAtencion/` | `zeus_mirror.PuntoAtencion` | Raramente |
| Tipos de servicio | `/listarTiposServicios/` | `zeus_mirror.TipoServicio` | Raramente |
| Sedes | `/listarSeriales/` | `zeus_mirror.Sede` | Raramente |

## Flujo recomendado cuando hay inconsistencias masivas

1. Sincronizar **Médicos** (más frecuente — cambian con contrataciones)
2. Sincronizar **Finalidades** (cambian raramente pero bloquean todo si falta una)
3. Verificar **Contratos** y **ContratoMarco** en el admin de Django

## Revisar el código de sincronización

Los endpoints de sincronización están en [zeus_mirror/views.py](zeus_mirror/views.py). Cada función:
1. Hace GET a la API ZEUS
2. Itera sobre los resultados
3. Usa `update_or_create` o `get_or_create` para actualizar la BD local

## Verificar token de API

Si la sincronización falla, el token de ZEUS puede haber expirado:
- Modelo: `home.TokenApiZeus` (vigencia = 1 día)
- Si expiró: se renueva automáticamente en la próxima llamada a `peticiones_http.obtener_token()`
- Revisar en [home/modules/peticiones_http.py](home/modules/peticiones_http.py) función `obtener_token`

## Configuración de ContratoMarco

Después de sincronizar Contratos, verifica que `ContratoMarco` esté configurado correctamente:
- Accede al admin de Django: `/admin/home/contratomarco/`
- Cada ContratoMarco debe tener mapeado `contrato_subsidiado` y `contrato_contributivo`
- Esto es crítico para la creación de admisiones
