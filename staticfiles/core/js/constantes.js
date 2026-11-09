// core/static/core/js/1_constantes.js

let instanciaGrafico = null;
let chartAvanzadoInstancia = null;
let datosAnalytics = [];

const MESES_CORTOS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sept', 'oct', 'nov', 'dic'];

const ORDEN_SLA = [
    'Respuesta enviada antes de la fecha límite',
    'Sin retraso',
    'De 1 a 3 días de retraso',
    'De 4 a 7 días de retraso',
    'De 7 a 10 días de retraso',
    'Más de 10 días de retraso'
];