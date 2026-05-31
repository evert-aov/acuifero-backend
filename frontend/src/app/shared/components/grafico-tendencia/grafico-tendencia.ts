import {
  Component, Input, OnChanges, OnDestroy, AfterViewInit,
  ViewChild, ElementRef, Inject, PLATFORM_ID,
} from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { Chart, ChartConfiguration, registerables } from 'chart.js';
import { Reading } from '../../../core/models/municipio.model';

Chart.register(...registerables);

@Component({
  selector: 'app-grafico-tendencia',
  standalone: true,
  imports: [],
  templateUrl: './grafico-tendencia.html',
  styleUrl: './grafico-tendencia.css',
})
export class GraficoTendencia implements AfterViewInit, OnChanges, OnDestroy {
  /** Datos históricos reales — cuando se pasa, tiene prioridad en modo 'auto' */
  @Input() readings: Reading[] = [];

  /** Proyección 6 meses (% del pico histórico) */
  @Input() proyeccion: number[] = [];

  /** Precipitación mensual histórica (mm) */
  @Input() precipitacion: number[] = [];

  /**
   * Modo de renderizado:
   *   'auto'      → usa readings si existen, sino proyeccion
   *   'historico' → fuerza el gráfico de lecturas reales
   *   'proyeccion'→ fuerza el gráfico de proyección a 6 meses
   */
  @Input() mode: 'auto' | 'historico' | 'proyeccion' = 'auto';

  /** Umbral crítico en % del pico histórico (línea de referencia en modo proyección) */
  @Input() umbralCritico = 15;

  @ViewChild('chartCanvas', { static: false }) canvasRef!: ElementRef<HTMLCanvasElement>;

  private chart: Chart | null = null;
  private viewReady = false;

  constructor(@Inject(PLATFORM_ID) private readonly platformId: object) {}

  ngAfterViewInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      this.viewReady = true;
      setTimeout(() => this.rebuild(), 0);
    }
  }

  ngOnChanges(): void {
    if (this.viewReady) this.rebuild();
  }

  ngOnDestroy(): void {
    this.chart?.destroy();
  }

  private rebuild(): void {
    this.chart?.destroy();
    this.chart = null;
    if (!this.canvasRef?.nativeElement) return;
    const ctx = this.canvasRef.nativeElement.getContext('2d');
    if (!ctx) return;

    const useReadings =
      this.mode === 'historico'  ? true :
      this.mode === 'proyeccion' ? false :
      this.readings.length > 0;

    this.chart = new Chart(ctx, useReadings ? this.configHistorico() : this.configProyeccion());
  }

  // ── Gráfico con datos reales de la tabla readings ──────────────────────────
  private configHistorico(): ChartConfiguration {
    const labels = this.readings.map(r =>
      new Date(r.timestamp).toLocaleDateString('es-BO', { day: '2-digit', month: 'short' })
    );
    const nivel  = this.readings.map(r => r.nivel_freatico_m);
    const precip = this.readings.map(r => r.precipitacion_mm);

    return {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Nivel freático (m)',
            data: nivel,
            borderColor: '#84CC16',
            backgroundColor: 'rgba(132,204,22,0.08)',
            borderWidth: 2,
            tension: 0.3,
            fill: true,
            yAxisID: 'y',
            pointRadius: 0,
            pointHoverRadius: 4,
          },
          {
            label: 'Precipitación (mm)',
            data: precip,
            borderColor: '#38bdf8',
            backgroundColor: 'rgba(56,189,248,0.07)',
            borderWidth: 1.5,
            tension: 0.3,
            fill: true,
            yAxisID: 'y1',
            pointRadius: 0,
            pointHoverRadius: 4,
          },
        ],
      },
      options: this.baseOptions('Nivel freático (m)', '#84CC16', 'Precipitación (mm)', '#38bdf8'),
    };
  }

  // ── Gráfico de proyección 6 meses ─────────────────────────────────────────
  private configProyeccion(): ChartConfiguration {
    const labels = this.getMonthLabels(6);

    return {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Nivel freático (%)',
            data: this.proyeccion,
            borderColor: '#84CC16',
            backgroundColor: 'rgba(132,204,22,0.08)',
            borderWidth: 2,
            tension: 0.4,
            fill: true,
            yAxisID: 'y',
            pointBackgroundColor: '#84CC16',
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
            pointRadius: 4,
          },
          {
            label: `Umbral crítico (${this.umbralCritico}%)`,
            data: new Array(6).fill(this.umbralCritico),
            borderColor: '#dc2626',
            borderWidth: 1.5,
            borderDash: [5, 4],
            fill: false,
            yAxisID: 'y',
            pointRadius: 0,
            tension: 0,
          },
          {
            label: 'Precipitación mm/mes',
            data: this.precipitacion,
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245,158,11,0.06)',
            borderWidth: 2,
            tension: 0.4,
            fill: true,
            yAxisID: 'y1',
            pointBackgroundColor: '#f59e0b',
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
            pointRadius: 4,
          },
        ],
      },
      options: this.baseOptions('Nivel freático (%)', '#84CC16', 'Precipitación (mm)', '#f59e0b', 0, 100),
    };
  }

  /** Genera etiquetas de mes real para los próximos N meses */
  private getMonthLabels(count: number): string[] {
    const nombres = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
    const labels: string[] = [];
    const hoy = new Date();
    for (let i = 1; i <= count; i++) {
      const d = new Date(hoy.getFullYear(), hoy.getMonth() + i, 1);
      labels.push(`${nombres[d.getMonth()]} '${String(d.getFullYear()).slice(2)}`);
    }
    return labels;
  }

  private baseOptions(
    yLabel: string, yColor: string,
    y1Label: string, y1Color: string,
    yMin?: number, yMax?: number,
  ): ChartConfiguration['options'] {
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          labels: {
            color: '#737373',
            font: { family: 'Poppins', size: 11 },
            padding: 16,
            usePointStyle: true,
            pointStyleWidth: 8,
          },
        },
        tooltip: {
          backgroundColor: '#262626',
          titleColor: '#F9FAF7',
          bodyColor: '#E5E5E5',
          borderColor: '#404040',
          borderWidth: 1,
          padding: 10,
          cornerRadius: 8,
        },
      },
      scales: {
        x: {
          grid: { color: '#E5E5E5' },
          ticks: {
            color: '#737373',
            font: { family: 'Poppins', size: 10 },
            maxTicksLimit: 8,
            maxRotation: 0,
          },
          border: { color: '#E5E5E5' },
        },
        y: {
          type: 'linear',
          position: 'left',
          title: { display: true, text: yLabel, color: yColor, font: { size: 11, family: 'Poppins' } },
          grid: { color: '#E5E5E5' },
          ticks: { color: '#737373', font: { family: 'Poppins', size: 11 } },
          border: { color: '#E5E5E5' },
          ...(yMin !== undefined ? { min: yMin } : {}),
          ...(yMax !== undefined ? { max: yMax } : {}),
        },
        y1: {
          type: 'linear',
          position: 'right',
          title: { display: true, text: y1Label, color: y1Color, font: { size: 11, family: 'Poppins' } },
          grid: { drawOnChartArea: false },
          ticks: { color: '#737373', font: { family: 'Poppins', size: 11 } },
          border: { color: '#E5E5E5' },
        },
      },
    };
  }
}
