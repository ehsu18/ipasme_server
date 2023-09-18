# Sistema IPASME - Desarrollado por Estudiantes de 4to Año del PNF de Informática

Este sistema ha sido meticulosamente desarrollado por un equipo de estudiantes de cuarto año del Programa Nacional de Formación (PNF) en Informática, en el contexto de una colaboración con el Instituto de Previsión y Asistencia Social del Ministerio de Educación (IPASME). Nuestra principal misión consiste en proporcionar una solución altamente eficiente y profesional que permita afrontar los retos identificados en la documentación del proyecto con rigor y excelencia.

Nuestro enfoque se centra en la optimización de la gestión de la información, buscando elevar los estándares de facilidad y confiabilidad en dicho proceso. Aspiramos a brindar un nivel de control superior sobre los datos, asegurando su integridad y disponibilidad en todo momento. Además, tenemos como propósito primordial ofrecer un servicio de la más alta calidad a la sociedad beneficiaria, cumpliendo con los más altos estándares de profesionalismo y eficacia en la ejecución de nuestro proyecto.



## Instalación
## Requisitos Previos

- **Python**: Asegúrate de tener Python instalado. Puedes descargarlo desde [python.org](https://www.python.org/downloads/) y seguir las instrucciones de instalación.

- **MongoDB**: Instala MongoDB siguiendo las instrucciones en [mongodb.com](https://www.mongodb.com/try/download/shell).

- **Virtualenv**: Ejecuta `pip install virtualenv` en la terminal de tu computadora para que su instalación sea globalmente.

## Configuración

1. Descarga el repositorio que está en esta dirección: `https://github.com/ehsu18/ipasme_server.git`.

2. Descomprime el archivo descargado en el paso anterior.

3. Abre la terminal o PowerShell en la dirección de la carpeta que contiene el proyecto.

4. Crea un entorno virtual en la raíz del proyecto con el comando `virtualenv venv`.

5. Activa el entorno virtual en PowerShell o la terminal del proyecto con el comando `. .\venv\Scripts\Activate`.

6. Activa el Entorno de MongoDB abriendo una nueva consola o PowerShell y ejecutando el comando `mongod`.

7. Regresa a la consola anterior y, en el mismo entorno virtual, instala las dependencias del proyecto con el comando  `pip install -r requirements.txt`.  

## Ejecución

1. Ejecuta el servidor del sistema con el comando `python manage.py runserver`.

2. Abre tu navegador y ve a la dirección que aparece en la consola.

Para acceder al sistema, utiliza las siguientes credenciales:
- **Usuario**: test
- **Contraseña**: password


¡Listo! Ahora puedes disfrutar del sistema IPASME.