# Plan de Expansión del Dataset Dorado - Sprint 1.2

## Resumen del Análisis

El análisis del dataset dorado actual muestra:
- **Total de preguntas**: 20
- **Categorías principales**: montos_limites (25%), procedimientos (25%)
- **Categorías subrepresentadas**: sanciones (5%), definiciones (5%)
- **Tipos de consulta principales**: procedural (35%), factual (30%)
- **Tipos de consulta subrepresentados**: reference (10%), consequence (5%), definition (5%)
- **Entidades más frecuentes**: viáticos (9 menciones), monto (3), plazo (3)

## Objetivos de Expansión

Para el Sprint 1.2, se propone expandir el dataset dorado de 20 a 50 preguntas, con los siguientes objetivos específicos:

1. **Equilibrar las categorías subrepresentadas**:
   - Aumentar preguntas de categoría "sanciones" de 1 a 5
   - Aumentar preguntas de categoría "definiciones" de 1 a 5
   - Mantener balance en las demás categorías

2. **Diversificar los tipos de consulta**:
   - Aumentar preguntas de tipo "reference" de 2 a 6
   - Aumentar preguntas de tipo "consequence" de 1 a 5
   - Aumentar preguntas de tipo "definition" de 1 a 5

3. **Ampliar la cobertura de entidades**:
   - Incluir más preguntas sobre entidades poco representadas como "servidores", "responsable", "aprobar"
   - Reducir la concentración en "viáticos" (actualmente 45% de las preguntas)

## Plan de Nuevas Preguntas (30 adicionales)

### Categoría: Sanciones (4 nuevas)

1. **Q021** - "¿Qué sanciones se aplican por no presentar la rendición de cuentas a tiempo?"
   - Tipo: consequence
   - Dificultad: medium
   - Entidades: sanciones, rendición, plazo

2. **Q022** - "¿Cuáles son las consecuencias de declarar gastos falsos en una comisión de servicios?"
   - Tipo: consequence
   - Dificultad: medium
   - Entidades: consecuencias, gastos falsos, comisión

3. **Q023** - "¿Qué norma establece las sanciones por mal uso de viáticos?"
   - Tipo: reference
   - Dificultad: medium
   - Entidades: norma, sanciones, viáticos

4. **Q024** - "¿Quién es responsable de aplicar sanciones por incumplimiento en rendiciones de viáticos?"
   - Tipo: responsibility
   - Dificultad: hard
   - Entidades: responsable, sanciones, rendición, viáticos

### Categoría: Definiciones (4 nuevas)

5. **Q025** - "¿Qué se considera como 'comisión de servicios' según la normativa del MINEDU?"
   - Tipo: definition
   - Dificultad: easy
   - Entidades: comisión de servicios, definición

6. **Q026** - "¿Cómo se define 'viático' en la normativa de viajes oficiales?"
   - Tipo: definition
   - Dificultad: easy
   - Entidades: viático, definición

7. **Q027** - "¿Qué se entiende por 'rendición de cuentas documentada' en el contexto de viáticos?"
   - Tipo: definition
   - Dificultad: medium
   - Entidades: rendición de cuentas documentada, definición

8. **Q028** - "¿Cuál es la definición de 'declaración jurada de gastos' según la normativa?"
   - Tipo: definition
   - Dificultad: medium
   - Entidades: declaración jurada, definición

### Categoría: Normativa (3 nuevas)

9. **Q029** - "¿Qué directiva interna del MINEDU regula el uso de viáticos?"
   - Tipo: reference
   - Dificultad: medium
   - Entidades: directiva, MINEDU, viáticos

10. **Q030** - "¿Qué norma establece los procedimientos para comisiones de servicio internacionales?"
    - Tipo: reference
    - Dificultad: hard
    - Entidades: norma, procedimientos, comisión, internacional

11. **Q031** - "¿Cuándo fue la última actualización de la normativa de viáticos del MINEDU?"
    - Tipo: factual
    - Dificultad: hard
    - Entidades: actualización, normativa, viáticos

### Categoría: Montos_Limites (4 nuevas)

12. **Q032** - "¿Cuál es el monto máximo para viáticos en comisiones a Asia?"
    - Tipo: factual
    - Dificultad: medium
    - Entidades: monto, viáticos, internacional, Asia

13. **Q033** - "¿Existe un monto mínimo para solicitar viáticos?"
    - Tipo: factual
    - Dificultad: easy
    - Entidades: monto, mínimo, viáticos

14. **Q034** - "¿Cuál es el límite de gastos de representación para funcionarios de alto nivel?"
    - Tipo: factual
    - Dificultad: hard
    - Entidades: límite, gastos, representación, funcionarios

