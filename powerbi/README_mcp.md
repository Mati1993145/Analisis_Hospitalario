# 🔌 Claude Desktop ↔ PostgreSQL vía MCP (análisis conversacional REM20)

> **Importante:** MCP no conecta Power BI con Claude. Son cosas distintas.
Power BI = dashboards visuales; para ese flujo, ver `README_powerbi.md`.
MCP (Model Context Protocol) = permite que Claude Desktop consulte la base PostgreSQL en lenguaje natural desde el chat, sin escribir SQL.
Son canales independientes y complementarios; este documento trata solo de MCP.

## Qué es

Claude Desktop se conecta a la base PostgreSQL `rem20_db` mediante un servidor MCP.
El usuario pregunta en lenguaje natural, por ejemplo: "¿cuál fue el índice ocupacional promedio del Servicio de Salud Metropolitano Central en 2023?".
Claude traduce la pregunta a SQL, consulta la base y responde con datos reales.
Así, el usuario puede analizar la información sin escribir SQL directamente.

## Requisito: Node.js

El servidor MCP de PostgreSQL se ejecuta con `npx`, incluido en Node.js.

1. Verifica que Node.js esté instalado:

```powershell
node --version
```

2. Verifica que `npx` esté disponible:

```powershell
npx --version
```

3. Si Node.js no está instalado, descarga la versión LTS desde:

```text
https://nodejs.org
```

## Localizar el archivo de configuración (Windows)

La configuración de Claude Desktop se guarda en:

```text
%APPDATA%\Claude\claude_desktop_config.json
```

1. Abre el Explorador de archivos.
2. Pega esta ruta en la barra de direcciones:

```text
%APPDATA%\Claude
```

3. También puedes abrirla con `Win + R`, pegando:

```text
%APPDATA%\Claude
```

4. Si el archivo `claude_desktop_config.json` no existe, créalo como archivo de texto plano con ese nombre exacto.
5. Verifica que no quede guardado como `claude_desktop_config.json.txt`, especialmente si Windows oculta las extensiones de archivo.

## Agregar el servidor MCP

Pega esta configuración completa en `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "postgresql-rem20": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://postgres:PASSWORD@localhost:5432/rem20_db"
      ]
    }
  }
}
```

1. Reemplaza `PASSWORD` por la contraseña real de PostgreSQL solo en el archivo local `claude_desktop_config.json`.
2. Nunca escribas la contraseña real en este repositorio ni en ningún archivo versionado.
3. Si ya existen otros servidores dentro de `mcpServers`, agrega solo la clave `"postgresql-rem20"` dentro del objeto `mcpServers` existente.
4. No reemplaces todo el archivo ni borres otros servidores.
5. Verifica que el JSON siga siendo válido, con comas entre claves cuando corresponda.

> Nota de seguridad: la contraseña queda en texto plano en `claude_desktop_config.json`; ese archivo es local, no está en el repositorio y no debe subirse a GitHub. En este README siempre se usa `PASSWORD` como placeholder.

## Reiniciar Claude Desktop

1. Cierra Claude Desktop por completo.
2. Revisa también el icono de la bandeja del sistema y ciérralo desde ahí si sigue activo.
3. Abre Claude Desktop nuevamente.
4. Al reconectar, debe aparecer el icono de herramientas o conector MCP en la interfaz del chat.
5. Esa señal indica que el servidor `postgresql-rem20` se cargó correctamente.

Si el icono no aparece:

1. Revisa que el JSON sea válido.
2. Confirma que Node.js esté instalado.
3. Verifica que la base PostgreSQL `rem20_db` esté corriendo.

## Ejemplos de consultas en lenguaje natural

1. "¿Cuál fue el índice ocupacional promedio nacional por año entre 2014 y 2026?"

Claude debería responder con una serie anual y una cifra promedio para cada año.

2. "Muéstrame los 10 establecimientos con mayor índice ocupacional en 2025."

Claude debería responder con un ranking de establecimientos, usando `establecimiento`, `codigo_establecimiento` e `indice_ocupacional`.

3. "¿Cómo cambió la letalidad nacional entre 2019 y 2021?"

Claude debería responder con una comparación anual de `letalidad`, útil para observar el efecto COVID.

4. "¿Qué Servicios de Salud tuvieron más egresos en 2024?"

Claude debería responder con un ranking por `glosa_sss`, ordenado por `numero_egresos`.

5. "¿Qué áreas funcionales tuvieron mayor promedio de días de estada?"

Claude debería responder con un ranking por `area_funcional`, usando `promedio_dias_estada`; es esperable que destaquen áreas psiquiátricas.

6. "Muéstrame la evolución mensual del índice ocupacional durante 2020 para ver la caída por la pandemia."

Claude debería responder con una serie temporal mensual usando `periodo`, `mes` e `indice_ocupacional`.

## Power BI y MCP son canales independientes

Power BI y MCP no se conectan entre sí.
Son dos formas complementarias de explotar la misma base PostgreSQL `rem20_db`.

Power BI sirve para dashboards visuales, exploración estructurada, reportes y monitoreo recurrente.
MCP sirve para análisis conversacional ad-hoc en lenguaje natural desde Claude Desktop.

Usa MCP para preguntas rápidas y exploratorias.
Usa Power BI para reportes consolidados, seguimiento periódico y visualizaciones reutilizables.
