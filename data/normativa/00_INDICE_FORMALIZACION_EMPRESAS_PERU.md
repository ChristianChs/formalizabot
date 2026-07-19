# Base oficial para RAG: formalizacion de empresas en Peru

Fecha de corte de esta base: 2026-07-17.

Alcance:
- Esta base se construyo solo con fuentes de primera mano del Estado peruano.
- Cubre la ruta general de formalizacion para empresa, con enfasis en persona juridica.
- Incluye el componente municipal de Tacna porque el proyecto esta orientado a MYPE en Tacna.
- El bloque de autorizaciones sectoriales se deja parametrizado por giro, porque la autoridad competente cambia segun la actividad economica.

## Ruta oficial resumida

Segun PRODUCE y MTPE, la formalizacion general de una empresa se organiza asi:

1. Constitucion y registro de la empresa.
2. Registro tributario.
3. Autorizacion municipal.
4. Autorizacion sectorial, si el giro la exige.
5. Registro laboral.

Fuentes:
- PRODUCE, "Registrar o constituir una empresa": https://www.gob.pe/269-registro-o-constitucion-de-empresa
- PRODUCE, "Constituir una empresa: guia paso a paso para emprendedores": https://www.gob.pe/80682-constituir-una-empresa-guia-paso-a-paso-para-emprendedores
- MTPE, "Guia de la Formalizacion": https://www.gob.pe/institucion/mtpe/informes-publicaciones/235224-guia-de-la-formalizacion
- PDF oficial MTPE: https://cdn.www.gob.pe/uploads/document/file/262973/Gui%CC%81a_de_la_formalizacio%CC%81n_21-11.pdf?v=1545251821

## Estructura de esta base documental

- `01_TIPO_DE_EMPRESA_Y_CONSTITUCION.md`
  Cubre eleccion de forma empresarial, reserva de nombre, minuta, capital, escritura, inscripcion y SACS.
- `02_RUC_REGIMEN_TRIBUTARIO_Y_CPE.md`
  Cubre activacion de RUC, clave SOL, regimen tributario y comprobantes electronicos.
- `03_LICENCIA_DE_FUNCIONAMIENTO_E_ITSE.md`
  Cubre licencia municipal, ITSE y estandarizacion nacional.
- `04_REGISTRO_LABORAL_Y_REMYPE.md`
  Cubre planilla electronica, REMYPE y regimen laboral MYPE.
- `05_TACNA_LICENCIAS_Y_FORMATOS_OFICIALES.md`
  Cubre formularios y referencias oficiales de la Municipalidad Provincial de Tacna.

## PDFs oficiales identificados

### MTPE

- "Guia de la formalizacion 21-11"
  Landing: https://www.gob.pe/institucion/mtpe/informes-publicaciones/235224-guia-de-la-formalizacion
  PDF: https://cdn.www.gob.pe/uploads/document/file/262973/Gui%CC%81a_de_la_formalizacio%CC%81n_21-11.pdf?v=1545251821

- "Articulo REMYPE - Enero 2019"
  Landing: https://www.gob.pe/institucion/mtpe/informes-publicaciones/259272-regimen-laboral-especial-de-la-micro-y-pequena-empresa

### SUNARP

- Resolucion N.° 160-2023-SUNARP/SN
  Landing: https://www.gob.pe/institucion/sunarp/normas-legales/4686430-160-2023-sunarp-sn
  PDF: https://cdn.www.gob.pe/uploads/document/file/5199202/Resoluci%C3%B3n%20de%20la%20Superintendencia%20Nacional%20de%20los%20Registros%20P%C3%BAblicos%20N.%C2%B0%20160-2023-SUNARP/SN.pdf?v=1695908569

- Modelos oficiales de constitucion aprobados por SUNARP:
  - SAC con directorio: https://cdn.www.gob.pe/uploads/document/file/5199472/Modelo%20de%20constituci%C3%B3n%20de%20Sociedad%20An%C3%B3nima%20Cerrada%20%28S.A.C.%29%20con%20directorio.pdf?v=1695909237
  - SAC sin directorio: https://cdn.www.gob.pe/uploads/document/file/5199473/Modelo%20de%20constituci%C3%B3n%20de%20Sociedad%20An%C3%B3nima%20Cerrada%20%28S.A.C.%29%20sin%20directorio.pdf?v=1695909237
  - SRL: https://cdn.www.gob.pe/uploads/document/file/5199474/Modelo%20de%20constituci%C3%B3n%20para%20una%20Sociedad%20Comercial%20de%20Responsabilidad%20Limitada%20-%20S.R.L.pdf?v=1695909237
  - SA: https://cdn.www.gob.pe/uploads/document/file/5199475/Modelo%20de%20constituci%C3%B3n%20de%20Sociedad%20An%C3%B3nima%20%E2%80%93%20S.A.pdf?v=1695909237
  - EIRL: https://cdn.www.gob.pe/uploads/document/file/5199476/Modelo%20de%20constituci%C3%B3n%20para%20una%20Empresa%20Individual%20de%20Responsabilidad%20Limitada%20-%20E.I.R.L.pdf?v=1695909237

- Resolucion N.° 179-2024-SUNARP/SN
  Landing: https://www.gob.pe/institucion/sunarp/normas-legales/6211058-179-2024-sunarp-sn

- Directiva DI-004-2024-SUNARP-DTR sobre reserva de nombre por SID-SUNARP
  PDF: https://cdn.www.gob.pe/uploads/document/file/7262306/6211058-di-004-2024-sunarp-dtr-directiva-que-regula-la-presentacion-electronica-tramite-y-anotacion-de-la-reserva-de-preferencia-registral-de-nombre-denominacion-o-razon-social-mediante-el-sistema-de-intermediacion-digital-de-la-sunarp.pdf?v=1758755159

- Infografias oficiales de reserva de nombre:
  Landing: https://www.gob.pe/institucion/sunarp/informes-publicaciones/1952729-reserva-de-nombre

### PCM

- "Guia sobre Licencias de Funcionamiento"
  Landing: https://www.gob.pe/institucion/pcm/informes-publicaciones/3040700-guia-sobre-licencias-de-funcionamiento
  PDF: https://cdn.www.gob.pe/uploads/document/file/3165307/Gui%CC%81a%20sobre%20Licencias%20de%20Funcionamiento.pdf.pdf?v=1653945813

- Decreto Supremo N.° 200-2020-PCM y anexos de procedimientos estandarizados
  Landing: https://www.gob.pe/institucion/pcm/normas-legales/1430019-200-2020-pcm

### Municipalidad Provincial de Tacna

- Compendio de documentos de licencias de funcionamiento:
  https://www.gob.pe/institucion/munitacna/colecciones/20144-licencias-de-funcionamiento-documentos

- Compendio de legislacion de licencias de funcionamiento:
  https://www.gob.pe/institucion/munitacna/colecciones/19786-licencias-de-funcionamiento-legislacion

## Criterio de uso para el RAG

- Priorizar estos markdown como capa de recuperacion semantica porque ya consolidan reglas, pasos y enlaces oficiales.
- Mantener los PDFs oficiales como respaldo documental para trazabilidad y citas largas.
- Para autorizaciones sectoriales, crear luego sub-bases por rubro:
  - alimentos y salud,
  - transporte,
  - industria,
  - turismo,
  - servicios financieros,
  - pesca y acuicultura,
  - hidrocarburos y energia.