15. **Q035** - "¿Qué porcentaje del viático corresponde si la comisión dura menos de 4 horas?"
    - Tipo: factual
    - Dificultad: medium
    - Entidades: porcentaje, viático, duración, comisión

### Categoría: Procedimientos (5 nuevas)

16. **Q036** - "¿Cómo se solicita una ampliación de plazo para rendición de viáticos?"
    - Tipo: procedural
    - Dificultad: medium
    - Entidades: ampliación, plazo, rendición, viáticos

17. **Q037** - "¿Cuál es el procedimiento para solicitar viáticos para un grupo de servidores?"
    - Tipo: procedural
    - Dificultad: hard
    - Entidades: procedimiento, viáticos, grupo, servidores

18. **Q038** - "¿Qué pasos se deben seguir para modificar el destino de una comisión ya aprobada?"
    - Tipo: procedural
    - Dificultad: hard
    - Entidades: pasos, modificar, destino, comisión

19. **Q039** - "¿Cómo se justifican gastos sin comprobante de pago?"
    - Tipo: procedural
    - Dificultad: medium
    - Entidades: justificar, gastos, comprobante

20. **Q040** - "¿Cuál es el procedimiento para devolver viáticos no utilizados?"
    - Tipo: procedural
    - Dificultad: medium
    - Entidades: procedimiento, devolver, viáticos

### Categoría: Plazos (5 nuevas)

21. **Q041** - "¿Con cuánta anticipación se debe solicitar viáticos para comisiones internacionales?"
    - Tipo: factual
    - Dificultad: medium
    - Entidades: anticipación, solicitar, viáticos, internacional

22. **Q042** - "¿Cuál es el plazo para aprobar o rechazar una solicitud de viáticos?"
    - Tipo: factual
    - Dificultad: medium
    - Entidades: plazo, aprobar, rechazar, solicitud, viáticos

23. **Q043** - "¿Cuánto tiempo se tiene para subsanar observaciones en la rendición de viáticos?"
    - Tipo: factual
    - Dificultad: medium
    - Entidades: tiempo, subsanar, observaciones, rendición

24. **Q044** - "¿Cuál es el plazo para solicitar reembolso por gastos adicionales justificados?"
    - Tipo: factual
    - Dificultad: hard
    - Entidades: plazo, reembolso, gastos adicionales

25. **Q045** - "¿En qué plazo debe notificarse la cancelación de una comisión de servicios?"
    - Tipo: factual
    - Dificultad: medium
    - Entidades: plazo, notificación, cancelación, comisión

### Categoría: Roles (5 nuevas)

26. **Q046** - "¿Quién puede autorizar comisiones de servicio al extranjero?"
    - Tipo: responsibility
    - Dificultad: hard
    - Entidades: autorizar, comisión, extranjero

27. **Q047** - "¿Qué área es responsable de verificar la documentación de rendición de viáticos?"
    - Tipo: responsibility
    - Dificultad: medium
    - Entidades: área, verificar, documentación, rendición

28. **Q048** - "¿Quién debe firmar la declaración jurada de gastos sin comprobante?"
    - Tipo: responsibility
    - Dificultad: easy
    - Entidades: firmar, declaración jurada, gastos

29. **Q049** - "¿Qué funcionario puede aprobar excepciones a los montos máximos de viáticos?"
    - Tipo: responsibility
    - Dificultad: hard
    - Entidades: funcionario, aprobar, excepciones, montos máximos

30. **Q050** - "¿Quién es responsable de capacitar al personal sobre la normativa de viáticos?"
    - Tipo: responsibility
    - Dificultad: medium
    - Entidades: responsable, capacitar, normativa, viáticos

## Distribución Final Proyectada

Después de la expansión, la distribución proyectada será:

### Por Categoría:
- montos_limites: 9 preguntas (18%)
- procedimientos: 10 preguntas (20%)
- plazos: 8 preguntas (16%)
- normativa: 5 preguntas (10%)
- roles: 8 preguntas (16%)
- sanciones: 5 preguntas (10%)
- definiciones: 5 preguntas (10%)

### Por Tipo de Consulta:
- factual: 14 preguntas (28%)
- procedural: 12 preguntas (24%)
- reference: 6 preguntas (12%)
- responsibility: 10 preguntas (20%)
- consequence: 5 preguntas (10%)
- definition: 5 preguntas (10%)

### Por Dificultad:
- easy: 5 preguntas (10%)
- medium: 28 preguntas (56%)
- hard: 17 preguntas (34%)

## Próximos Pasos

1. Validar este plan con expertos en normativas del MINEDU
2. Confirmar las respuestas ground truth para cada nueva pregunta
3. Implementar las preguntas en el formato JSON del dataset dorado
4. Actualizar el dataset y ejecutar pruebas de validación
5. Documentar la expansión del dataset en el informe del Sprint 1.2
