import { Component, HostListener } from '@angular/core';
import { RouterModule } from '@angular/router';
import {
  LucideAngularModule,
  Droplets, ArrowRight, Radio, Brain, Bell,
  ChevronDown, TriangleAlert, MapPin, TrendingDown, Shield
} from 'lucide-angular';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [RouterModule, LucideAngularModule],
  templateUrl: './landing.html',
  styleUrl: './landing.css',
})
export class Landing {
  readonly Droplets = Droplets;
  readonly ArrowRight = ArrowRight;
  readonly Radio = Radio;
  readonly Brain = Brain;
  readonly Bell = Bell;
  readonly ChevronDown = ChevronDown;
  readonly TriangleAlert = TriangleAlert;
  readonly MapPin = MapPin;
  readonly TrendingDown = TrendingDown;
  readonly Shield = Shield;

  scrolled = false;

  readonly regiones = [
    { nombre: 'Chaco',           municipios: 3, riesgo: 'Crítico', color: '#991b1b', bgColor: '#fee2e2' },
    { nombre: 'Chiquitanía',     municipios: 4, riesgo: 'Alto',    color: '#92400e', bgColor: '#fef3c7' },
    { nombre: 'Norte Integrado', municipios: 3, riesgo: 'Medio',   color: '#78350f', bgColor: '#fefce8' },
    { nombre: 'Metropolitana',   municipios: 1, riesgo: 'Medio',   color: '#14532d', bgColor: '#f0fdf4' },
  ];

  @HostListener('window:scroll')
  onScroll(): void {
    this.scrolled = window.scrollY > 8;
  }
}
