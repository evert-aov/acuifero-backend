export interface Municipio {
  id: number;
  nombre: string;
  lat: number;
  lng: number;
  region: string;
  poblacion: number;
  nivel_riesgo: 'bajo' | 'medio' | 'alto' | 'critico';
  score_riesgo: number;
}

export interface Prediccion {
  tendencia: string;
  meses_criticos: number;
  proyeccion: number[];
  precipitacion_historica: number[];
}

export interface Alerta {
  id: number;
  municipio_id: number;
  municipio_nombre: string;
  tipo: string;
  descripcion: string;
  severidad: 'warning' | 'critical';
  created_at: string;
}

export interface Reading {
  timestamp: string;
  municipio_id: number;
  nivel_freatico_m: number;
  humedad_suelo_pct: number;
  extraccion_lps: number;
  precipitacion_mm: number;
}
