# PRIMEAGE: Análisis Futbolístico por Rango de Edad

## Resumen

**PRIMEAGE** es una herramienta de análisis de datos diseñada para explorar y visualizar el rendimiento futbolístico en función del rango de edad de los jugadores profesionales. El proyecto permite analizar grandes volúmenes de datos y segmentar información relevante para descubrir tendencias, identificar picos de rendimiento y realizar comparativas por edad y temporada.

## Características principales

- **Análisis multitemporal y segmentado por edad** para las temporadas: 2021/22, 2022/23, 2023/24 y 2024/25.
- **Datos obtenidos exclusivamente de archivos CSV descargados de Kaggle**.
- **Almacenamiento y análisis en MongoDB**, facilitando consultas complejas y dinámicas.
- **Visualización de resultados** mediante gráficos y tablas generados con Python.
- **Scripts y notebooks reproducibles** para la carga, procesamiento y análisis de los datos.

## Estructura del sistema

1. **Obtención de datos**:  
   Descarga de los ficheros CSV de Kaggle con información detallada sobre jugadores, partidos y equipos para las temporadas seleccionadas.

2. **Carga y almacenamiento en MongoDB**:  
   Los archivos CSV se importan como colecciones en una base de datos MongoDB, donde se gestionan y relacionan los datos históricos y estadísticos de cada temporada.

3. **Preprocesamiento y enriquecimiento**:  
   Mediante scripts en Python, se realiza limpieza, estandarización de formatos, segmentación por rango de edad y cálculo de métricas agregadas (goles/minuto, asistencias, etc.).

4. **Análisis y visualización**:  
   Generación de informes, gráficos y consultas estadísticas desde la base de datos utilizando notebooks y scripts Python.

## Tecnologías utilizadas

- **Python** (pandas, pymongo, matplotlib, seaborn, jupyter)
- **MongoDB** como base de datos principal
- **Docker** para despliegue y facilitar la réplica del entorno
- **Git/GitHub** para versionado y desarrollo colaborativo

## Cómo usar PRIMEAGE

1. Descarga los archivos CSV relevantes desde Kaggle (consulta la carpeta `/data` o la documentación del proyecto).
2. Levanta una instancia de MongoDB (puedes usar Docker con la configuración incluida).
3. Ejecuta los scripts de carga para importar los CSV a la base de datos.
4. Utiliza los notebooks de análisis para procesar, explorar y visualizar los datos.
5. Personaliza las consultas y visualizaciones según los objetivos de tu análisis.

## Resultados obtenidos

- Segmentación y análisis detallado por rango de edad y temporada.
- Tendencias históricas en el uso y rendimiento de jugadores jóvenes y veteranos.
- Informes y gráficos listos para presentaciones a clubes, técnicos o analistas.

## Trabajo futuro

- Integrar nuevas ligas, competiciones y fuentes de datos con estructura similar (nuevos CSV de Kaggle).
- Implementar modelos de predicción para evolución de carrera o riesgo de lesión.
- Desarrollar una interfaz web para facilitar el acceso a las visualizaciones y consultas.

## Repositorio

[https://github.com/Javi05x/PRIMEAGE](https://github.com/Javi05x/PRIMEAGE)

---

Si tienes sugerencias o quieres contribuir, por favor abre un issue o una pull request.
