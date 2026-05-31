import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import {
  LucideAngularModule,
  ArrowLeft, TriangleAlert, TrendingDown,
  Droplets, CloudRain, Gauge, Waves,
} from 'lucide-angular';
import { DatosLocalesService } from '../../core/services/datos-locales.service';
import { Municipio, Prediccion, Reading } from '../../core/models/municipio.model';
import { GraficoTendencia } from '../../shared/components/grafico-tendencia/grafico-tendencia';
import { GeminiPanel } from '../../shared/components/gemini-panel/gemini-panel';
import { forkJoin } from 'rxjs';

@Component({
  selector: 'app-municipio-detalle',
  standalone: true,
  imports: [CommonModule, RouterModule, LucideAngularModule, GraficoTendencia, GeminiPanel],
  templateUrl: './municipio-detalle.html',
  styleUrl: './municipio-detalle.css',
})
export class MunicipioDetalle implements OnInit {
  readonly ArrowLeft    = ArrowLeft;
  readonly TriangleAlert = TriangleAlert;
  readonly TrendingDown  = TrendingDown;
  readonly Droplets      = Droplets;
  readonly CloudRain     = CloudRain;
  readonly Gauge         = Gauge;
  readonly Waves         = Waves;

  readonly municipio  = signal<Municipio | null>(null);
  readonly prediccion = signal<Prediccion | null>(null);
  readonly readings   = signal<Reading[]>([]);
  readonly loading    = signal(true);
  readonly notFound   = signal(false);

  /** Última lectura del sensor */
  readonly lastReading = computed(() => {
    const r = this.readings();
    return r.length > 0 ? r[r.length - 1] : null;
  });

  /** Últimos 90 días para el gráfico histórico */
  readonly chartReadings = computed(() => this.readings());

  constructor(
    private readonly route: ActivatedRoute,
    private readonly datos: DatosLocalesService,
  ) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));

    forkJoin({
      municipio:  this.datos.getMunicipio(id),
      prediccion: this.datos.getPrediccion(id),
      readings:   this.datos.getReadings(id, 90),
    }).subscribe({
      next: ({ municipio, prediccion, readings }) => {
        if (!municipio) {
          this.notFound.set(true);
        } else {
          this.municipio.set(municipio);
          this.prediccion.set(prediccion ?? null);
          this.readings.set(readings ?? []);
        }
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Error cargando datos del municipio:', err);
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
}
