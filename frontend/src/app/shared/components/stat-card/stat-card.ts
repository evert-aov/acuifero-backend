import { Component, Input } from '@angular/core';
import { LucideAngularModule, LucideIconData } from 'lucide-angular';

@Component({
  selector: 'app-stat-card',
  standalone: true,
  imports: [LucideAngularModule],
  templateUrl: './stat-card.html',
  styleUrl: './stat-card.css',
})
export class StatCard {
  @Input() valor: string | number = '';
  @Input() etiqueta: string = '';
  @Input() color: string = '#262626';
  @Input() icono?: LucideIconData;
}
