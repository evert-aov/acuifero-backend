import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Municipio, Prediccion, Alerta, Reading } from '../models/municipio.model';
import { Api } from './api';

@Injectable({ providedIn: 'root' })
export class DatosLocalesService {

  constructor(private readonly api: Api) {}

  getMunicipios(): Observable<Municipio[]> {
    return this.api.getMunicipios();
  }

  getMunicipio(id: number): Observable<Municipio | undefined> {
    return this.api.getMunicipio(id) as Observable<Municipio | undefined>;
  }

  getPrediccion(municipioId: number): Observable<Prediccion | undefined> {
    return this.api.getPrediccion(municipioId) as Observable<Prediccion | undefined>;
  }

  getAlertas(): Observable<Alerta[]> {
    return this.api.getAlertas();
  }

  getResumenGemini(municipioId: number): Observable<{ resumen: string }> {
    return this.api.getResumenGemini(municipioId);
  }

  getReadings(municipioId: number, days = 90): Observable<Reading[]> {
    return this.api.getReadings(municipioId, days);
  }

  getLastReading(municipioId: number): Observable<Reading> {
    return this.api.getLastReading(municipioId);
  }
}
