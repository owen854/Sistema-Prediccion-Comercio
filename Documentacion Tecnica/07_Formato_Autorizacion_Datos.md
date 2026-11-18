# Formato de autorización para el uso de datos de ventas

> **Borrador para revisión.** Antes de presentarlo a los comercios, debe revisarlo el director del proyecto y, si la Universidad de Pamplona lo exige, su oficina de protección de datos o jurídica. Requerimientos: RF-09, RNF-19 (Ley 1581 de 2012 y Decreto 1377 de 2013, compilado en el Decreto 1074 de 2015).

---

## AUTORIZACIÓN PARA EL USO DE INFORMACIÓN DE VENTAS CON FINES ACADÉMICOS

**Proyecto:** Sistema de Predicción de Demanda para el Comercio Minorista Fronterizo
**Institución:** Universidad de Pamplona — Facultad de Ingenierías y Arquitectura, programa de Ingeniería de Sistemas
**Investigadores:** Jesus David Leal Espinel, Juan Felipe Mantilla Claro y Andres Felipe Florez Mora

Yo, ________________________________, identificado(a) con ______ No. ______________, en calidad de ____________________ (propietario / representante legal / administrador autorizado) del establecimiento de comercio ________________________________, ubicado en el municipio de ____________________, **autorizo** de manera libre, previa, expresa e informada a los investigadores del proyecto para recolectar y tratar la información de ventas del establecimiento en los siguientes términos:

### 1. Información que se entrega

- Registros de ventas: fecha, código o nombre del producto, categoría, unidades vendidas y valor.
- De manera opcional: precio, promociones, inventario y punto de venta.
- Periodo: desde ____________ hasta ____________.

**No se entregarán datos personales de clientes** (nombres, documentos de identidad, teléfonos, correos, direcciones). Si un archivo los contiene por error, el sistema elimina esas columnas antes de guardar la información.

### 2. Finalidad

La información se usará **exclusivamente con fines académicos**: analizar patrones de consumo, entrenar y validar modelos de pronóstico de demanda y evaluar su efecto en la gestión de inventarios, como parte del trabajo de grado mencionado. No se usará con fines comerciales ni se venderá o cederá a terceros.

### 3. Tratamiento y seguridad

- El nombre del establecimiento y de sus puntos de venta se reemplaza por un **código seudónimo** antes de procesar los datos.
- La información se guarda en equipos del proyecto con acceso restringido a los investigadores y no se publica en repositorios públicos.
- Los resultados que se publiquen (monografía, artículos, presentaciones) mostrarán solo **cifras agregadas o anonimizadas** que no permitan identificar al establecimiento.
- La información se conservará hasta la finalización del proyecto y su sustentación, y luego se eliminará o anonimizará de forma irreversible, salvo que el comerciante autorice por escrito un plazo mayor.

### 4. Derechos del titular

Conozco que, de acuerdo con la Ley 1581 de 2012, puedo:

- Conocer, actualizar y rectificar la información entregada.
- Solicitar prueba de esta autorización.
- Ser informado sobre el uso que se ha dado a la información.
- **Revocar esta autorización** y solicitar la eliminación de la información en cualquier momento, sin que ello me genere perjuicio alguno.
- Presentar quejas ante la Superintendencia de Industria y Comercio.

Para ejercer estos derechos puedo escribir a: ______________________________ (correo de contacto del proyecto).

### 5. Carácter voluntario

La entrega de la información es voluntaria. No entregarla o revocar esta autorización no genera ninguna consecuencia para el establecimiento.

---

Firma: ______________________________

Nombre: ______________________________

Fecha: ____ / ____ / ________

Ciudad: ______________________________

---

## Uso dentro del sistema

1. El formato firmado se guarda fuera del repositorio (carpeta del proyecto con acceso restringido).
2. En la vista **Mis datos** o por la API (`POST /api/v1/comercios/{id}/autorizaciones`) se registra la autorización con su fecha, alcance y una referencia al documento firmado (por ejemplo, el nombre del archivo escaneado), **sin datos personales del firmante**.
3. El sistema rechaza cualquier carga de ventas de un comercio que no tenga una autorización registrada.
