import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges, afterNextRender } from '@angular/core';
import { Municipio } from '../../../core/models/municipio.model';

@Component({
  selector: 'app-mapa-scz',
  standalone: true,
  imports: [],
  templateUrl: './mapa-scz.html',
  styleUrl: './mapa-scz.css',
})
export class MapaScz implements OnChanges {
  @Input() municipios: Municipio[] = [];
  @Output() municipioSeleccionado = new EventEmitter<Municipio>();

  private map: any = null;
  private L: any = null;
  private markersLayer: any = null;

  private readonly colorMap: Record<string, string> = {
    critico: '#dc2626',
    alto:    '#f59e0b',
    medio:   '#eab308',
    bajo:    '#84CC16',
  };

  constructor() {
    afterNextRender(async () => {
      await this.initMap();
      if (this.municipios.length) {
        this.renderMarkers();
      }
    });
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['municipios'] && this.map && this.L) {
      this.renderMarkers();
    }
  }

  private async initMap(): Promise<void> {
    const L = await import('leaflet');
    this.L = L;

    this.map = L.map('map-scz', {
      center: [-17.5, -62],
      zoom: 6,
      zoomControl: false,
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> © <a href="https://carto.com/">Carto</a>',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(this.map);

    L.control.zoom({ position: 'bottomleft' }).addTo(this.map);
    this.markersLayer = L.layerGroup().addTo(this.map);
  }

  private renderMarkers(): void {
    const L = this.L;
    this.markersLayer.clearLayers();

    this.municipios.forEach(m => {
      const color = this.colorMap[m.nivel_riesgo] ?? '#737373';
      const isCritico = m.nivel_riesgo === 'critico';

      const circle = L.circleMarker([m.lat, m.lng], {
        radius: 10 + m.score_riesgo * 8,
        fillColor: color,
        color: '#ffffff',
        weight: 2,
        opacity: 1,
        fillOpacity: isCritico ? 0.9 : 0.75,
      }).addTo(this.markersLayer);

      circle.bindTooltip(`
        <div style="font-family:Poppins,sans-serif;font-size:12px;padding:4px 2px;color:#262626">
          <strong>${m.nombre}</strong><br>
          <span style="color:${color};font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.04em">
            &#9679; ${m.nivel_riesgo}
          </span>
          &nbsp;&middot;&nbsp;${(m.score_riesgo * 100).toFixed(0)}/100
        </div>
      `, { sticky: true });

      circle.on('click', () => this.municipioSeleccionado.emit(m));
    });
  }
}
