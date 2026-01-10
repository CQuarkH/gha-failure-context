# Contexto Técnico: Recursive Language Models (RLMs)

[RLM Paper](https://arxiv.org/pdf/2512.24601)

Definición General: Los Recursive Language Models (RLMs) son un marco de inferencia que permite a los LLMs procesar prompts de longitud arbitraria (infinitos) tratándolos como parte de un entorno externo en lugar de una entrada directa de tokens a la red neuronal.

## Mecanismo de Funcionamiento:

- Prompt como Variable: El texto de entrada (el prompt largo) no se pasa al contexto del modelo. En su lugar, se carga como una variable de cadena (string) dentro de un entorno de ejecución persistente (Python REPL).

- Interacción Programática: El modelo actúa como un agente que escribe código para interactuar con esta variable. Puede usar operaciones de string, expresiones regulares (regex) o lógica de segmentación para "mirar" (peek) partes específicas del texto sin cargarlo todo en su memoria de atención.

- Llamadas Recursivas: El entorno REPL permite al modelo ejecutar una función especial (ej. llm_query()) que invoca una nueva instancia del modelo (sub-llamada) sobre un fragmento específico de la variable context. Esto permite descomponer problemas complejos en sub-tareas recursivas.

## Flujo de Trabajo Típico:

- Fase 1 (Exploración): El modelo escribe código para inspeccionar la estructura del context (ej. leer las primeras líneas, buscar palabras clave, contar saltos de línea).

- Fase 2 (Descomposición): Basado en la exploración, el modelo divide el context en chunks relevantes y lanza sub-llamadas recursivas para procesar solo esos segmentos.

- Fase 3 (Agregación): El modelo recibe las respuestas de las sub-llamadas, las almacena en variables y sintetiza una respuesta final.

## Ventajas

- Desacopla la longitud del prompt de la ventana de contexto del modelo, mitigando el "context rot" (degradación por contexto largo) y permitiendo procesar entradas órdenes de magnitud mayores que la capacidad nativa del modelo mediante acceso selectivo y comprimido a la información.

- Lo anterior lo hace ideal para logs gigantes o para texto extenso (como la Biblia).

## Desventajas

- Depende completamente de la capacidad agéntica y de manejo de código que tenga el modelo utilizado, debido a que es el modelo el que elije la forma de interactuar con el input, y esto puede ir desde escribir su propio código, como también la capacidad de crear subagentes o llamarse recursivamente.

- Se ha visto que el System Prompt inicial que se le pasa al modelo también influye en cómo este se comporta a la hora de hacer RLM, y que el mismo prompt podría no funcionar correctamente en modelos distintos.
