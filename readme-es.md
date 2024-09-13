
# Script de Arbitraje de Apuestas Deportivas en España

**[Read in English](README.md)**

## Resumen breve

Este es mi intento de desarrollar una herramienta en Python de arbitraje de las casas de apuestas en España. La herramienta, extrae y analiza las cuotas de apuestas de todas las casas con licencia (39 en total) para identificar oportunidades de arbitraje en apuestas ganador-perdedor para eventos con hasta 4 participantes que no se estén jugando en el momento de la apuesta. El desarrollo de esta herramienta se llevó acabo de forma intermitente desde noviembre de 2023 hasta mayo de 2024. A pesar de la ambición por finalizar el proyecto, la complejidad y los rápidos cambios en las casas de apuestas me llevaron a dejar el proyecto a medias tras lograr el arbitraje simultaneo de 12 casas de apuestas, cubriendo aproximadamente el 30% del mercado nacional.

La herramienta utiliza solicitudes asíncronicas para extraer eficientemente las cuotas, que luego son procesadas a través de "parsers" personalizados (el parseo es una técnica usada para interpretar la sintaxis de un texto o programa y extraer información relevante del mismo) y almacenados en una base de datos SQLite. Utilizando procesamiento de lenguaje natural y un algoritmo de emparejamiento, se normalizan los nombres de los eventos entre distintas casas de apuestas y se identifican las cuotas más rentables. Este script es modular y está compuesto por distintos componentes para la extracción de datos, gestión de bases de datos y análisis de arbitraje, lo que lo hace adaptable para usuarios que deseen personalizar o ampliar las capacidades del script.

Si tienes la intención de desarrollar una herramienta similar sin tener un perfil en ingeniería / programación, te animo enérgicamente a reconsiderarlo. Este proyecto conlleva muchos desafíos y la probabilidad de éxito sin experiencia extensa puede ser baja. Considero que este proyecto podría encajar mejor a un equipo en lugar de a una sola persona.

**Uso y colaboración**: Mi principal objetivo con este proyecto es ayudar a otros a desarrollar sus propias herramientas y proyectos. Siéntete libre de copiar, adaptar y utilizar cualquier parte de este script como desees. Espero que al compartir mi trabajo abiertamente, se fomente el aprendizaje y la innovación. Animo a cualquiera a utilizar estos recursos para mejorar sus capacidades en sus respectivos campos.

