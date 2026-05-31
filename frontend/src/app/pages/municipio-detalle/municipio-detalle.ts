import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import {
  LucideAngularModule,
  ArrowLeft, TriangleAlert, TrendingDown, TrendingUp,
  Droplets, CloudRain, Gauge, Waves, ChartLine,
} from 'lucide-angular';
import { DatosLocalesService } from '../../core/services/datos-locales.service';
import { Municipio, Prediccion, Reading, MunicipioSensorAggregation } from '../../core/models/municipio.model';
import { GraficoTendencia } from '../../shared/components/grafico-tendencia/grafico-tendencia';
import { GeminiPanel } from '../../shared/components/gemini-panel/gemini-panel';
import { forkJoin, of, catchError } from 'rxjs';

@Component({
  selector: 'app-municipio-detalle',
  standalone: true,
  imports: [CommonModule, RouterModule, LucideAngularModule, GraficoTendencia, GeminiPanel],
  templateUrl: './municipio-detalle.html',
  styleUrl: './municipio-detalle.css',
})
export class MunicipioDetalle implements OnInit {
  readonly ArrowLeft     = ArrowLeft;
  readonly TriangleAlert = TriangleAlert;
  readonly TrendingDown  = TrendingDown;
  readonly TrendingUp    = TrendingUp;
  readonly Droplets      = Droplets;
  readonly CloudRain     = CloudRain;
  readonly Gauge         = Gauge;
  readonly Waves         = Waves;
  readonly ChartLine     = ChartLine;

  readonly municipio     = signal<Municipio | null>(null);
  readonly prediccion    = signal<Prediccion | null>(null);
  readonly readings      = signal<Reading[]>([]);
  readonly sensorScores  = signal<MunicipioSensorAggregation | null>(null);
  readonly loading       = signal(true);
  readonly notFound      = signal(false);

  /** Tab activo en la sección de gráficos */
  readonly activeTab     = signal<'historico' | 'prediccion'>('historico');

  /** Última lectura del sensor más crítico */
  readonly lastReading = computed(() => {
    const r = this.readings();
    return r.length > 0 ? r[r.length - 1] : null;
  });

  readonly chartReadings = computed(() => this.readings());

  /** Metadatos de visualización según la tendencia */
  readonly tendenciaInfo = computed(() => {
    const pred = this.prediccion();
    if (!pred) return null;
    const map: Record<string, TendenciaInfo> = {
      critica_inmediata:    { label: 'Crisis inmediata',       color: '#dc2626', bg: 'bg-red-50',    border: 'border-red-200',    textClass: 'text-red-600'    },
      descendente_severo:   { label: 'Descenso severo',        color: '#f59e0b', bg: 'bg-amber-50',  border: 'border-amber-200',  textClass: 'text-amber-600'  },
      descendente_leve:     { label: 'Descenso leve',          color: '#eab308', bg: 'bg-yellow-50', border: 'border-yellow-200', textClass: 'text-yellow-700' },
      estable_riesgo_medio: { label: 'Estable — riesgo medio', color: '#84CC16', bg: 'bg-lime-50',   border: 'border-lime-200',   textClass: 'text-lime-700'   },
      estable:              { label: 'Estable',                color: '#22c55e', bg: 'bg-green-50',  border: 'border-green-200',  textClass: 'text-green-700'  },
    };
    return map[pred.tendencia] ?? { label: pred.tendencia, color: '#737373', bg: 'bg-gray-50', border: 'border-gray-200', textClass: 'text-gray-600' };
  });

  constructor(
    private readonly route: ActivatedRoute,
    private readonly datos: DatosLocalesService,
  ) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));

    forkJoin({
      municipio:    this.datos.getMunicipio(id),
      prediccion:   this.datos.getPrediccion(id),
      readings:     this.datos.getReadings(id, 90),
      sensorScores: this.datos.getSensorScores(id).pipe(catchError(() => of(null))),
    }).subscribe({
      next: ({ municipio, prediccion, readings, sensorScores }) => {
        if (!municipio) {
          this.notFound.set(true);
        } else {
          this.municipio.set(municipio);
          this.prediccion.set(prediccion ?? null);
          this.readings.set(readings ?? []);
          this.sensorScores.set(sensorScores);
        }
        this.loading.set(false);
      },
      error: () => {
        this.notFound.set(true);
        this.loading.set(false);
      },
    });
  }

  getRiesgoClass(nivel: string): string {
    const map: Record<string, string> = {
      critico: 'badge-critico', alto: 'badge-alto',
      medio:   'badge-medio',   bajo: 'badge-bajo',
    };
    return map[nivel] || '';
  }

  getRiesgoColor(nivel: string): string {
    const map: Record<string, string> = {
      critico: '#dc2626', alto: '#f59e0b',
      medio:   '#eab308', bajo: '#84CC16',
    };
    return map[nivel] || '#737373';
  }

  getHumedadColor(pct: number): string {
    if (pct >= 90) return '#dc2626';
    if (pct >= 70) return '#f59e0b';
    return '#84CC16';
  }

  getSensorScoreColor(nivel: string): string {
    return this.getRiesgoColor(nivel);
  }

  formatTendencia(val: number): string {
    const abs = Math.abs(val);
    const dir = val < 0 ? '↓' : val > 0 ? '↑' : '→';
    return `${dir} ${(abs * 30).toFixed(2)} m/mes`;
  }
}

interface TendenciaInfo {
  label: string;
  color: string;
  bg: string;
  border: string;
  textClass: string;
}
