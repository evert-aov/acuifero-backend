import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import {
  LucideAngularModule,
  MapPin, CircleAlert, TriangleAlert, ChartBar, ArrowRight
} from 'lucide-angular';
import { DatosLocalesService } from '../../core/services/datos-locales.service';
import { Municipio, Alerta } from '../../core/models/municipio.model';
import { StatCard } from '../../shared/components/stat-card/stat-card';
import { AlertaCard } from '../../shared/components/alerta-card/alerta-card';
import { MapaScz } from '../../shared/components/mapa-scz/mapa-scz';
import { Navbar } from '../../shared/components/navbar/navbar';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, LucideAngularModule, StatCard, AlertaCard, MapaScz, Navbar],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard implements OnInit {
  readonly MapPin = MapPin;
  readonly CircleAlert = CircleAlert;
  readonly TriangleAlert = TriangleAlert;
  readonly ChartBar = ChartBar;
  readonly ArrowRight = ArrowRight;

  municipios: Municipio[] = [];
  alertas: Alerta[] = [];
  loading = true;

  constructor(private datos: DatosLocalesService, private router: Router) {}

  ngOnInit(): void {
    this.datos.getMunicipios().subscribe({
      next: (data) => { this.municipios = data; this.loading = false; },
      error: (err) => { console.error('Error fetching municipios:', err); this.loading = false; }
    });
    this.datos.getAlertas().subscribe({
      next: (data) => { this.alertas = data; },
      error: (err) => { console.error('Error fetching alertas:', err); }
    });
  }

  get criticosCount(): number {
    return this.municipios.filter(m => m.nivel_riesgo === 'critico').length;
  }

  get altosCount(): number {
    return this.municipios.filter(m => m.nivel_riesgo === 'alto').length;
  }

  get alertasCriticasCount(): number {
    return this.alertas.filter(a => a.severidad === 'critical').length;
  }

  get scorePromedio(): string {
    if (!this.municipios.length) return '—';
    const avg = this.municipios.reduce((sum, m) => sum + m.score_riesgo, 0) / this.municipios.length;
    return (avg * 100).toFixed(0) + '/100';
  }

  get municipiosPorRiesgo(): Array<Municipio & { alerta?: Alerta }> {
    const orden: Record<string, number> = { critico: 0, alto: 1, medio: 2, bajo: 3 };
    return [...this.municipios]
      .sort((a, b) => (orden[a.nivel_riesgo] ?? 4) - (orden[b.nivel_riesgo] ?? 4) || b.score_riesgo - a.score_riesgo)
      .map(m => ({ ...m, alerta: this.alertas.find(a => a.municipio_id === m.id) }));
  }

  irAMunicipio(municipio: Municipio): void {
    this.router.navigate(['/municipio', municipio.id]);
  }
}
