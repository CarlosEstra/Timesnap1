-- Script para verificar los cálculos de horas trabajadas por filtro
USE timesnapbd;

-- ===========================================
-- CÁLCULO DE HORAS PARA HOY (2025-12-05)
-- ===========================================

SELECT
    'HOY - 2025-12-05' as periodo,
    e.id_empleado,
    CONCAT(e.nombre, ' ', e.apellido1) as empleado,
    1 as dias_trabajados,
    -- Calcular horas trabajadas considerando comida
    ROUND(
        (
            TIMESTAMPDIFF(MINUTE,
                -- Hora entrada (o hora oficial si es más tarde)
                GREATEST(ra_entrada.hora, e.hora_entrada_puesto),
                -- Hora salida (o hora oficial si es más temprano)
                LEAST(ra_salida.hora, e.hora_salida_puesto)
            ) / 60.0
            -- Restar tiempo de comida si aplica
            - CASE
                WHEN ra_entrada.hora <= e.hora_comida_entrada
                     AND ra_salida.hora >= e.hora_comida_salida
                THEN TIMESTAMPDIFF(MINUTE, e.hora_comida_entrada, e.hora_comida_salida) / 60.0
                ELSE 0
            END
        ), 2
    ) as horas_calculadas
FROM empleados e
LEFT JOIN registros_asistencia ra_entrada ON ra_entrada.id_empleado = e.id_empleado
    AND ra_entrada.tipo = 'entrada' AND ra_entrada.fecha = '2025-12-05'
LEFT JOIN registros_asistencia ra_salida ON ra_salida.id_empleado = e.id_empleado
    AND ra_salida.tipo = 'salida' AND ra_salida.fecha = '2025-12-05'
WHERE ra_entrada.id_registro IS NOT NULL AND ra_salida.id_registro IS NOT NULL
ORDER BY e.id_empleado;

-- ===========================================
-- CÁLCULO DE HORAS PARA ESTA SEMANA (2025-12-01 al 2025-12-07)
-- ===========================================

SELECT
    'SEMANA - 2025-12-01 al 2025-12-07' as periodo,
    e.id_empleado,
    CONCAT(e.nombre, ' ', e.apellido1) as empleado,
    COUNT(DISTINCT ra_entrada.fecha) as dias_trabajados,
    ROUND(
        SUM(
            TIMESTAMPDIFF(MINUTE,
                GREATEST(ra_entrada.hora, e.hora_entrada_puesto),
                LEAST(ra_salida.hora, e.hora_salida_puesto)
            ) / 60.0
            - CASE
                WHEN ra_entrada.hora <= e.hora_comida_entrada
                     AND ra_salida.hora >= e.hora_comida_salida
                THEN TIMESTAMPDIFF(MINUTE, e.hora_comida_entrada, e.hora_comida_salida) / 60.0
                ELSE 0
            END
        ), 2
    ) as horas_calculadas
FROM empleados e
LEFT JOIN registros_asistencia ra_entrada ON ra_entrada.id_empleado = e.id_empleado
    AND ra_entrada.tipo = 'entrada' AND ra_entrada.fecha BETWEEN '2025-12-01' AND '2025-12-07'
LEFT JOIN registros_asistencia ra_salida ON ra_salida.id_empleado = e.id_empleado
    AND ra_salida.tipo = 'salida' AND ra_salida.fecha BETWEEN '2025-12-01' AND '2025-12-07'
WHERE ra_entrada.id_registro IS NOT NULL AND ra_salida.id_registro IS NOT NULL
GROUP BY e.id_empleado, e.nombre, e.apellido1
ORDER BY e.id_empleado;

-- ===========================================
-- CÁLCULO DE HORAS PARA QUINCENA PASADA (2025-11-16 al 2025-11-30)
-- ===========================================

SELECT
    'QUINCENA - 2025-11-16 al 2025-11-30' as periodo,
    e.id_empleado,
    CONCAT(e.nombre, ' ', e.apellido1) as empleado,
    COUNT(DISTINCT ra_entrada.fecha) as dias_trabajados,
    ROUND(
        SUM(
            TIMESTAMPDIFF(MINUTE,
                GREATEST(ra_entrada.hora, e.hora_entrada_puesto),
                LEAST(ra_salida.hora, e.hora_salida_puesto)
            ) / 60.0
            - CASE
                WHEN ra_entrada.hora <= e.hora_comida_entrada
                     AND ra_salida.hora >= e.hora_comida_salida
                THEN TIMESTAMPDIFF(MINUTE, e.hora_comida_entrada, e.hora_comida_salida) / 60.0
                ELSE 0
            END
        ), 2
    ) as horas_calculadas
FROM empleados e
LEFT JOIN registros_asistencia ra_entrada ON ra_entrada.id_empleado = e.id_empleado
    AND ra_entrada.tipo = 'entrada' AND ra_entrada.fecha BETWEEN '2025-11-16' AND '2025-11-30'
LEFT JOIN registros_asistencia ra_salida ON ra_salida.id_empleado = e.id_empleado
    AND ra_salida.tipo = 'salida' AND ra_salida.fecha BETWEEN '2025-11-16' AND '2025-11-30'
WHERE ra_entrada.id_registro IS NOT NULL AND ra_salida.id_registro IS NOT NULL
GROUP BY e.id_empleado, e.nombre, e.apellido1
ORDER BY e.id_empleado;

-- ===========================================
-- VERIFICACIÓN DETALLADA DE UN EMPLEADO (EJEMPLO: EMPLEADO 2)
-- ===========================================

SELECT
    'DETALLE EMPLEADO 2 - HOY' as periodo,
    ra.fecha,
    ra.tipo,
    ra.hora,
    e.hora_entrada_puesto,
    e.hora_salida_puesto,
    e.hora_comida_entrada,
    e.hora_comida_salida,
    -- Cálculo de horas para este día
    ROUND(
        TIMESTAMPDIFF(MINUTE,
            GREATEST(ra.hora, e.hora_entrada_puesto),
            LEAST(ra.hora, e.hora_salida_puesto)
        ) / 60.0, 2
    ) as horas_dia
FROM empleados e
JOIN registros_asistencia ra ON ra.id_empleado = e.id_empleado
WHERE e.id_empleado = '2'
    AND ra.fecha = '2025-12-05'
ORDER BY ra.fecha, ra.tipo;
