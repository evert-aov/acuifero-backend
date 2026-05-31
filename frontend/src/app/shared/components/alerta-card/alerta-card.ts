import { Component, Input } from '@angular/core';
import { LucideAngularModule, LucideIconData, Sun, Gauge, CircleAlert, Bell } from 'lucide-angular';
import { Alerta } from '../../../core/models/municipio.model';

@Component({
  selector: 'app-alerta-card',
  standalone: true,
  imports: [LucideAngularModule],
  templateUrl: './alerta-card.html',
  styleUrl: './alerta-card.css',
})
export class AlertaCard {
  @Input() alerta!: Alerta;

  private readonly iconMap: Record<string, LucideIconData> = {
    sequia: Sun,
    sobreextraccion: Gauge,
    contaminacion: CircleAlert,
  };

  get isCritica(): boolean {
    return this.alerta?.severidad === 'critical';
  }

  get tipoIcono(): LucideIconData {
    return this.iconMap[this.alerta?.tipo] ?? Bell;
  }
}
