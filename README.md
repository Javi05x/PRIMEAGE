# PRIMEAGE

## Descripción

**AGE-FIVE** es un proyecto de análisis del rendimiento de futbolistas profesionales en las 5 grandes ligas europeas (Premier League, LaLiga, Serie A, Bundesliga y Ligue 1), clasificándolos por rangos de edad:

- **18–27**: Jugadores jóvenes
- **28–37**: Jugadores en plenitud
- **38+**: Jugadores veteranos

El análisis abarca las temporadas **2023/24** y **2024/25**, usando datos estadísticos detallados de cada jugador.

## Autores

- **Jaime Ercilla Martin**
- **Javier Bolívar García-Izquierdo**

## Fuentes de datos

Los datos provienen de dos datasets de Kaggle en formato Excel:

- [Top 5 Leagues — Temporada 23/24](https://www.kaggle.com/datasets/orkunaktas/all-football-players-stats-in-top-5-leagues-2324)
- [Top 5 Leagues — Temporada 24/25](https://www.kaggle.com/datasets/orkunaktas/all-football-players-stats-in-top-5-leagues-2425)

## Estructura del proyecto

```
AGE-FIVE/
├── .env.example           # Plantilla de variables de entorno
├── .gitignore
├── README.md
├── docker-compose.yml     # Levanta MongoDB y Mongo Express con Docker
├── requirements.txt       # Dependencias Python
├── data/
│   └── README.md          # Instrucciones para colocar los Excel de Kaggle
└── bd_futbol/
    ├── config.py          # Configuración centralizada (URI, colección, rangos, rutas)
    └── descargar_dt.py    # Script principal de carga de datos a MongoDB
```

## Requisitos previos

- **Docker** y **Docker Compose** (para levantar MongoDB)
- **Python 3.10+**

## Instalación paso a paso

### 1. Clonar el repositorio

```bash
git clone https://github.com/Javi05x/AGE-FIVE.git
cd AGE-FIVE
```

### 2. Crear y activar un entorno virtual

```bash
python -m venv venv
# En Linux/macOS:
source venv/bin/activate
# En Windows:
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar las variables de entorno

```bash
cp .env.example .env
# Edita .env si necesitas cambiar las rutas o la URI de MongoDB
```

### 5. Descargar los datasets de Kaggle

Descarga los dos archivos Excel desde los enlaces indicados en la sección **Fuentes de datos** y colócalos en la carpeta `data/`:

- `data/top5-players-2324.xlsx`
- `data/top5-players-2425.xlsx`

Consulta `data/README.md` para más detalles.

### 6. Levantar MongoDB con Docker

```bash
docker-compose up -d
```

Esto arranca MongoDB en `localhost:27017` y Mongo Express en `http://localhost:8081`.

### 7. Cargar los datos en MongoDB

```bash
python bd_futbol/descargar_dt.py
```

El script carga ambas temporadas en la colección `Jugadores` de la base de datos `ProyectoFutbol`. Si ya existen datos de una temporada, preguntará si deseas sobreescribirlos.

## Fases del proyecto

| Fase | Descripción |
|------|-------------|
| **Fase 1** | Base del proyecto: configuración, carga de datos y estructura MongoDB |
| **Fase 2** | Análisis exploratorio de datos (EDA) con pandas y visualizaciones |
| **Fase 3** | Modelos de predicción y clustering con scikit-learn |
| **Fase 4** | Dashboard interactivo con Jupyter o similar |

## Tecnologías usadas

- **Python 3.10+** — lenguaje principal
- **MongoDB 7** — base de datos NoSQL (vía Docker)
- **Docker / Docker Compose** — gestión del entorno de base de datos
- **pandas** — manipulación y limpieza de datos
- **pymongo** — conexión y operaciones con MongoDB
- **openpyxl** — lectura de archivos Excel
- **python-dotenv** — gestión de variables de entorno
- **matplotlib / seaborn** — visualización de datos
- **numpy** — operaciones numéricas
- **scikit-learn** — modelos de machine learning (fases futuras)
- **Jupyter** — análisis interactivo (fases futuras)