## Índice
1. [Advertencia Legal](#advertencia-legal)
2. [Cómo usarlo](#cómo-usarlo)
3. [Qué es (probablemente) más reutilizable.](#qué-es-probablemente-más-útil)
4. [Cómo funciona](#cómo-funciona)
5. [Estructura de las carpetas](#estructura-carpetas)
6. [Solución de Problemas](#solución-de-problemas)
7. [Progreso y precisión de cada casa de apuestas](#progreso-y-precisión-de-cada-casa-de-apuestas)
8. [Información de Contacto](#información-de-contacto)
9. [Por Qué Empecé Este Proyecto (podría ser relevante si estás considerando contratarme)](#por-qué-empece)
10. [Por Qué Dejé El Proyecto Incompleto (psrsecc)](#por-qué-dejé-el-proyecto)

## Advertencia Legal
### Cumplimiento de `robots.txt`
Este script puede no adherirse al archivo `robots.txt` de cada casa de apuestas, el cual está destinado a regular el acceso automatizado a sus datos. Los usuarios son responsables de verificar y respetar las directivas `robots.txt` de cada sitio web que tengan la intención de procesar sus datos. Algunos componentes del script se han desarrollado a nivel teórico (no se han ejecutado nunca) para respetar las directrices de `robots.txt`; sin embargo, seguramente puedan seguir funcionando eficazmente a pesar de esta limitacion.

### Uso ético y legal
La funcionalidad proporcionada por este script debe usarse de manera ética y dentro de los límites de la ley. Antes de utilizar o ejecutar este script, los usuarios deben asegurarse de que sus actividades sean compatibles con todas las leyes y acuerdos de términos de servicio aplicables.

### Disclaimer
Esta herramienta se proporciona tal cual, sin ninguna garantía o promesa. El creador de este script no es responsable de ninguna acción tomada por sus usuarios, incluyendo cualquier consecuencia legal o daño potencial derivado de su uso. Los usuarios deben consultar con asesores legales para entender los posibles riesgos y legalidades del uso de tecnologías de scraping web en su región.

El uso de este script implica la aceptación de estos términos y la comprensión de que, como usuario, eres el único responsable de cualquier implicación legal de tus acciones.

## Cómo usarlo
Simplemente asegúrate de descargar todas las bibliotecas importadas en `scrape_v7` o cualquier otro script que desees usar, y ejecútalo. Para mayor conveniencia, puedes consultar el archivo `requirements.txt`, que contiene una lista de todas las bibliotecas usadas. 

**Importante:** El archivo `requirements.txt` puede incluir bibliotecas adicionales que no son estrictamente necesarias para este proyecto específico, ya que incluye dependencias de otros proyectos en los que estoy trabajando actualmente. Aunque lamento cualquier posible inconveniente que esto pueda causar, recomiendo la instalación de todos los paquetes listados para evitar errores en la ejecución.

## Qué es (probablemente) más reutilizable. Cópialo. 

### Herramientas de Análisis de Datos
Básicamente la parte más reutilizable. Estas son las únicas herramientas que no creo que necesiten muchas actualizaciones, ya que las casas de apuestas rara vez cambian la estructura de sus HTMLs, aunque sí cambian de vez en cuando la forma en que interactúas con la página (lo que hace que obtener los HTMLs sea mucho más costoso). Puedes encontrarlas etiquetadas como `"parser"` en la carpeta de cada casa de apuestas.

### Detección de Arbitraje
Los scripts involucrados en identificar oportunidades de arbitraje son `maxodds.py` y `arbitrage.py`. No solo muestran cómo procesar y analizar las cuotas desde la base de datos, sino que también realizan todos los cálculos sobre cuánto apostar para maximizar el retorno. Son EXTREMADAMENTE reutilizables para alguien que esté empezando este proyecto, ya que la mayoría de los eventos / equipos / jugadores están nombrados de manera diferente para evitar comparar cuotas de manera automatizada. Mi enfoque puede NO ser perfecto, y tener un gran margen de mejoría, pero es una muy buena manera de empezar que habilita la posibilidad de probar otras funcionalidades que son más escalables.

###
Para un mayor entendimiento de como estos componentes se interrelacionan para otorgar un resultado cómodo de analizar, se pueden referir a [Cómo Funciona](#cómo-funciona)

## Cómo Funciona

Esta sección sirve como guía rápida para explorar las carpetas del proyecto y sus funcionalidades. He desarrollado todo de manera modular, lo que permite inspeccionar cada componente, ya sea dentro de las carpetas individuales de las casas de apuestas o en el script `scrape_v7` de manera individualizada.

### Prácticas Comunes
El proceso completo realizado simultáneamente en cada casa de apuestas incluye:
1. **Obtención de Datos:**: Utilización de `requests` para descargar contenido HTML de las páginas web de las casas de apuestas, a través de diferentes enfoques adaptados a la estructura de cada página.
2. **Análisis de Datos**: Extracción y procesamiento de los datos de los HTMLs usando scripts de análisis personalizados adaptados a la estructura de cada página de apuestas. A continuación se genera un archivo `.txt` con el nombre de la carpeta de cada casa de apuestas.
- Con tal de facilitar los siguientes pasos, los nombres de los participantes en cada evento son normalizados para facilitar asociar aquellos eventos que son los mismos pero que son nombrados de distinta manera a través de las distintas casas de apuestas.
3. **Almacenamiento de Datos**: Almacenado y gestión de los datos analizados en una base de datos SQLite usando `SQL.py` y `odds.py` para una recuperación y análisis eficientes de los archivos `.txt` previamente creados.

### Detección de Arbitraje

La base principal radica en leer la base de datos centralizada para identificar las mejores cuotas para cada evento. Para ello, he logrado implementar un algoritmo preexistente que utiliza técnicas de simulación de lenguaje natural (NLTK) para intentar vincular los mismos eventos nombrados de manera ligeramente diferente por cada casa de apuestas. Esto se puede analizar y optimizar en **`maxodds.py`**, aunque la configuración ya ha sido exhaustivamente probada y considero que es la más óptima. El principal resultado de este proceso es `maxodds.txt`, el cual contiene las mejores cuotas de cada evento, junto a un enlace a cada cuota en su respectiva casa de apuestas.

Finalmente, **`arbitrage.py`** extiende la funcionalidad de `maxodds.py` añadiendo la capacidad de filtrar y mostrar únicamente aquellos eventos donde existan oportunidades de arbitraje. Calcula las apuestas para cada cuota para garantizar un beneficio sin importar el resultado. El producto final de este proceso es `arbitrageable.txt`, el cual es una versión reducida de `maxodds.txt` que contiene únicamente aquellos eventos que se pueden arbitrar. 

## Estructura de las Carpetas

El proyecto está organizado en varios directorios y archivos, cada uno con una función específica en el flujo de trabajo del script.

### Directorio Raíz
- `README.md`: Proporciona una descripción general del proyecto, incluyendo instalación, uso y advertencia legal.
- `requirements.txt`: Lista todas las bibliotecas de Python necesarias para ejecutar los scripts, lo que simplifica el proceso de configuración con un solo comando.

### Carpetas de Casas de Apuestas
Cada casa de apuestas analizada por el script tiene su propia carpeta con el nombre de la casa de apuestas. Estas carpetas contienen:
- **Scripts de obtención de datos**: Adaptados a cada casa de apuestas, manejan las peculiaridades específicas de la obtención de datos de los sitios web.
- **Scripts de solicitudes**:  Estos gestionan las solicitudes enviadas a los servidores web de las casas de apuestas. Manejan tareas como gestionar sesiones HTTP, reintentar solicitudes fallidas y cumplir con los límites de peticiones, asegurando que las actividades de obtención de datos sean eficientes.
- **Scripts de análisis**: Extraen y formatean los datos de los scripts de obtención de datos en un formato estructurado y analizable.
- **Archivos de datos (`.txt`)**: Resultados de los scripts de obtención de datos, almacenando los datos procesados listos para su análisis.

### Scripts centrales
- `scrape_v7.py`: El script principal que orquesta el proceso de obtención de datos en TODAS las casas de apuestas simultáneamente y que tiene como producto final el archivo `.txt` con las oportunidades de arbitraje. 
- `maxodds.py`: Analiza los datos para identificar las mejores cuotas de apuestas entre las casas de apuestas.
- `arbitrage.py`: Identifica y calcula oportunidades de arbitraje, mostrando apuestas potenciales en  `arbitrageable.txt`.

### Archivos de Base de Datos
- `SQL.py`: Gestiona todas las interacciones con la base de datos SQLite, configurando el esquema de la base de datos.
- `odds.py`: Maneja la inserción y consulta de datos en la base de datos, facilitando la gestión eficiente de datos.

### Archivos de Salida
- `maxodds.txt`: Contiene los resultados de `maxodds.py`, listando las mejores cuotas encontradas para cada evento.
- `arbitrageable.txt`: Generado por `arbitrage.py`, lista todos los eventos donde se han encontrado oportunidades de arbitraje junto con las apuestas sugeridas.

## Solución de Problemas

Bueno, al ejecutar `scrape_v7` un monton de cosas pueden salir mal. He intentado minimizar el número de errores, pero SIEMPRE al ejecutar el programa hay errores relacionados con la parte asincrónica, los cuales no tengo ni la más mínima idea de cómo solucionar. Cabe destacar que esto no paraliza la ejecución del archivo, y únicamente implica perder entre 50-200 eventos de los más de 20.000 analizados en ese momento. Si aún así, decides intentar solucionarlos, ¡buena suerte!

Por otro lado, una lista más completa podría ser:

- **Problemas de conectividad con la base de datos**: Asegúrate de que la ruta de la base de datos SQLite en `SQL.py` y `odds.py` sea correcta. Verifica que el archivo de la base de datos sea accesible y que no esté siendo utilizado por otro proceso.

- **Errores de análisis (parsing)**: Si el análisis falla debido a actualizaciones en la estructura HTML de una casa de apuestas, actualiza los scripts de análisis correspondientes en la carpeta de dicha casa de apuestas con los elementos HTML correctos. Te puede llevar desde un par de horas hasta días dependiendo de la complejidad de la estructura HTML.

- **Datos faltantes en los archivos de salida:**: Asegúrate de que todos los scripts se completaron correctamente sin errores. Revisa los errores en la consola y verifica la integridad de la base de datos y los archivos de salida.

## Progreso y Precisión por Casa de Apuestas

La siguiente tabla detalla el progreso y la precisión de la obtención de datos para cada casa de apuestas de este proyecto. La puntuación (1-10) representa el porcentaje de eventos ofrecidos que fueron cubiertos con éxito por esta herramienta.

| Casa de Apuestas | Progreso (1-10) | Última Fecha de Obtención de Datos | Comentarios |
|------------------|-----------------|------------------------|-------------------------|
| Betfair          | 9               | 28/08/2024             |  |
| Interwetten      | 9               | Error 403 repentino; 21/05/2024 | Hasta la última obtención de datos, se cubrieron más del 95% de los eventos. |
| Marca            | 9               | 28/08/2024             |  |
| MarathonBet      | 9               | Error repentino; 26/05/2024 |  |
| PokerStars       | 9               | 28/08/2024             |  |
| Zebet            | 10              | 28/08/2024             | Contiene el mejor "scraper" hasta ahora. |
| Bet777           | 8.5             | 28/08/2024             |  |
| TonyBet          | 3               | 28/08/2024             | Funcional al principio, pero surgieron problemas más tarde (estropeé el `requester`); cubre solo alrededor del 25% de los eventos. Se necesita más desarrollo, pero espero que mi trabajo sea útil para alguien. |
| Dafabet          | 7               | 28/08/2024             | Todavía en desarrollo, falta mejorar la obtención de datos. |
| 1xBet            | 6.5             | Error repentino; MAYO 2024 | Problemas previos; las cuotas ganador-perdedor se mezclaron con otros tipos de apuestas para UFC, boxeo, en vivo y tenis de mesa. |
| Winamax          | 6               | Error 403 repentino; 25/11/2023 | No funciona en `scrape_v7`. Activo en `scrape_v1`. Se cubrieron muchos eventos; revisar el `parser`. No se continuó el desarrollo debido a limitaciones del `requester` relacionadas con el error 403. |
| Bwin             | 8               | 28/08/2024             | Errores de obtención de datos (`parser`); selecciona apuestas "set" en lugar de apuestas ganador-perdedor. No lo incluiría al ejecutar el `scrape_v7` completo, ya que genera numerosos falsos positivos en `arbitrageable.txt`. |

**Nota:**  Recuerda que esta herramienta solo obtiene datos de **apuestas de ganador-perdedor**. Los siguientes eventos están **EXCLUIDOS**:

- **Deportes con más de 4 participantes**: Raramente podrás arbitrar todos los resultados posibles en un evento de 5-20 participantes sin asumir que algunos de ellos tienen pocas posibilidades de ganar. Terminas tomando riesgos mínimo. El arbitraje deportivo consiste en NO asumir riesgos.

- **Eventos en vivo**: Son más complejos de desarrollar; requieren la automatización de la cuenta en la casa de apuestas analizada, lo cual está fuera del alcance de este script.

## Información de contacto

Simplemente envía un correo electrónico a TarasKuzmych@proton.me con el asunto "Bets Arbitrage" y tu mensaje. De lo contrario, no responderé.

## Por Qué Empecé Este Proyecto (podría ser relevante si estás considerando contratarme)

Este proyecto nació mientras completaba mi primer curso de programación con Python (previo a esto, no tenía experiencia en programación). Durante el desarrollo del curso, siempre mantuve una convicción clara: el verdadero valor de estos cursos no radica solo en adquirir nuevos conocimientos y herramientas, sino en aplicarlos para crear productos tangibles y útiles. Con esta idea en mente, y una vez finalizado el curso, comencé a buscar un proyecto paralelo que no solo me permitiera aprovechar mis nuevas habilidades, sino también generar un ingreso adicional al final de cada mes.

Explorando algunas ideas potenciales, un día, de camino a casa tras la clase, en el tren, recordé un concepto que había conocido unos meses antes: el arbitraje en apuestas deportivas. Había oído hablar de personas que obtenían beneficios utilizando herramientas diseñadas para aprovechar estas oportunidades de arbitraje. Incluso, en su momento, consideré pagar por uno de estos servicios, ya que parecían ofrecer una forma de obtener ganancias seguras, salvo el riesgo de ser bloqueado por las casas de apuestas (bendito problema). 

Así que en ese tren me pregunté por qué debería pagar por un servicio así cuando yo mismo podía crearlo. "Si ellos pudieron, ¿por qué yo no debería de poder" Y de esta manera tan ingenua empezó este proyecto, por la necesidad de construir algo rentable y por no tener ideas más originales. 

## Por Qué Dejé El Proyecto Incompleto (psrsecc)

Empecé este proyecto en noviembre de 2023 y trabajé en él de manera intermitente hasta mayo de 2024. En ese momento, tres casas de apuestas dejaron de funcionar repentinamente debido a cambios que implementaron. Para ese entonces, solo había logrado que 10 casas de apuestas funcionaran de manera simultánea, y ni siquiera óptimamente para fines de arbitraje. Considerando la creciente complejidad, la integración completa de las casas de apuestas restantes parecía una tarea abrumadora, probablemente me llevaría más de dos años finalizar el proyecto, siempre y cuando la dificultad de desarrollo fuera lineal, lo cual claramente no era el caso. Además de eso, habría requerido actualizaciones constantes de los subproyectos ya "terminados", lo cual parecía inviable para mí.

El proyecto presentó dos obstáculos técnicos principales:
- Primero, la dificultad técnica de eludir las protecciones web para solicitar y descargar HTMLs con éxito de las páginas de las casas de apuestas.
- En segundo lugar, la problematica de los eventos nombrados de manera ligeramente diferente en cada casa de apuestas. A pesar de intentar solucionarlo durante meses, este último problema persistió, resaltando quizás una tara en mis habilidades o una complejidad del proyecto más allá de mi inteligencia.

En algún momento, consideré vender las oportunidades de arbitraje que pudiera llegar a extraer. Sin embargo, este plan requería una cobertura más amplia en el número de casas de apuestas y una solución al problema de nombramiento de los eventos. Al darme cuenta de la limitación para generar ingresos a corto plazo, junto con el valor educativo menguante y los desafíos técnicos abrumadores, me vi obligado a reevaluar mis prioridades. A medida que mi "niño interior" dejó de jugar con este proyecto, el entusiasmo desapareció y comenzó a sentirse más como una obligación que como un pasatiempo. Tuve que adoptar un enfoque más pragmático, reconociendo que los rendimientos marginales eran mucho más bajos que otros caminos potenciales que podría explorar en los próximos meses.

Por lo tanto, creo que lo mejor es dejar este proyecto de lado y seguir adelante. Tuve la oportunidad de aprender lecciones valiosas y, aunque fracasé estrepitosamente, espero ayudar a alguien con el progreso que logré (¡y posiblemente diferenciarme en un proceso de selección!).

###
***Hasta el siguiente proyecto.***
