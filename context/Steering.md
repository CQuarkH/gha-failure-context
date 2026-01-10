# Contexto Técnico: Steering en Large Language Models

Definición General: El Steering (dirección o guiado) en LLMs es una técnica de control de comportamiento que modifica las activaciones internas del modelo durante la inferencia para influir en sus outputs sin reentrenamiento. Se basa en identificar y manipular "vectores de dirección" en el espacio de activaciones que corresponden a características o comportamientos específicos.

## Mecanismo de Funcionamiento:

- Vectores de Dirección (Steering Vectors): Se identifican vectores en el espacio latente del modelo que representan conceptos, estilos o comportamientos específicos (ej. "ser más formal", "evitar ciertos temas", "usar humor"). Estos vectores se obtienen típicamente mediante diferencias de activaciones entre pares de prompts contrastantes o mediante análisis de componentes principales.

- Intervención en Activaciones: Durante la inferencia, se añade (o resta) el steering vector a las activaciones de capas específicas del modelo, típicamente en las capas intermedias del transformer. Esto "empuja" la representación interna hacia la dirección deseada sin modificar los pesos del modelo.

- Magnitud de Steering: La intensidad del efecto se controla mediante un coeficiente de escala (steering strength) que multiplica el vector. Valores más altos producen efectos más pronunciados pero pueden degradar la coherencia.

## Flujo de Trabajo Típico:

- Fase 1 (Identificación): Se generan pares de ejemplos contrastantes que exhiben y no exhiben el comportamiento deseado. Se extraen las activaciones internas del modelo para ambos casos y se calcula la diferencia, obteniendo así el steering vector.

- Fase 2 (Validación): Se prueba el steering vector en un conjunto de validación para ajustar la magnitud óptima y las capas donde aplicarlo, buscando el balance entre efectividad y preservación de capacidades generales.

- Fase 3 (Aplicación): Durante la inferencia en producción, el steering vector se añade automáticamente a las activaciones en las capas seleccionadas, modificando el comportamiento del modelo de forma consistente sin necesidad de prompt engineering complejo.

## Ventajas

- Permite control fino y consistente sobre aspectos específicos del comportamiento del modelo (tono, estilo, safety, sesgo) sin necesidad de fine-tuning costoso o prompts largos y frágiles.

- Es modular y composable: múltiples steering vectors pueden aplicarse simultáneamente para controlar diferentes aspectos, y pueden activarse/desactivarse dinámicamente según el contexto.

- Preserva las capacidades generales del modelo base, ya que no modifica los pesos permanentemente, solo las activaciones durante la inferencia.

## Desventajas

- Requiere acceso a las activaciones internas del modelo, lo que generalmente solo es posible con modelos open-source o mediante APIs especiales. No funciona con APIs estándar de proveedores comerciales (OpenAI, Anthropic) que solo exponen entradas/salidas.

- La efectividad depende críticamente de la calidad de los datos contrastantes usados para extraer los steering vectors. Vectores mal identificados pueden producir comportamientos impredecibles o degradación de la calidad.

- Puede haber interferencia entre múltiples steering vectors aplicados simultáneamente, y el efecto puede variar según el dominio o tipo de tarea (lo que funciona bien en generación de texto creativo puede no funcionar igual en tareas de razonamiento lógico).

- Los steering vectors pueden no generalizar bien entre diferentes versiones del mismo modelo o entre arquitecturas distintas, requiriendo re-extracción cuando el modelo se actualiza.
